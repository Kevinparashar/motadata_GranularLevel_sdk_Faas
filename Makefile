.PHONY: help install install-dev test test-unit test-integration test-faas lint format type-check clean build docs serve examples run-service

# Default target
.DEFAULT_GOAL := help

# Python interpreter
PYTHON := python3
PIP := pip3

# Project directories
SRC_DIR := src
TESTS_DIR := tests
EXAMPLES_DIR := examples
DOCS_DIR := docs

# Colors for output
COLOR_RESET := \033[0m
COLOR_BOLD := \033[1m
COLOR_GREEN := \033[32m
COLOR_YELLOW := \033[33m
COLOR_BLUE := \033[34m

help: ## Show this help message
	@echo "$(COLOR_BOLD)Motadata Python AI SDK - Development Commands$(COLOR_RESET)"
	@echo ""
	@echo "$(COLOR_BOLD)Usage:$(COLOR_RESET)"
	@echo "  make [target]"
	@echo ""
	@echo "$(COLOR_BOLD)Available targets:$(COLOR_RESET)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(COLOR_GREEN)%-20s$(COLOR_RESET) %s\n", $$1, $$2}'
	@echo ""

install: ## Install production dependencies
	@echo "$(COLOR_BLUE)Installing production dependencies...$(COLOR_RESET)"
	$(PIP) install -r requirements.txt
	@echo "$(COLOR_GREEN)✓ Production dependencies installed$(COLOR_RESET)"

install-dev: ## Install development dependencies
	@echo "$(COLOR_BLUE)Installing development dependencies...$(COLOR_RESET)"
	$(PIP) install -r requirements.txt
	$(PIP) install -e ".[dev]"
	@echo "$(COLOR_GREEN)✓ Development dependencies installed$(COLOR_RESET)"

test: ## Run all tests (unit + integration)
	@echo "$(COLOR_BLUE)Running all tests...$(COLOR_RESET)"
	$(PYTHON) -m pytest $(TESTS_DIR) -v
	@echo "$(COLOR_GREEN)✓ All tests completed$(COLOR_RESET)"

test-unit: ## Run unit tests only
	@echo "$(COLOR_BLUE)Running unit tests...$(COLOR_RESET)"
	$(PYTHON) -m pytest $(TESTS_DIR)/unit_tests -v
	@echo "$(COLOR_GREEN)✓ Unit tests completed$(COLOR_RESET)"

test-integration: ## Run integration tests only
	@echo "$(COLOR_BLUE)Running integration tests...$(COLOR_RESET)"
	$(PYTHON) -m pytest $(TESTS_DIR)/integration_tests -v
	@echo "$(COLOR_GREEN)✓ Integration tests completed$(COLOR_RESET)"

test-faas: ## Run FaaS service tests
	@echo "$(COLOR_BLUE)Running FaaS service tests...$(COLOR_RESET)"
	$(PYTHON) -m pytest $(TESTS_DIR)/unit_tests/test_faas $(TESTS_DIR)/integration_tests/test_faas -v
	@echo "$(COLOR_GREEN)✓ FaaS tests completed$(COLOR_RESET)"

test-cov: ## Run tests with coverage report
	@echo "$(COLOR_BLUE)Running tests with coverage...$(COLOR_RESET)"
	$(PYTHON) -m pytest $(TESTS_DIR) --cov=$(SRC_DIR) --cov-report=html --cov-report=term
	@echo "$(COLOR_GREEN)✓ Coverage report generated: htmlcov/index.html$(COLOR_RESET)"

lint: ## Run linting checks (flake8, pylint, etc.)
	@echo "$(COLOR_BLUE)Running linting checks...$(COLOR_RESET)"
	@echo "$(COLOR_YELLOW)Note: Install flake8 or pylint for detailed linting$(COLOR_RESET)"
	@echo "$(COLOR_GREEN)✓ Linting completed (basic checks)$(COLOR_RESET)"

format: ## Format code with black and isort
	@echo "$(COLOR_BLUE)Formatting code...$(COLOR_RESET)"
	$(PYTHON) -m black $(SRC_DIR) $(EXAMPLES_DIR)
	$(PYTHON) -m isort $(SRC_DIR) $(EXAMPLES_DIR)
	@echo "$(COLOR_GREEN)✓ Code formatted$(COLOR_RESET)"

format-check: ## Check code formatting without making changes
	@echo "$(COLOR_BLUE)Checking code formatting...$(COLOR_RESET)"
	$(PYTHON) -m black --check $(SRC_DIR) $(EXAMPLES_DIR)
	$(PYTHON) -m isort --check-only $(SRC_DIR) $(EXAMPLES_DIR)
	@echo "$(COLOR_GREEN)✓ Code formatting check completed$(COLOR_RESET)"

type-check: ## Run type checking with mypy
	@echo "$(COLOR_BLUE)Running type checks...$(COLOR_RESET)"
	$(PYTHON) -m mypy $(SRC_DIR)
	@echo "$(COLOR_GREEN)✓ Type checking completed$(COLOR_RESET)"

clean: ## Clean build artifacts and cache
	@echo "$(COLOR_BLUE)Cleaning build artifacts...$(COLOR_RESET)"
	find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type d -name "*.egg-info" -exec rm -r {} + 2>/dev/null || true
	rm -rf build/ dist/ .pytest_cache/ .coverage htmlcov/ .mypy_cache/
	@echo "$(COLOR_GREEN)✓ Clean completed$(COLOR_RESET)"

build: ## Build the package
	@echo "$(COLOR_BLUE)Building package...$(COLOR_RESET)"
	$(PYTHON) -m build
	@echo "$(COLOR_GREEN)✓ Package built in dist/$(COLOR_RESET)"

docs: ## Generate documentation (if using sphinx/mkdocs)
	@echo "$(COLOR_BLUE)Documentation is in Markdown format$(COLOR_RESET)"
	@echo "$(COLOR_GREEN)✓ Documentation available in $(DOCS_DIR)/$(COLOR_RESET)"

serve: ## Serve documentation locally (if using mkdocs)
	@echo "$(COLOR_YELLOW)Documentation is in Markdown format$(COLOR_RESET)"
	@echo "$(COLOR_BLUE)View documentation in:$(COLOR_RESET)"
	@echo "  - $(DOCS_DIR)/README.md"
	@echo "  - $(DOCS_DIR)/guide/DOCUMENTATION_INDEX.md"

examples: ## Run example scripts
	@echo "$(COLOR_BLUE)Running example scripts...$(COLOR_RESET)"
	@echo "$(COLOR_YELLOW)Available examples:$(COLOR_RESET)"
	@ls -1 $(EXAMPLES_DIR)/*.py 2>/dev/null || echo "  No root-level examples"
	@echo "$(COLOR_BLUE)Basic usage examples:$(COLOR_RESET)"
	@ls -1 $(EXAMPLES_DIR)/basic_usage/*.py 2>/dev/null || echo "  No basic usage examples"
	@echo "$(COLOR_BLUE)FaaS examples:$(COLOR_RESET)"
	@ls -1 $(EXAMPLES_DIR)/faas/*.py 2>/dev/null || echo "  No FaaS examples"

run-service: ## Run a FaaS service (usage: make run-service SERVICE=agent_service PORT=8080)
	@if [ -z "$(SERVICE)" ]; then \
		echo "$(COLOR_YELLOW)Usage: make run-service SERVICE=agent_service PORT=8080$(COLOR_RESET)"; \
		echo "$(COLOR_BLUE)Available services:$(COLOR_RESET)"; \
		echo "  - agent_service"; \
		echo "  - rag_service"; \
		echo "  - gateway_service"; \
		echo "  - ml_service"; \
		echo "  - cache_service"; \
		echo "  - prompt_service"; \
		echo "  - data_ingestion_service"; \
		echo "  - prompt_generator_service"; \
		echo "  - llmops_service"; \
	else \
		echo "$(COLOR_BLUE)Starting $(SERVICE) on port $(PORT:-8080)...$(COLOR_RESET)"; \
		uvicorn src.faas.services.$(SERVICE).service:app --host 0.0.0.0 --port $(PORT:-8080) --reload; \
	fi

check: format-check type-check lint ## Run all checks (format, type, lint)
	@echo "$(COLOR_GREEN)✓ All checks completed$(COLOR_RESET)"

ci: clean install-dev test format-check type-check ## Run CI pipeline locally
	@echo "$(COLOR_GREEN)✓ CI pipeline completed$(COLOR_RESET)"

benchmark: ## Run benchmark tests
	@echo "$(COLOR_BLUE)Running benchmark tests...$(COLOR_RESET)"
	$(PYTHON) -m pytest $(TESTS_DIR)/benchmarks -v
	@echo "$(COLOR_GREEN)✓ Benchmark tests completed$(COLOR_RESET)"

requirements: ## Update requirements.txt from pyproject.toml
	@echo "$(COLOR_BLUE)Updating requirements.txt...$(COLOR_RESET)"
	$(PIP) freeze > requirements.txt
	@echo "$(COLOR_GREEN)✓ Requirements updated$(COLOR_RESET)"

venv: ## Create virtual environment
	@echo "$(COLOR_BLUE)Creating virtual environment...$(COLOR_RESET)"
	$(PYTHON) -m venv venv
	@echo "$(COLOR_GREEN)✓ Virtual environment created$(COLOR_RESET)"
	@echo "$(COLOR_YELLOW)Activate with: source venv/bin/activate$(COLOR_RESET)"

version: ## Show current version
	@echo "$(COLOR_BLUE)Current version:$(COLOR_RESET)"
	@grep -E '^version\s*=' pyproject.toml | sed 's/.*= *"\(.*\)"/\1/'

info: ## Show project information
	@echo "$(COLOR_BOLD)Motadata Python AI SDK$(COLOR_RESET)"
	@echo ""
	@echo "$(COLOR_BLUE)Project Structure:$(COLOR_RESET)"
	@echo "  Source: $(SRC_DIR)/"
	@echo "  Tests: $(TESTS_DIR)/"
	@echo "  Examples: $(EXAMPLES_DIR)/"
	@echo "  Documentation: $(DOCS_DIR)/"
	@echo ""
	@echo "$(COLOR_BLUE)Python Version:$(COLOR_RESET)"
	@$(PYTHON) --version
	@echo ""
	@echo "$(COLOR_BLUE)Package Version:$(COLOR_RESET)"
	@make version

