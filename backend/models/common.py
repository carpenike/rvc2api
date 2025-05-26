"""
backend.models.common

Shared Pydantic models for use across rvc2api modules.

This module contains base models that are used across different components of the application.
"""

from pydantic import BaseModel


class CoachInfo(BaseModel):
    """
    CoachInfo

    Represents coach/model metadata parsed from the mapping YAML or filename.

    Attributes:
        year (str | None): Model year (e.g., '2021').
        make (str | None): Manufacturer (e.g., 'Entegra').
        model (str | None): Model name (e.g., 'Aspire').
        trim (str | None): Trim level or submodel (e.g., '44R').
        filename (str | None): Mapping filename in use.
        notes (str | None): Additional notes or parsing status.
    """

    year: str | None = None
    make: str | None = None
    model: str | None = None
    trim: str | None = None
    filename: str | None = None
    notes: str | None = None
