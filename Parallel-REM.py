#!/usr/bin/env python3
"""
Parallel-REM: A High-Performance Parallel Pipeline for Microbiome Network Inference.
"""

import os
import argparse
import warnings
import multiprocessing
import numpy as np
import pandas as pd
from scipy.stats import norm
from joblib import Parallel, delayed
from tqdm.auto import tqdm

# Statsmodels
import statsmodels.api as sm
from statsmodels.robust.robust_linear_model import RLM
from statsmodels.robust.norms import HuberT
from statsmodels.tools import add_constant
from statsmodels.stats.multitest import fdrcorrection

# Thread control to prevent conflicts with Parallel execution
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
warnings.filterwarnings("ignore")

# ============================================================
# 1. ROBUST Regression Function
# ============================================================
def compute_meta_lm(df, var1, var2, study_col, study_list):
    # FIX 1: Force warnings to be ignored INSIDE the worker process
    import warnings
    warnings.filterwarnings("ignore")
    
    rows = []
    
    for study in study_list:
        sub = df[df[study_col] == study]
        x_raw = sub[var2].values.astype(float)
        y_raw = sub[var1].values.astype(float)
        
        mask = (~np.isnan(x_raw)) & (~np.isnan(y_raw))
        x = x_raw[mask]
        y = y_raw[mask]

        # --- Strict Biological Filtering ---
        if len(x) < 5 or np.std(x) == 0 or np.std(y) == 0:
            continue
            
        n_cooccur = np.sum((x != 0) & (y != 0))
        min_required = max(5, int(len(x) * 0.10)) 
        
        if n_cooccur < min_required:
            continue

        # --- Standardization ---
        x = (x - np.mean(x)) / np.std(x)
        y = (y - np.mean(y)) / np.std(y)

        ti, pi, direction = 0.0, 1.0, 0.0

        try:
            X = add_constant(x)
            model = RLM(y, X, M=HuberT())
            result = model.fit(maxiter=50)

            if len(result.tvalues) > 1:
                t_val = result.tvalues[1]
                if np.abs(t_val) > 100: 
                    ti = np.sign(t_val) * 100.0
                    pi = 1e-50 
                    direction = np.sign(ti)
                else:
                    ti = float(t_val)
                    pi = float(result.pvalues[1])
                    direction = np.sign(ti)
            else:
                ti, pi = 0.0, 1.0

        except:
            try:
                ols = sm.OLS(y, X).fit()
                robust = ols.get_robustcov_results(cov_type='HC3')
                
                if len(robust.tvalues) > 1 and np.isfinite(robust.tvalues[1]):
                    ti = float(robust.tvalues[1])
                    if np.abs(ti) > 100:
                        ti = np.sign(ti) * 100.0
                        pi = 1e-50
                        direction = np.sign(ti)
                    else:
                        pi = float(robust.pvalues[1])
                        direction = np.sign(ti)
                else:
                    ti, pi = 0.0, 1.0
            except:
                ti, pi = 0.0, 1.0

        rows.append([study, ti, len(y), 1, pi, direction])

    df_study = pd.DataFrame(rows, columns=["dataset", "ti", "ni", "mi", "pi", "di"])
    if df_study.empty:
        return None

    # --- META-ANALYSIS POOLING (FISHER'S Z) ---
    df_study["r"] = df_study["ti"] / np.sqrt(df_study["ni"].clip(lower=1))
    df_study["r"] = df_study["r"].clip(-0.995, 0.995)
    df_study["yi"] = np.arctanh(df_study["r"])
    df_study["vi"] = 1.0 / np.maximum(df_study["ni"] - 3.0, 1.0)

    wi = 1.0 / df_study["vi"]
    yi = df_study["yi"]

    try:
        fixed_mu = np.sum(wi * yi) / np.sum(wi)
        Q = np.sum(wi * (yi - fixed_mu)**2)
        df_Q = len(df_study) - 1
        denom = np.sum(wi) - np.sum(wi**2) / np.sum(wi)
        tau2 = max((Q - df_Q) / denom, 0) if denom > 0 else 0

        w_star = 1.0 / (df_study["vi"] + tau2)
        mu_hat = np.sum(w_star * yi) / np.sum(w_star)
        
        se_mu = np.sqrt(1.0 / np.sum(w_star))
        z_score = abs(mu_hat / se_mu)
        combined_p = 2 * (1 - norm.cdf(z_score))
        
    except:
        mu_hat, combined_p = 0.0, 1.0

    return {"df_studies": df_study, "beta": float(mu_hat), "pval": combined_p}

# ============================================================
# 2. Worker Function
# ============================================================
def run_single_pair(s1, s2, df, study_col, study_list):
    if s1 == s2:
        return (s1, s2, 0.0, 1.0, 1.0, 0.0)

    out = compute_meta_lm(df, s1, s2, study_col, study_list)
    if out is None:
        return (s1, s2, 0.0, 1.0, 1.0, 0.0)

    beta = out["beta"]
    pval = out["pval"]
    df_s = out["df_studies"]

    if len(df_s) > 0:
        consistency = np.mean(np.sign(df_s["di"]) == np.sign(beta))
    else:
        consistency = 0.0

    return (s1, s2, beta, pval, consistency, np.sign(beta))

# ============================================================
# 3. Main Runner
# ============================================================
def REM_network(df, species_list, study_col, study_list, n_jobs=4, batch_size=50):
    total_pairs = len(species_list)**2
    print(f"[✔] Total pairs to compute: {total_pairs:,}")
    print(f"[✔] Using {n_jobs} CPU cores with batch size {batch_size}")

    pairs = [(s1, s2) for s1 in species_list for s2 in species_list]

    def tqdm_wrapper(pairs):
        for a, b in tqdm(pairs, total=total_pairs, desc="Computing", ncols=100):
            yield a, b

    # FIX 2: Use context manager "with Parallel" to guarantee clean teardown of workers
    with Parallel(n_jobs=n_jobs, backend="loky", batch_size=batch_size) as parallel:
        results = parallel(
            delayed(run_single_pair)(s1, s2, df, study_col, study_list)
            for (s1, s2) in tqdm_wrapper(pairs)
        )

    est = pd.DataFrame(0.0, index=species_list, columns=species_list)
    pval = pd.DataFrame(1.0, index=species_list, columns=species_list)
    consistency = pd.DataFrame(1.0, index=species_list, columns=species_list)
    
    for s1, s2, beta, p, cons, signb in results:
        est.loc[s1, s2] = beta
        pval.loc[s1, s2] = p
        consistency.loc[s1, s2] = cons

    print("[✔] Applying Global FDR correction...")
    p_values_flat = pval.values.flatten()
    _, q_values_flat = fdrcorrection(p_values_flat)
    qval = pd.DataFrame(q_values_flat.reshape(pval.shape), index=species_list, columns=species_list)

    dir_matrix = pd.DataFrame(0, index=species_list, columns=species_list)
    sig_strong = (qval <= 0.01) & (consistency >= 0.70)
    sig_weak = (pval <= 0.05) & (consistency >= 0.70) & (~sig_strong)
    
    dir_matrix[sig_strong] = 2 * np.sign(est[sig_strong])
    dir_matrix[sig_weak] = np.sign(est[sig_weak])

    est_filtered = est.copy()
    est_filtered[qval > 0.05] = 0.0

    return {
        "est": est, 
        "est_filtered": est_filtered,
        "pval": pval, 
        "consistency": consistency, 
        "qval": qval, 
        "dir": dir_matrix
    }

# ============================================================
# 4. CLI Execution Block
# ============================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parallel-REM Network Inference Pipeline")
    parser.add_argument("--abundance", required=True, help="Path to abundance matrix CSV (samples as rows, species as columns)")
    parser.add_argument("--meta", required=True, help="Path to metadata CSV (samples as rows, must contain 'study_name' column)")
    parser.add_argument("--cores", type=int, default=-1, help="Number of CPU cores to use (-1 for all available)")
    parser.add_argument("--outdir", default="REM_Results", help="Directory to save output matrices")
    args = parser.parse_args()

    os.makedirs(args.outdir, exist_ok=True)

    print("[1] Loading Data...")
    df_abund = pd.read_csv(args.abundance, index_col=0)
    df_meta = pd.read_csv(args.meta, index_col=0)

    if "study_name" not in df_meta.columns:
        raise ValueError("Metadata CSV must contain a 'study_name' column.")

    # Align data
    common_samples = df_abund.index.intersection(df_meta.index)
    df_abund = df_abund.loc[common_samples]
    df_meta = df_meta.loc[common_samples]

    df_rem = df_abund.copy()
    df_rem["study_name"] = df_meta["study_name"].astype(str).values

    species_list = df_abund.columns.tolist()
    study_list = df_rem["study_name"].unique().tolist()

    n_jobs = multiprocessing.cpu_count() if args.cores == -1 else args.cores

    print(f"[✔] Total Samples: {len(common_samples)}")
    print(f"[✔] Species count: {len(species_list)}")
    print(f"[✔] Study count:   {len(study_list)}")

    final_results = REM_network(df_rem, species_list, "study_name", study_list, n_jobs=n_jobs)

    # Save outputs
    final_results['est'].to_csv(os.path.join(args.outdir, "rem_est_matrix.csv"))
    final_results['est_filtered'].to_csv(os.path.join(args.outdir, "rem_est_filtered_matrix.csv"))
    final_results['pval'].to_csv(os.path.join(args.outdir, "rem_pval_matrix.csv"))
    final_results['consistency'].to_csv(os.path.join(args.outdir, "rem_consistency_matrix.csv"))
    final_results['qval'].to_csv(os.path.join(args.outdir, "rem_qval_matrix.csv"))
    final_results['dir'].to_csv(os.path.join(args.outdir, "rem_dir_matrix.csv"))

    print(f"\n[✔] Analysis Complete. All matrices saved to: {args.outdir}/")

    # Bypass Python 3.13 macOS multiprocessing teardown bug
    os._exit(0)