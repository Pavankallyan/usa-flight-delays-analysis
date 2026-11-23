# Shortcuts for the flight-delays analysis.
PY ?= python3

.PHONY: setup test demo clean

setup: ## Install dependencies
	$(PY) -m pip install -r requirements.txt

test: ## Run the pytest suite (data validation + analysis unit tests)
	$(PY) -m pytest tests/ -q

demo: ## Print the delay summary for the 100k-row sample
	$(PY) examples/delay_explorer.py

clean: ## Remove Python caches
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type d -name .pytest_cache -prune -exec rm -rf {} +
