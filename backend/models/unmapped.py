"""
Unmapped Entry Models

Pydantic models for handling unmapped CAN entries and unknown PGNs.
These models represent CAN messages that couldn't be mapped to configured entities.
"""

from typing import Any

from pydantic import BaseModel, Field


class SuggestedMapping(BaseModel):
    """
    Provides a suggested mapping for an unmapped device instance
    based on existing configurations.
    """

    instance: str
    name: str
    suggested_area: str | None = None


class UnmappedEntryModel(BaseModel):
    """Represents an RV-C message that could not be mapped to a configured entity."""

    pgn_hex: str
    pgn_name: str | None = Field(
        None,
        description=(
            "The human-readable name of the PGN (from arbitration ID), if known from the spec."
        ),
    )
    dgn_hex: str
    dgn_name: str | None = Field(
        None, description="The human-readable name of the DGN, if known from the spec."
    )
    instance: str
    last_data_hex: str
    decoded_signals: dict[str, Any] | None = None
    first_seen_timestamp: float
    last_seen_timestamp: float
    count: int
    suggestions: list[SuggestedMapping] | None = None
    spec_entry: dict[str, Any] | None = Field(
        None,
        description=("The raw rvc.json spec entry used for decoding, if PGN was known."),
    )


class UnknownPGNEntry(BaseModel):
    """Represents a CAN message whose PGN (from arbitration ID) is not in the rvc.json spec."""

    arbitration_id_hex: str
    first_seen_timestamp: float
    last_seen_timestamp: float
    count: int
    last_data_hex: str
