#!/usr/bin/env python3
"""
Generate Figure 2 and Figure 3-style benchmark plots for the dummy experiment.
"""

import argparse
import os
import platform
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import pandas as pd

TMP_CACHE_DIR = Path(tempfile.gettempdir()) / "parallel_rem_cache"
TMP_CACHE_DIR.mkdir(parents=True, exist_ok=True)
MATPLOTLIB_CACHE_DIR = TMP_CACHE_DIR / "matplotlib"
XDG_CACHE_DIR = TMP_CACHE_DIR / "xdg"
MATPLOTLIB_CACHE_DIR.mkdir(parents=True, exist_ok=True)
XDG_CACHE_DIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(MATPLOTLIB_CACHE_DIR))
os.environ.setdefault("XDG_CACHE_HOME", str(XDG_CACHE_DIR))

import matplotlib.pyplot as plt


def parse_args():
    parser = argparse.ArgumentParser(
        description="Benchmark Parallel-REM on a dataset and generate Figure 2/3-like plots."
    )
    parser.add_argument(
        "--abundance",
        default="example_data/dummy_abundance.csv",
        help="Path to abundance matrix CSV.",
    )
    parser.add_argument(
        "--meta",
        default="example_data/dummy_metadata.csv",
        help="Path to metadata CSV.",
    )
    parser.add_argument(
        "--pipeline",
        default="Parallel-REM.py",
        help="Path to the Parallel-REM pipeline script.",
    )
    parser.add_argument(
        "--backend",
        default="loky",
        choices=["loky", "multiprocessing", "threading"],
        help="joblib backend to request from Parallel-REM.",
    )
    parser.add_argument(
        "--outdir",
        default="benchmark_results",
        help="Directory where metrics and plots will be saved.",
    )
    parser.add_argument(
        "--cores",
        type=int,
        nargs="+",
        help="Core counts to benchmark. Defaults to powers of two plus the machine maximum.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Stream the underlying pipeline logs for each benchmark run.",
    )
    parser.add_argument(
        "--run-timeout-sec",
        type=float,
        default=90.0,
        help="Timeout per benchmark subprocess run in seconds.",
    )
    return parser.parse_args()


def default_core_counts(max_cores):
    cores = [1]
    candidate = 2

    while candidate < max_cores:
        cores.append(candidate)
        candidate *= 2

    if max_cores not in cores:
        cores.append(max_cores)

    return sorted(set(cores))


def normalize_core_counts(core_counts, max_cores):
    if core_counts is None:
        return default_core_counts(max_cores)

    cleaned = sorted(set(core for core in core_counts if 1 <= core <= max_cores))
    if not cleaned:
        raise ValueError("No valid core counts were supplied.")
    if cleaned[0] != 1:
        raise ValueError("The benchmark must include 1 core to compute speedup.")
    return cleaned


def load_dataset_summary(abundance_path, meta_path):
    abundance = pd.read_csv(abundance_path, index_col=0)
    metadata = pd.read_csv(meta_path, index_col=0)

    if "study_name" not in metadata.columns:
        raise ValueError("Metadata CSV must contain a 'study_name' column.")

    sample_count = abundance.shape[0]
    species_count = abundance.shape[1]
    study_count = metadata["study_name"].nunique()
    total_pairs = species_count ** 2

    return {
        "samples": sample_count,
        "species": species_count,
        "studies": study_count,
        "pairs": total_pairs,
    }


def backend_retry_order(preferred_backend):
    # On macOS + Python 3.13, loky cleanup can emit noisy teardown exceptions.
    # Prefer multiprocessing first to keep benchmark output clean and stable.
    if (
        preferred_backend == "loky"
        and platform.system() == "Darwin"
        and sys.version_info >= (3, 13)
    ):
        order = ["multiprocessing", "threading", "loky"]
    else:
        order = [preferred_backend, "multiprocessing", "threading"]

    deduped = []
    seen = set()
    for backend in order:
        if backend not in seen:
            deduped.append(backend)
            seen.add(backend)
    return deduped


def run_single_benchmark(
    pipeline_path,
    abundance_path,
    meta_path,
    cores,
    backend,
    verbose,
    timeout_sec,
):
    with tempfile.TemporaryDirectory(prefix=f"parallel_rem_{cores}c_") as run_dir:
        last_error = None
        for selected_backend in backend_retry_order(backend):
            command = [
                sys.executable,
                str(pipeline_path),
                "--abundance",
                str(abundance_path),
                "--meta",
                str(meta_path),
                "--cores",
                str(cores),
                "--backend",
                selected_backend,
                "--outdir",
                run_dir,
            ]

            start = time.perf_counter()
            try:
                if verbose:
                    completed = subprocess.run(command, check=False, timeout=timeout_sec)
                else:
                    completed = subprocess.run(
                        command,
                        check=False,
                        timeout=timeout_sec,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                    )
            except subprocess.TimeoutExpired:
                elapsed = time.perf_counter() - start
                last_error = RuntimeError(
                    f"Timed out after {elapsed:.2f} sec with backend '{selected_backend}'."
                )
                print(
                    f"[warn] {cores} core(s) timed out with backend '{selected_backend}' "
                    f"after {elapsed:.2f} sec."
                )
                continue

            elapsed = time.perf_counter() - start
            if completed.returncode == 0:
                return elapsed, selected_backend

            error_message = (
                f"Benchmark run failed for {cores} core(s) with backend "
                f"'{selected_backend}' (exit code {completed.returncode})."
            )
            if not verbose and completed.stdout:
                error_message = f"{error_message}\n{completed.stdout}"
            last_error = RuntimeError(error_message)
            print(
                f"[warn] {cores} core(s) failed with backend '{selected_backend}'. "
                "Trying fallback backend..."
            )

        if last_error is None:
            last_error = RuntimeError(f"No backend attempts were made for {cores} core(s).")
        raise last_error


def benchmark_pipeline(
    pipeline_path,
    abundance_path,
    meta_path,
    core_counts,
    total_pairs,
    backend,
    verbose,
    timeout_sec,
):
    rows = []

    for cores in core_counts:
        print(f"[benchmark] Running Parallel-REM with {cores} core(s)...")
        elapsed, used_backend = run_single_benchmark(
            pipeline_path=pipeline_path,
            abundance_path=abundance_path,
            meta_path=meta_path,
            cores=cores,
            backend=backend,
            verbose=verbose,
            timeout_sec=timeout_sec,
        )
        throughput = total_pairs / elapsed
        rows.append(
            {
                "cpu_cores": cores,
                "execution_time_sec": elapsed,
                "throughput_pairs_per_sec": throughput,
                "backend_used": used_backend,
            }
        )
        print(
            f"[benchmark] {cores:>2} core(s): "
            f"{elapsed:.2f} sec, {throughput:.2f} pairs/sec "
            f"(backend: {used_backend})"
        )

    metrics = pd.DataFrame(rows)
    baseline_time = metrics.loc[metrics["cpu_cores"] == 1, "execution_time_sec"].iloc[0]
    metrics["speedup_factor"] = baseline_time / metrics["execution_time_sec"]
    metrics["parallel_efficiency"] = metrics["speedup_factor"] / metrics["cpu_cores"]
    return metrics


def plot_strong_scaling(metrics, summary, output_path):
    plt.style.use("seaborn-v0_8-whitegrid")
    fig, ax = plt.subplots(figsize=(8.6, 5.2))

    ax.plot(
        metrics["cpu_cores"],
        metrics["cpu_cores"],
        linestyle="--",
        linewidth=1.5,
        color="#b8b8b8",
        label="Ideal Linear Speedup",
    )
    ax.plot(
        metrics["cpu_cores"],
        metrics["speedup_factor"],
        marker="o",
        linewidth=2.2,
        markersize=6,
        color="#2ca02c",
        label="Actual Speedup",
    )

    best_row = metrics.loc[metrics["speedup_factor"].idxmax()]
    x_offset = max(1.0, metrics["cpu_cores"].max() * 0.22)
    y_offset = max(1.0, metrics["speedup_factor"].max() * 0.18)
    text_x = max(0.9, best_row["cpu_cores"] - x_offset)
    ax.annotate(
        f"{best_row['speedup_factor']:.2f}x Speedup",
        xy=(best_row["cpu_cores"], best_row["speedup_factor"]),
        xytext=(text_x, best_row["speedup_factor"] + y_offset),
        arrowprops={"arrowstyle": "->", "color": "black", "lw": 1.1},
        fontsize=10,
    )

    axis_limit = max(metrics["cpu_cores"].max(), metrics["speedup_factor"].max()) * 1.15
    ax.set_xlim(0.5, metrics["cpu_cores"].max() * 1.05)
    ax.set_ylim(0, axis_limit)
    ax.set_xticks(metrics["cpu_cores"])
    ax.set_xlabel("Number of CPU Cores")
    ax.set_ylabel("Speedup Factor (vs 1 Core)")
    ax.set_title(
        "Strong Scaling Analysis: Parallel-REM Dummy Experiment\n"
        f"Dataset: {summary['samples']} Samples, {summary['species']} Species, {summary['studies']} Studies"
    )
    ax.legend(loc="upper left", frameon=True)

    fig.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)


def plot_parallel_efficiency(metrics, summary, output_path):
    plt.style.use("seaborn-v0_8-whitegrid")
    fig, ax = plt.subplots(figsize=(8.6, 5.2))

    ax.plot(
        metrics["cpu_cores"],
        metrics["parallel_efficiency"],
        marker="o",
        linewidth=2.0,
        markersize=6,
        color="#9b59b6",
    )
    ax.axhline(
        0.5,
        linestyle="--",
        linewidth=1.4,
        color="#9e9e9e",
        label="50% Efficiency Threshold",
    )

    ax.set_xlim(0.5, metrics["cpu_cores"].max() * 1.05)
    ax.set_ylim(0, 1.05)
    ax.set_xticks(metrics["cpu_cores"])
    ax.set_xlabel("Number of CPU Cores")
    ax.set_ylabel("Efficiency (Speedup / Cores)")
    ax.set_title(
        "Parallel Efficiency Drop-off\n"
        f"Dataset: {summary['samples']} Samples, {summary['species']} Species"
    )
    ax.legend(loc="upper right", frameon=True)

    fig.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)


def main():
    args = parse_args()

    abundance_path = Path(args.abundance).resolve()
    meta_path = Path(args.meta).resolve()
    pipeline_path = Path(args.pipeline).resolve()
    output_dir = Path(args.outdir).resolve()

    if not abundance_path.exists():
        raise FileNotFoundError(f"Abundance file not found: {abundance_path}")
    if not meta_path.exists():
        raise FileNotFoundError(f"Metadata file not found: {meta_path}")
    if not pipeline_path.exists():
        raise FileNotFoundError(f"Pipeline script not found: {pipeline_path}")

    summary = load_dataset_summary(abundance_path, meta_path)
    max_cores = os.cpu_count() or 1
    core_counts = normalize_core_counts(args.cores, max_cores)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(
        "[setup] Benchmarking "
        f"{summary['pairs']} ordered species pairs from "
        f"{summary['samples']} samples and {summary['species']} species."
    )
    print(f"[setup] Core counts: {core_counts}")
    print(f"[setup] Requested backend: {args.backend}")

    metrics = benchmark_pipeline(
        pipeline_path=pipeline_path,
        abundance_path=abundance_path,
        meta_path=meta_path,
        core_counts=core_counts,
        total_pairs=summary["pairs"],
        backend=args.backend,
        verbose=args.verbose,
        timeout_sec=args.run_timeout_sec,
    )

    metrics_path = output_dir / "dummy_scaling_metrics.csv"
    figure2_path = output_dir / "figure2_dummy_strong_scaling.png"
    figure3_path = output_dir / "figure3_dummy_parallel_efficiency.png"

    metrics.to_csv(metrics_path, index=False)
    plot_strong_scaling(metrics, summary, figure2_path)
    plot_parallel_efficiency(metrics, summary, figure3_path)

    print(f"[done] Metrics saved to: {metrics_path}")
    print(f"[done] Figure 2-style plot saved to: {figure2_path}")
    print(f"[done] Figure 3-style plot saved to: {figure3_path}")


if __name__ == "__main__":
    main()
