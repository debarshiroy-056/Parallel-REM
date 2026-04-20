# Parallel-REM: High-Performance Microbiome Network Inference

[![bioRxiv](https://img.shields.io/badge/bioRxiv-Preprint-red)](https://doi.org/10.64898/2026.03.27.714858)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

Parallel-REM is a highly scalable Python pipeline for inferring **microbial interaction networks** using **Random Effects Models (REM)**.
The pipeline is designed to address the severe computational bottlenecks that arise when constructing large-scale ecological networks from high-dimensional microbiome datasets.

The system combines **algorithmic sparsity filtering**, **batched parallel execution**, and **robust statistical modeling** to enable scalable microbiome network inference on modern multi-core architectures.

---

## Paper

The methodology and benchmarking results are described in our preprint:

**Scalable Microbiome Network Inference: Mitigating Sparsity and Computational Bottlenecks in Random Effects Models**

Debarshi Roy, Tarini Shankar Ghosh

Microbiome Informatics Lab, IIIT Delhi

bioRxiv (2026)

DOI: https://doi.org/10.64898/2026.03.27.714858

---

## Key Features

### Algorithmic Short-Circuiting

Parallel-REM bypasses expensive robust regression calculations for zero-inflated microbial abundance matrices by applying strict biological filters:

- Variance threshold filtering
- Dynamic co-occurrence sparsity filtering

This prevents convergence failures and eliminates unnecessary computations.

---

### High-Performance Parallelization

The pipeline uses a **batched master-worker architecture** implemented with `joblib` and the `loky` backend.

This design:

- Enables efficient multi-core utilization
- Reduces inter-process communication overhead
- Achieves near-linear speedup on multi-core systems

Benchmarks demonstrate up to **26× speedup on 64-core architectures**.

---

### Memory-Bounded Execution

To avoid memory overflow on large datasets, Parallel-REM uses:

- Shared memory mapping
- Task batching
- Controlled inter-process communication

This ensures stable memory usage even when processing **tens of thousands of samples**.

---

## Installation

Clone the repository and install the required dependencies.

```bash
git clone https://github.com/debarshiroy-056/Parallel-REM.git
cd Parallel-REM

pip install numpy pandas scipy statsmodels joblib tqdm
```

### Requirements

- Python 3.8+
- NumPy
- Pandas
- SciPy
- Statsmodels
- Joblib
- tqdm

---

## Quick Start (Using Example Data)

Due to clinical privacy restrictions, the **70,000-sample dataset used in the paper cannot be publicly released**.

To enable reproducibility, we provide a **synthetic zero-inflated toy dataset** that demonstrates the pipeline workflow.

Run the pipeline using the provided example dataset:

```bash
python Parallel-REM.py \
  --abundance example_data/dummy_abundance.csv \
  --meta example_data/dummy_metadata.csv
```

### Makefile Support

A `Makefile` is included to automate toy data generation, pipeline execution, and cleaning results.

```bash
make          # generate toy data if needed and run the pipeline
make data     # generate example toy data files
make run      # execute Parallel-REM on the example toy dataset
make clean    # remove generated CSV outputs from REM_Results/
```

---

## Optional Arguments

| Argument   | Description                                                    |
| ---------- | -------------------------------------------------------------- |
| `--cores`  | Number of CPU cores to use (default: all available cores)      |
| `--outdir` | Output directory for result matrices (default: `REM_Results/`) |

Example:

```bash
python Parallel-REM.py \
  --abundance example_data/dummy_abundance.csv \
  --meta example_data/dummy_metadata.csv \
  --cores 4 \
  --outdir results/
```

---

## Output

The pipeline produces several matrices representing inferred microbial interactions:

- Network interaction matrix
- Effect size matrix
- Significance matrix (p-values / FDR corrected)

These outputs can be used for:

- Microbial ecological network analysis
- Downstream machine learning pipelines
- Graph-based microbiome studies

---

## Benchmark Summary

Parallel-REM was evaluated on a **large clinical microbiome dataset**:

- **70,185 samples**
- **466 microbial species**
- **217,156 pairwise interactions**

The optimized pipeline achieved:

- **26.1× speedup** compared to sequential execution
- Near-linear scaling up to **48 CPU cores**

---

## Repository Structure

```
Parallel-REM/
│
├── Parallel-REM.py
├── example_data/
│   ├── dummy_abundance.csv
│   └── dummy_metadata.csv
│
├── REM_Results/
│
└── README.md
```

---

## Citation

If you use **Parallel-REM** in your research, please cite:

Roy, Debarshi and Ghosh, Tarini Shankar (2026).
_Scalable Microbiome Network Inference: Mitigating Sparsity and Computational Bottlenecks in Random Effects Models._
bioRxiv.

DOI: https://doi.org/10.64898/2026.03.27.714858

BibTeX:

```bibtex
@article{roy2026parallelrem,
  title={Scalable Microbiome Network Inference: Mitigating Sparsity and Computational Bottlenecks in Random Effects Models},
  author={Roy, Debarshi and Ghosh, Tarini Shankar},
  journal={bioRxiv},
  year={2026},
  doi={10.64898/2026.03.27.714858}
}
```

---

## License

This project is licensed under the **MIT License**.

---

## Acknowledgements

This work was developed at the **Microbiome Informatics Lab, IIIT Delhi**.

---

## Star the Repository

If you find this project useful, please consider giving it a ⭐ on GitHub.
