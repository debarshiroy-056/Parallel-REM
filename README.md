# Parallel-REM: High-Performance Microbiome Network Inference

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

Parallel-REM is a highly scalable, Python-based parallel pipeline for inferring microbial interaction networks using Random Effects Models (REM). It utilizes `statsmodels` and a batched `joblib` Master-Worker architecture to achieve massive speedups over traditional single-threaded R implementations, resolving convergence failures native to sparse biological matrices.

## Features
* **Algorithmic Short-Circuiting:** Bypasses expensive robust regression calculations for zero-inflated, non-co-occurring species pairs using variance and co-occurrence thresholds.
* **High-Performance Scaling:** Achieves near-linear speedup, scaling efficiently up to 64 CPU cores.
* **Memory Bounded:** Uses task batching and shared memory-mapping (`loky`) to prevent Out-Of-Memory (OOM) errors on large clinical datasets.

## Installation

Clone the repository and install the required dependencies (NumPy, Pandas, SciPy, Statsmodels, Joblib, tqdm):

```bash
git clone [https://github.com/debarshiroy-056/Parallel-REM.git](https://github.com/debarshiroy-056/Parallel-REM.git)
cd Parallel-REM
pip install numpy pandas scipy statsmodels joblib tqdm

Quick Start (Using Example Data)
Due to clinical privacy restrictions, the 70,000-sample dataset used in the original paper is not publicly available. However, we have provided a synthetic, zero-inflated "toy dataset" in the example_data/ directory so you can test the pipeline and observe the sparsity filters in action.

To run the pipeline on the toy dataset:

python Parallel-REM.py --abundance example_data/dummy_abundance.csv --meta example_data/dummy_metadata.csv

Optional Arguments:

--cores: Specify the number of CPU cores to use (e.g., --cores 4). Defaults to all available cores.

--outdir: Specify the output directory for the generated matrices. Defaults to REM_Results/.

Citation
If you use Parallel-REM in your research, please cite our COMSYS-2026 paper:

@inproceedings{roy2026parallel,
  title={Accelerating Microbiome Network Inference: A High-Performance Parallel Pipeline for Advanced Representation Learning},
  author={Roy, Debarshi and Ghosh, Tarini Shankar},
  booktitle={7th International Conference on Frontiers in Computing and Systems (COMSYS)},
  year={2026},
  organization={Springer}
}

