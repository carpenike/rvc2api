"""
Core package for rvc2api.

This package contains core application components like configuration, state management,
events system, and application initialization.
"""

# Import core components to make them available via the package
from backend.core.state import app_state, initialize_app_state  # noqa: F401
from backend.core.state_setup import setup_app_state  # noqa: F401
