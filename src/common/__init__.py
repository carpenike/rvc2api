"""
common

This package contains shared models and utilities used across the rvc2api project.

Modules:
    - models: Defines shared Pydantic models used by multiple components
"""

from common.models import CoachInfo, UserCoachInfo

__all__ = ["CoachInfo", "UserCoachInfo"]
