.PHONY: help install test coverage lint format clean check dev-setup

help:  ## Show this help message
	@echo "Usage: make [target]"
	@echo ""
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

install:  ## Install development dependencies
	pip install -r requirements.txt

test:  ## Run tests
	pytest test_git_commitai.py -v

coverage:  ## Run tests with coverage report
	pytest test_git_commitai.py -v --cov=git_commitai --cov-report=term-missing --cov-report=html
	@echo "HTML coverage report generated in htmlcov/index.html"

lint:  ## Run linting checks
	black --check git_commitai.py test_git_commitai.py
	flake8 git_commitai.py test_git_commitai.py --max-line-length=100 --extend-ignore=E203,W503

format:  ## Format code with black
	black git_commitai.py test_git_commitai.py

clean:  ## Clean up generated files
	rm -rf __pycache__
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf coverage.xml
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete

check: lint test  ## Run all checks (lint + test)

dev-setup: install  ## Set up development environment
	@echo "Development environment ready!"
	@echo "Run 'make test' to run tests"
	@echo "Run 'make coverage' to see coverage report"
