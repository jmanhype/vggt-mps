# VGGT-MPS Makefile
# Modern development workflow with uv

.PHONY: help install dev test demo benchmark format lint clean model run web check all

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

# Python executable
PYTHON := python
UV := uv

help: ## Show this help message
	@echo "$(BLUE)VGGT-MPS Development Commands$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)Quick Start:$(NC)"
	@echo "  make install    # Install dependencies"
	@echo "  make test       # Run tests"
	@echo "  make demo       # Run demo"

install: ## Install project with uv
	@echo "$(BLUE)Installing VGGT-MPS with uv...$(NC)"
	$(UV) pip install -e .
	@echo "$(GREEN)✓ Installation complete!$(NC)"

dev: ## Install with development dependencies
	@echo "$(BLUE)Installing development dependencies...$(NC)"
	$(UV) pip install -e ".[dev]"
	@echo "$(GREEN)✓ Development environment ready!$(NC)"

web-deps: ## Install web interface dependencies
	@echo "$(BLUE)Installing web dependencies...$(NC)"
	$(UV) pip install -e ".[web]"
	@echo "$(GREEN)✓ Web dependencies installed!$(NC)"

all-deps: ## Install all optional dependencies
	@echo "$(BLUE)Installing all dependencies...$(NC)"
	$(UV) pip install -e ".[all]"
	@echo "$(GREEN)✓ All dependencies installed!$(NC)"

test: ## Run test suite
	@echo "$(BLUE)Running tests...$(NC)"
	$(PYTHON) main.py test --suite all

test-mps: ## Run MPS-specific tests
	@echo "$(BLUE)Testing MPS support...$(NC)"
	$(PYTHON) main.py test --suite mps

test-sparse: ## Run sparse attention tests
	@echo "$(BLUE)Testing sparse attention...$(NC)"
	$(PYTHON) main.py test --suite sparse

demo: ## Run demo
	@echo "$(BLUE)Running VGGT demo...$(NC)"
	$(PYTHON) main.py demo

demo-kitchen: ## Run kitchen dataset demo
	@echo "$(BLUE)Running kitchen demo...$(NC)"
	$(PYTHON) main.py demo --kitchen --images 4

benchmark: ## Run performance benchmarks
	@echo "$(BLUE)Running benchmarks...$(NC)"
	$(PYTHON) main.py benchmark

benchmark-compare: ## Compare sparse vs dense performance
	@echo "$(BLUE)Comparing sparse vs dense...$(NC)"
	$(PYTHON) main.py benchmark --compare

format: ## Format code with black
	@echo "$(BLUE)Formatting code...$(NC)"
	black src/ tests/ main.py
	@echo "$(GREEN)✓ Code formatted!$(NC)"

lint: ## Run linting checks
	@echo "$(BLUE)Running linters...$(NC)"
	flake8 src/ tests/ main.py
	@echo "$(GREEN)✓ Linting passed!$(NC)"

type-check: ## Run type checking with mypy
	@echo "$(BLUE)Type checking...$(NC)"
	mypy src/ tests/ main.py
	@echo "$(GREEN)✓ Type checking passed!$(NC)"

clean: ## Clean build artifacts
	@echo "$(BLUE)Cleaning build artifacts...$(NC)"
	rm -rf build/ dist/ *.egg-info .pytest_cache/
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg" -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)✓ Cleaned!$(NC)"

model: ## Download VGGT model weights
	@echo "$(BLUE)Downloading VGGT model (5GB)...$(NC)"
	$(PYTHON) main.py download
	@echo "$(GREEN)✓ Model downloaded!$(NC)"

run: ## Run 3D reconstruction on images
	@echo "$(BLUE)Running 3D reconstruction...$(NC)"
	$(PYTHON) main.py reconstruct data/*.jpg

run-sparse: ## Run with sparse attention
	@echo "$(BLUE)Running sparse reconstruction...$(NC)"
	$(PYTHON) main.py reconstruct --sparse data/*.jpg

web: ## Launch web interface
	@echo "$(BLUE)Launching Gradio interface...$(NC)"
	$(PYTHON) main.py web

check: lint type-check test ## Run all checks
	@echo "$(GREEN)✓ All checks passed!$(NC)"

venv: ## Create virtual environment with uv
	@echo "$(BLUE)Creating virtual environment...$(NC)"
	$(UV) venv
	@echo "$(GREEN)✓ Virtual environment created!$(NC)"
	@echo "$(YELLOW)Activate with: source .venv/bin/activate$(NC)"

sync: ## Sync dependencies from pyproject.toml
	@echo "$(BLUE)Syncing dependencies...$(NC)"
	$(UV) pip sync pyproject.toml
	@echo "$(GREEN)✓ Dependencies synced!$(NC)"

update-deps: ## Update all dependencies
	@echo "$(BLUE)Updating dependencies...$(NC)"
	$(UV) pip install --upgrade -e ".[all]"
	@echo "$(GREEN)✓ Dependencies updated!$(NC)"

freeze: ## Export current dependencies
	@echo "$(BLUE)Exporting dependencies...$(NC)"
	$(UV) pip freeze > requirements-lock.txt
	@echo "$(GREEN)✓ Exported to requirements-lock.txt$(NC)"

ci: ## Run CI pipeline
	@echo "$(BLUE)Running CI pipeline...$(NC)"
	make clean
	make install
	make check
	@echo "$(GREEN)✓ CI pipeline complete!$(NC)"

# Docker commands (future)
docker-build: ## Build Docker image
	@echo "$(YELLOW)Docker support coming soon...$(NC)"

# Default target
all: clean install test
	@echo "$(GREEN)✓ Build complete!$(NC)"