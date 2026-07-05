"""Pytest configuration — sys.path setup and marker registration."""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def pytest_configure(config):
    """Register custom pytest markers."""
    config.addinivalue_line(
        "markers",
        "real: real integration test — no mock on the primary external dependency",
    )
