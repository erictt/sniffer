# Sniffer - Video Processing and Transcription Tool
# Makefile for development tasks

.DEFAULT_GOAL := help
SHELL := /bin/bash

# Variables
PYTHON := python
UV := uv
PACKAGE_NAME := sniffer
SRC_DIR := sniffer
TESTS_DIR := tests
DOCS_DIR := docs

# Colors for output
BLUE := \033[36m
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
RESET := \033[0m

##@ Help
.PHONY: help
help: ## Display this help message
	@echo "$(BLUE)Sniffer Development Makefile$(RESET)"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"; printf "Usage:\n  make $(BLUE)<target>$(RESET)\n"} /^[a-zA-Z_0-9-]+:.*?##/ { printf "  $(BLUE)%-20s$(RESET) %s\n", $$1, $$2 } /^##@/ { printf "\n$(YELLOW)%s$(RESET)\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Environment Setup
.PHONY: install
install: ## Install project dependencies with uv
	@echo "$(GREEN)Installing dependencies with uv...$(RESET)"
	$(UV) sync
	@echo "$(GREEN)Dependencies installed successfully!$(RESET)"

.PHONY: install-dev
install-dev: ## Install project with development dependencies
	@echo "$(GREEN)Installing with development dependencies...$(RESET)"
	$(UV) sync --group dev
	@echo "$(GREEN)Development environment ready!$(RESET)"

.PHONY: install-pip
install-pip: ## Install project with pip (fallback)
	@echo "$(YELLOW)Installing with pip...$(RESET)"
	pip install -e ".[dev]"

.PHONY: setup
setup: install-dev setup-dirs ## Complete development setup
	@echo "$(GREEN)Development environment setup complete!$(RESET)"

.PHONY: setup-dirs
setup-dirs: ## Create required data directories
	@echo "$(GREEN)Setting up data directories...$(RESET)"
	$(PYTHON) main.py setup

##@ Code Quality
.PHONY: format
format: ## Format code with ruff
	@echo "$(GREEN)Formatting code...$(RESET)"
	$(UV) run ruff format .
	@echo "$(GREEN)Code formatted successfully!$(RESET)"

.PHONY: lint
lint: ## Lint code with ruff
	@echo "$(GREEN)Linting code...$(RESET)"
	$(UV) run ruff check .

.PHONY: lint-fix
lint-fix: ## Lint and automatically fix issues
	@echo "$(GREEN)Linting and fixing code...$(RESET)"
	$(UV) run ruff check --fix .
	@echo "$(GREEN)Code linted and fixed!$(RESET)"

.PHONY: type-check
type-check: ## Run type checking with mypy
	@echo "$(GREEN)Running type checks...$(RESET)"
	$(UV) run mypy $(SRC_DIR)/ --ignore-missing-imports
	@echo "$(GREEN)Type checking complete!$(RESET)"

.PHONY: check
check: lint type-check ## Run all code quality checks
	@echo "$(GREEN)All quality checks completed!$(RESET)"

##@ Testing
.PHONY: test
test: ## Run tests with pytest
	@echo "$(GREEN)Running tests...$(RESET)"
	$(UV) run pytest $(TESTS_DIR)/ -v

.PHONY: test-cov
test-cov: ## Run tests with coverage report
	@echo "$(GREEN)Running tests with coverage...$(RESET)"
	$(UV) run pytest $(TESTS_DIR)/ --cov=$(SRC_DIR) --cov-report=html --cov-report=term

.PHONY: test-fast
test-fast: ## Run tests in parallel (fast)
	@echo "$(GREEN)Running tests in parallel...$(RESET)"
	$(UV) run pytest $(TESTS_DIR)/ -v -n auto

.PHONY: test-watch
test-watch: ## Run tests in watch mode
	@echo "$(GREEN)Running tests in watch mode...$(RESET)"
	$(UV) run pytest-watch $(TESTS_DIR)/ --

.PHONY: test-unit
test-unit: ## Run unit tests only
	@echo "$(GREEN)Running unit tests...$(RESET)"
	$(UV) run pytest $(TESTS_DIR)/ -v -m "not integration"

.PHONY: test-integration
test-integration: ## Run integration tests only
	@echo "$(GREEN)Running integration tests...$(RESET)"
	$(UV) run pytest $(TESTS_DIR)/ -v -m "integration"

##@ Application
.PHONY: run
run: ## Run the application help
	@echo "$(GREEN)Running Sniffer CLI...$(RESET)"
	$(PYTHON) main.py --help

.PHONY: process-sample
process-sample: ## Process sample video (requires sample.mp4 in current directory)
	@echo "$(GREEN)Processing sample video...$(RESET)"
	@if [ -f "sample.mp4" ]; then \
		$(PYTHON) main.py process sample.mp4 --frames middle --verbose; \
	else \
		echo "$(RED)Error: sample.mp4 not found. Place a sample video file in the current directory.$(RESET)"; \
		exit 1; \
	fi

.PHONY: info-sample
info-sample: ## Show info for sample video
	@echo "$(GREEN)Showing sample video info...$(RESET)"
	@if [ -f "sample.mp4" ]; then \
		$(PYTHON) main.py info sample.mp4; \
	else \
		echo "$(RED)Error: sample.mp4 not found.$(RESET)"; \
		exit 1; \
	fi

.PHONY: demo
demo: setup-dirs ## Run a complete demo (requires sample.mp4)
	@echo "$(GREEN)Running Sniffer demo...$(RESET)"
	@if [ -f "sample.mp4" ]; then \
		$(PYTHON) main.py info sample.mp4; \
		echo ""; \
		$(PYTHON) main.py process sample.mp4 --frames middle --verbose; \
	else \
		echo "$(YELLOW)No sample.mp4 found. Creating directories and showing help instead...$(RESET)"; \
		$(PYTHON) main.py setup; \
		$(PYTHON) main.py --help; \
	fi

##@ Cleanup
.PHONY: clean
clean: clean-cache clean-test clean-build ## Clean all generated files
	@echo "$(GREEN)All cleanup completed!$(RESET)"

.PHONY: clean-cache
clean-cache: ## Remove Python cache files
	@echo "$(GREEN)Cleaning Python cache...$(RESET)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type f -name ".coverage" -delete

.PHONY: clean-test
clean-test: ## Remove test artifacts
	@echo "$(GREEN)Cleaning test artifacts...$(RESET)"
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .coverage

.PHONY: clean-build
clean-build: ## Remove build artifacts
	@echo "$(GREEN)Cleaning build artifacts...$(RESET)"
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/

.PHONY: clean-data
clean-data: ## Remove processed data (WARNING: This deletes your processed videos!)
	@echo "$(RED)WARNING: This will delete all processed data!$(RESET)"
	@read -p "Are you sure? (y/N): " confirm && \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		echo "$(GREEN)Cleaning data directories...$(RESET)"; \
		rm -rf data/audio/* data/video_frames/* data/transcripts/*; \
		echo "$(GREEN)Data directories cleaned!$(RESET)"; \
	else \
		echo "$(YELLOW)Cleanup cancelled.$(RESET)"; \
	fi

##@ Release & Deployment
.PHONY: build
build: clean-build ## Build distribution packages
	@echo "$(GREEN)Building distribution packages...$(RESET)"
	$(UV) build
	@echo "$(GREEN)Build completed! Check dist/ directory.$(RESET)"

.PHONY: install-local
install-local: build ## Install package locally from build
	@echo "$(GREEN)Installing package locally...$(RESET)"
	pip install dist/*.whl --force-reinstall
	@echo "$(GREEN)Package installed! Try: sniffer --help$(RESET)"

.PHONY: version
version: ## Show current version
	@echo "$(GREEN)Current version:$(RESET)"
	@grep version pyproject.toml | head -1

##@ Utilities
.PHONY: deps-update
deps-update: ## Update all dependencies
	@echo "$(GREEN)Updating dependencies...$(RESET)"
	$(UV) sync --upgrade

.PHONY: deps-tree
deps-tree: ## Show dependency tree
	@echo "$(GREEN)Dependency tree:$(RESET)"
	$(UV) tree

.PHONY: security-check
security-check: ## Check for security vulnerabilities
	@echo "$(GREEN)Running security checks...$(RESET)"
	$(UV) run bandit -r $(SRC_DIR)/

.PHONY: size-check
size-check: ## Check package size
	@echo "$(GREEN)Checking package size...$(RESET)"
	@if [ -d "dist" ]; then \
		ls -lh dist/; \
	else \
		echo "$(YELLOW)No dist/ directory found. Run 'make build' first.$(RESET)"; \
	fi

.PHONY: env-info
env-info: ## Show environment information
	@echo "$(GREEN)Environment Information:$(RESET)"
	@echo "Python: $$(python --version)"
	@echo "UV: $$(uv --version 2>/dev/null || echo 'Not installed')"
	@echo "Current directory: $$(pwd)"
	@echo "Virtual environment: $${VIRTUAL_ENV:-'None'}"

##@ Development Workflow
.PHONY: dev
dev: clean install-dev check test ## Complete development cycle
	@echo "$(GREEN)Development cycle completed successfully!$(RESET)"

.PHONY: pre-commit
pre-commit: format lint-fix test ## Pre-commit checks
	@echo "$(GREEN)Pre-commit checks completed!$(RESET)"

.PHONY: ci
ci: install-dev check test-cov ## Continuous Integration workflow
	@echo "$(GREEN)CI workflow completed!$(RESET)"

.PHONY: all
all: clean install-dev check test-cov build ## Run everything
	@echo "$(GREEN)Complete build and test cycle completed!$(RESET)"

# Ensure targets run even if files with same names exist
.PHONY: install install-dev install-pip setup setup-dirs format lint lint-fix type-check check test test-cov test-fast test-watch test-unit test-integration run process-sample info-sample demo clean clean-cache clean-test clean-build clean-data build install-local version deps-update deps-tree security-check size-check env-info dev pre-commit ci all help