.PHONY: help install dev data run analyze demo test lint clean

help:
	@echo "Targets:"
	@echo "  install   Install runtime dependencies"
	@echo "  dev       Install dev dependencies (pytest, matplotlib, ruff)"
	@echo "  data      Generate the synthetic cancellation dataset"
	@echo "  run       Run the classification pipeline over the dataset"
	@echo "  analyze   Print summary statistics (use 'make analyze CHARTS=1' for figures)"
	@echo "  demo      data -> run -> analyze, end to end"
	@echo "  test      Run the test suite (incl. the 50-case regression gate)"
	@echo "  lint      Run ruff"
	@echo "  clean     Remove generated artifacts"

install:
	pip install -r requirements.txt

dev:
	pip install -r requirements-dev.txt

data:
	python scripts/generate_data.py

run:
	python scripts/run_classification.py

analyze:
	python scripts/analyze_results.py $(if $(CHARTS),--charts,)

demo: data run analyze

test:
	pytest -q

lint:
	ruff check src scripts tests

clean:
	rm -f data/classified_output.csv
	rm -rf data/figures __pycache__ .pytest_cache .ruff_cache
	find . -name '__pycache__' -type d -prune -exec rm -rf {} +
