# Makefile for Parallel-REM pipeline automation

PYTHON ?= python3
OUTDIR ?= REM_Results
BENCHMARK_OUTDIR ?= benchmark_results
ABUNDANCE ?= example_data/dummy_abundance.csv
META ?= example_data/dummy_metadata.csv
BACKEND ?= multiprocessing
BENCHMARK_TIMEOUT ?= 90
TOY_SCRIPT ?= generate_toy_data.py
PIPELINE ?= Parallel-REM.py
BENCHMARK_SCRIPT ?= generate_scaling_plots.py

.PHONY: all help data run plots clean

all: run plots

help:
	@echo "Usage: make [target]"
	@echo "Targets:"
	@echo "  all      - generate toy data, run the pipeline, and create scaling plots"
	@echo "  data     - generate example toy data files"
	@echo "  run      - execute Parallel-REM on the example toy dataset"
	@echo "  plots    - benchmark the dummy dataset and generate Figure 2/3-like plots"
	@echo "             (uses BENCHMARK_TIMEOUT seconds per benchmark run)"
	@echo "  clean    - remove generated result matrices and benchmark plots"

data: $(ABUNDANCE) $(META)

$(ABUNDANCE) $(META): $(TOY_SCRIPT)
	$(PYTHON) $(TOY_SCRIPT)

run: data
	$(PYTHON) $(PIPELINE) --abundance $(ABUNDANCE) --meta $(META) --backend $(BACKEND) --outdir $(OUTDIR)

plots: data
	$(PYTHON) $(BENCHMARK_SCRIPT) --abundance $(ABUNDANCE) --meta $(META) --pipeline $(PIPELINE) --backend $(BACKEND) --run-timeout-sec $(BENCHMARK_TIMEOUT) --outdir $(BENCHMARK_OUTDIR)

clean:
	@echo "Removing result folder $(OUTDIR)"
	@rm -rf $(OUTDIR)
	@echo "Removing benchmark folder $(BENCHMARK_OUTDIR)"
	@rm -rf $(BENCHMARK_OUTDIR)
