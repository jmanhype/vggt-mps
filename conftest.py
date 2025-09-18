"""
Global pytest configuration for vggt project

This ensures proper module discovery and path setup for all tests.
"""

import sys
from pathlib import Path
import matplotlib
import matplotlib.pyplot as plt
import pytest

def pytest_configure(config):
    """Configure pytest to add the project root to sys.path."""
    # Get the project root directory (where this conftest.py is located)
    project_root = Path(__file__).parent.resolve()

    # Add to sys.path if not already there
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

@pytest.fixture(autouse=True)
def no_plot_show(monkeypatch):
    """Disable plt.show() during tests so figures don't block."""
    matplotlib.use("Agg")  # non-interactive backend
    monkeypatch.setattr(plt, "show", lambda: None)