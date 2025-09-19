# VGGT-MPS Makefile
# Modern development workflow with uv

.PHONY: help install dev test demo benchmark format lint clean clean-runtime clean-models distclean model run web check all

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

# Python executable
PYTHON := python
UV := uv

RUNTIME_DIRS := logs outputs tmp data
MODEL_FILES := models/vggt_model.pt repo/vggt/vggt_model.pt

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
	rm -rf build/ dist/ *.egg-info .pytest_cache/ .benchmarks/
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg" -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)✓ Cleaned!$(NC)"

clean-runtime: ## Remove runtime directories (logs/, outputs/, tmp/, data/)
	@echo "$(BLUE)Cleaning runtime directories...$(NC)"
	@for dir in $(RUNTIME_DIRS); do \
		if [ -d "$$dir" ]; then \
			echo "  • removing $$dir"; \
			rm -rf "$$dir"; \
		fi; \
	done
	@echo "$(GREEN)✓ Runtime directories removed!$(NC)"

clean-models: ## Remove downloaded models and caches
	@echo "$(BLUE)Removing downloaded models...$(NC)"
	@for target in $(MODEL_FILES); do \
		if [ -e "$$target" ]; then \
			echo "  • deleting $$target"; \
			rm -rf "$$target"; \
		fi; \
	done
	@echo "$(GREEN)✓ Model artifacts removed!$(NC)"

distclean: clean clean-runtime clean-models ## Remove all build artifacts, runtime data, and models
	@echo "$(GREEN)✓ Workspace completely cleaned!$(NC)"

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

# PyPI Publishing Commands
build: clean ## Build distribution packages
	@echo "$(BLUE)Building distribution packages...$(NC)"
	$(PYTHON) -m pip install --upgrade build
	$(PYTHON) -m build
	@echo "$(GREEN)✓ Build complete! Check dist/ directory$(NC)"

test-upload: build ## Upload to TestPyPI
	@echo "$(BLUE)Uploading to TestPyPI...$(NC)"
	$(PYTHON) -m pip install --upgrade twine
	$(PYTHON) -m twine upload --repository testpypi dist/*
	@echo "$(GREEN)✓ Uploaded to TestPyPI!$(NC)"
	@echo "$(YELLOW)Test install with: pip install -i https://test.pypi.org/simple/ vggt-mps$(NC)"

upload: build ## Upload to PyPI (production)
	@echo "$(RED)⚠️  Production PyPI Upload$(NC)"
	@echo "$(YELLOW)Are you sure? This will upload to production PyPI. Press Ctrl-C to cancel.$(NC)"
	@read -p "Press Enter to continue..." dummy
	$(PYTHON) -m pip install --upgrade twine
	$(PYTHON) -m twine upload dist/*
	@echo "$(GREEN)✓ Uploaded to PyPI!$(NC)"
	@echo "$(YELLOW)Install with: pip install vggt-mps$(NC)"

check-dist: build ## Check distribution package
	@echo "$(BLUE)Checking distribution...$(NC)"
	$(PYTHON) -m twine check dist/*
	@echo "$(GREEN)✓ Distribution check passed!$(NC)"

release: ## Create a new release (requires VERSION parameter)
	@if [ -z "$(VERSION)" ]; then \
		echo "$(RED)ERROR: Please specify VERSION=x.y.z$(NC)"; \
		echo "$(YELLOW)Usage: make release VERSION=2.0.1$(NC)"; \
		exit 1; \
	fi
	@echo "$(BLUE)Creating release $(VERSION)...$(NC)"
	@echo "$(YELLOW)This will:$(NC)"
	@echo "  1. Update version in pyproject.toml"
	@echo "  2. Create git tag"
	@echo "  3. Build and upload to PyPI"
	@read -p "Continue? (y/n) " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		sed -i.bak 's/version = "[0-9]*\.[0-9]*\.[0-9]*"/version = "$(VERSION)"/' pyproject.toml && rm pyproject.toml.bak; \
		git add pyproject.toml; \
		git commit -m "chore: bump version to $(VERSION)"; \
		git tag -a v$(VERSION) -m "Release version $(VERSION)"; \
		make upload; \
		echo "$(GREEN)✓ Release $(VERSION) complete!$(NC)"; \
		echo "$(YELLOW)Don't forget to: git push origin main --tags$(NC)"; \
	fi

# Docker commands (future)
docker-build: ## Build Docker image
	@echo "$(YELLOW)Docker support coming soon...$(NC)"

# Default target
all: clean install test
	@echo "$(GREEN)✓ Build complete!$(NC)"
