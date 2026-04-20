![1776666260390](image/README/1776666260390.png)![1776666265378](image/README/1776666265378.png)![1776666276386](image/README/1776666276386.png)# Parallel-REM

## Overview

This repository contains the `Parallel-REM` pipeline, a toy-data generator, and a benchmarking script that recreates Figure 2-style and Figure 3-style scaling plots for the dummy experiment included in `example_data/`.

## Repository Layout

```text
Parallel-REM/
├── Parallel-REM.py
├── generate_toy_data.py
├── generate_scaling_plots.py
├── Makefile
├── example_data/
│   ├── dummy_abundance.csv
│   └── dummy_metadata.csv
└── README.md
```

## Run the Pipeline

Run the main network inference pipeline on the bundled dummy dataset:

```bash
python3 Parallel-REM.py \
  --abundance example_data/dummy_abundance.csv \
  --meta example_data/dummy_metadata.csv \
  --backend loky \
  --outdir REM_Results
```

If `loky` is unavailable on a restricted system, the pipeline automatically retries with the `multiprocessing` backend.

## Generate Figure 2 and Figure 3-Like Plots

The new benchmarking script runs `Parallel-REM.py` multiple times across different CPU core counts, collects runtime metrics, and writes:

- `benchmark_results/dummy_scaling_metrics.csv`
- `benchmark_results/figure2_dummy_strong_scaling.png`
- `benchmark_results/figure3_dummy_parallel_efficiency.png`

Run it directly with the dummy experiment:

```bash
python3 generate_scaling_plots.py
```

For macOS/Python 3.13 environments, the benchmark path prioritizes `multiprocessing`
before `loky` to avoid noisy teardown messages from `loky` resource tracking.
This keeps terminal output cleaner at the end of a run.

You can also provide custom inputs or explicit core counts:

```bash
python3 generate_scaling_plots.py \
  --abundance example_data/dummy_abundance.csv \
  --meta example_data/dummy_metadata.csv \
  --backend loky \
  --run-timeout-sec 90 \
  --cores 1 2 4 8 \
  --outdir benchmark_results
```

To prevent indefinite hangs, each benchmark run is bounded by `--run-timeout-sec`.
If one backend (for example `loky`) times out or fails, the script automatically retries with fallback backends (`multiprocessing`, then `threading`) and records the selected backend in `dummy_scaling_metrics.csv`.

## Makefile Shortcuts

```bash
make data
```

Generates the dummy abundance and metadata files.

```bash
make run
```

Runs the main `Parallel-REM` pipeline on the dummy dataset.

```bash
make plots
```

Generates the Figure 2-style strong-scaling plot and Figure 3-style efficiency plot for the dummy experiment.
By default, each benchmark subprocess has a 90-second timeout.
The Makefile defaults to `BACKEND=multiprocessing` for cleaner terminal output.

Override timeout from the command line if needed:

```bash
make BENCHMARK_TIMEOUT=120 plots
```

```bash
make
```

Runs both the pipeline and the plotting workflow.

```bash
make clean
```

Removes `REM_Results/` and `benchmark_results/`.

## Authors

Debarshi Roy & Nandini Ahuja
