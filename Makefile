# Makefile for Parallel-REM pipeline automation

PYTHON ?= python3
OUTDIR ?= REM_Results
ABUNDANCE ?= example_data/dummy_abundance.csv
META ?= example_data/dummy_metadata.csv
TOY_SCRIPT ?= generate_toy_data.py
PIPELINE ?= Parallel-REM.py

.PHONY: all help data run clean

all: run

help:
	@echo "Usage: make [target]"
	@echo "Targets:"
	@echo "  all      - generate toy data (if needed) and run the pipeline"
	@echo "  data     - generate example toy data files"
	@echo "  run      - execute Parallel-REM on the example toy dataset"
	@echo "  clean    - remove generated result matrices from $(OUTDIR)"

data: $(ABUNDANCE) $(META)

$(ABUNDANCE) $(META): $(TOY_SCRIPT)
	$(PYTHON) $(TOY_SCRIPT)

run: data
	$(PYTHON) $(PIPELINE) --abundance $(ABUNDANCE) --meta $(META) --outdir $(OUTDIR)

clean:
	@echo "Removing result folder $(OUTDIR)"
	@rm -rf $(OUTDIR)
