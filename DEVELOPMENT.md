# Development Guide

This guide covers the modern development workflow using `uv` and `make`.

## Prerequisites

1. **Install uv** (if not already installed):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

   Or with Homebrew:
   ```bash
   brew install uv
   ```

2. **Python 3.10+** on Apple Silicon Mac

## Quick Start

```bash
# Clone the repository
git clone https://github.com/jmanhype/vggt-mps.git
cd vggt-mps

# Install with uv (10-100x faster than pip!)
make install

# Run tests
make test

# Run demo
make demo
```

## Makefile Commands

Our Makefile provides convenient shortcuts for common tasks:

### Installation
- `make install` - Install project with uv
- `make dev` - Install with development dependencies
- `make web-deps` - Install web interface dependencies
- `make all-deps` - Install all optional dependencies

### Development
- `make test` - Run full test suite
- `make test-mps` - Test MPS support
- `make test-sparse` - Test sparse attention
- `make format` - Format code with black
- `make lint` - Run linting checks
- `make type-check` - Run type checking with mypy
- `make check` - Run all checks (lint + type + test)

### Running
- `make demo` - Run demo with sample images
- `make demo-kitchen` - Run kitchen dataset demo
- `make benchmark` - Run performance benchmarks
- `make benchmark-compare` - Compare sparse vs dense
- `make web` - Launch Gradio web interface
- `make run` - Run 3D reconstruction on images
- `make run-sparse` - Run with sparse attention

### Utilities
- `make model` - Download VGGT model weights (5GB)
- `make clean` - Clean build artifacts
- `make freeze` - Export current dependencies
- `make update-deps` - Update all dependencies
- `make sync` - Sync dependencies from pyproject.toml

### Help
- `make help` - Show all available commands

## Using UV Directly

UV provides ultra-fast Python package management:

```bash
# Create virtual environment
uv venv

# Activate it
source .venv/bin/activate

# Install in editable mode
uv pip install -e .

# Install with extras
uv pip install -e ".[dev,web]"

# Update dependencies
uv pip install --upgrade -e ".[all]"

# Export dependencies
uv pip freeze > requirements-lock.txt
```

## Project Structure

```
vggt-mps/
├── Makefile              # Development commands
├── pyproject.toml        # Modern Python packaging
├── .python-version       # Python version for pyenv
├── main.py              # Single entry point
├── src/                 # Source code
│   ├── commands/        # CLI commands
│   ├── utils/          # Utilities
│   └── tools/          # MCP tools
└── tests/              # Test suite
```

## Development Workflow

1. **Create feature branch**:
   ```bash
   git checkout develop
   git checkout -b feature/your-feature
   ```

2. **Make changes and test**:
   ```bash
   # Make your changes
   vim src/...

   # Format code
   make format

   # Run checks
   make check
   ```

3. **Commit and push**:
   ```bash
   git add .
   git commit -m "feat: Your feature description"
   git push -u origin feature/your-feature
   ```

4. **Create PR to develop branch**

## Testing

We have comprehensive test suites:

```bash
# Run all tests
make test

# Run specific test suites
make test-mps      # MPS functionality
make test-sparse   # Sparse attention

# Run with pytest directly
pytest tests/test_mps.py -v
pytest tests/sparse_attention/ -v
```

## Benchmarking

Compare performance:

```bash
# Basic benchmark
make benchmark

# Compare sparse vs dense
make benchmark-compare

# Custom benchmark
python main.py benchmark --images 100
```

## CI/CD

For continuous integration:

```bash
# Run full CI pipeline
make ci
```

This runs: clean → install → lint → type-check → test

## Troubleshooting

### UV Issues

If uv is not found:
```bash
# Add to PATH
export PATH="$HOME/.cargo/bin:$PATH"

# Or install with pip
pip install uv
```

### Python Version

Ensure you're using Python 3.10+:
```bash
python --version
# Should show: Python 3.10.x or higher
```

### MPS Issues

Test MPS availability:
```bash
make test-mps
```

## Tips

1. **Use UV for Speed**: UV is 10-100x faster than pip
2. **Use Make for Convenience**: Common commands are just `make test`, `make demo`, etc.
3. **Keep Dependencies Updated**: Run `make update-deps` periodically
4. **Format Before Committing**: Always run `make format` before commits
5. **Run Checks**: Use `make check` before pushing

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

## Support

- GitHub Issues: https://github.com/jmanhype/vggt-mps/issues
- Documentation: https://github.com/jmanhype/vggt-mps#readme