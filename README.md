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