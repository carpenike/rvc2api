"""
Backend package for CoachIQ.

This package contains the FastAPI application, API routers, business logic services,
and integration components for the CoachIQ system.
"""

# Import the registration module to ensure feature factories are registered
from backend.integrations import registration

# Explicitly reference the import to satisfy type checker
_ = registration

__version__ = "0.1.0"
