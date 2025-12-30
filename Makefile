# Makefile for Law Enforcement Data Fairness & Bias Audit

.PHONY: help install setup test run-analysis dashboard clean lint format

# Default target
help:
	@echo "Available commands:"
	@echo "  install      - Install Python dependencies"
	@echo "  setup        - Set up project environment"
	@echo "  test         - Run tests"
	@echo "  run-analysis - Run complete bias analysis"
	@echo "  dashboard    - Start interactive dashboard"
	@echo "  sample-data  - Generate sample data for testing"
	@echo "  clean        - Clean up generated files"
	@echo "  lint         - Run code linting"
	@echo "  format       - Format code with black"

# Installation and setup
install:
	pip install -r requirements.txt

setup: install
	mkdir -p data logs output
	cp .env.example .env
	@echo "Setup complete! Edit .env file with your configuration."

# Testing
test:
	python -m pytest tests/ -v

# Analysis commands
run-analysis:
	python scripts/run_analysis.py --data-source sample --save-to-db

run-analysis-fbi:
	python scripts/run_analysis.py --data-source fbi --max-pages 5 --save-to-db

sample-data:
	python scripts/run_analysis.py --data-source sample --output-dir output/sample

# Dashboard
dashboard:
	python scripts/start_dashboard.py

dashboard-dev:
	python scripts/start_dashboard.py --port 8502

# Development tools
lint:
	flake8 src/ scripts/ --max-line-length=100 --ignore=E203,W503

format:
	black src/ scripts/ --line-length=100

type-check:
	mypy src/ --ignore-missing-imports

# Cleanup
clean:
	rm -rf __pycache__ .pytest_cache .mypy_cache
	rm -rf output/* logs/*
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete

# Database operations
init-db:
	python -c "from src.database.connection import DatabaseManager; db = DatabaseManager(); db.create_tables(); print('Database initialized')"

reset-db:
	rm -f data/fairness_audit.db
	$(MAKE) init-db

# Documentation
docs:
	@echo "Generating documentation..."
	@echo "Project structure:" > docs/structure.md
	@find . -type f -name "*.py" | head -20 >> docs/structure.md

# Docker commands (if using Docker)
docker-build:
	docker build -t fairness-audit .

docker-run:
	docker run -p 8501:8501 fairness-audit

# Quick start for new users
quickstart: setup sample-data dashboard
	@echo "Quick start complete!"
	@echo "1. Sample analysis has been run"
	@echo "2. Dashboard is starting on http://localhost:8501"
	@echo "3. Check output/ directory for results"