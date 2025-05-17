"""
Defines Pydantic models for API request/response validation and serialization.

These models are used throughout the FastAPI application to ensure data consistency
and provide clear API documentation for request bodies and response payloads.

Models:
    - Entity: State and metadata of a monitored RV-C entity
    - ControlCommand: Structure for sending control commands to an entity
    - SuggestedMapping: Suggested mapping for an unmapped device instance
    - UnmappedEntryModel: RV-C message not mapped to a configured entity
    - UnknownPGNEntry: CAN message with unknown PGN
    - BulkLightControlResponse: Response for bulk light control operations
    - ControlEntityResponse: Response for individual entity control commands
    - CANInterfaceStats: Statistics for a CAN interface
    - AllCANStats: Statistics for all CAN interfaces
    - GitHubReleaseAsset: Downloadable asset attached to a GitHub release
    - GitHubReleaseInfo: Metadata about a GitHub release
    - GitHubUpdateStatus: Status and metadata of the latest GitHub release
    - CoachInfo: (re-exported from common.models)
"""

from typing import Any

from pydantic import BaseModel, Field


# ── Pydantic Models for API responses ────────────────────────────────────────
class Entity(BaseModel):
    """Represents the state and metadata of a monitored RV-C entity."""

    entity_id: str
    value: dict[str, str]
    raw: dict[str, int]
    state: str
    timestamp: float
    suggested_area: str | None = "Unknown"
    device_type: str | None = "unknown"
    capabilities: list[str] | None = []
    friendly_name: str | None = None
    groups: list[str] | None = Field(default_factory=list)


class ControlCommand(BaseModel):
    """Defines the structure for sending control commands to an entity, typically a light."""

    command: str
    state: str | None = Field(
        None, description="Target state: 'on' or 'off'. Required only for 'set' command."
    )
    brightness: int | None = Field(
        None,
        ge=0,
        le=100,
        description=(
            "Brightness percent (0-100). Only used when command is 'set' and state is 'on'."
        ),
    )


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


class BulkLightControlResponse(BaseModel):
    """Response model for bulk light control operations, summarizing the outcome."""

    status: str
    message: str  # Added message field
    action: str
    group: str | None = None  # Added group field
    lights_processed: int
    lights_commanded: int
    errors: list[dict[str, str]] = Field(default_factory=list)  # Changed type from List[str]
    details: list[dict[str, Any]] = Field(default_factory=list)  # Added details field


class ControlEntityResponse(BaseModel):
    """Response model for individual entity control commands, confirming the action taken."""

    status: str
    entity_id: str
    command: str
    state: str
    brightness: int
    action: str


class CANInterfaceStats(BaseModel):
    """Statistics for a CAN interface."""

    name: str
    state: str | None = None
    restart_ms: int | None = None
    bitrate: int | None = None
    sample_point: float | None = None
    tq: int | None = None  # Time quantum in nanoseconds
    prop_seg: int | None = None
    phase_seg1: int | None = None
    phase_seg2: int | None = None
    sjw: int | None = None  # Synchronization Jump Width
    brp: int | None = None  # Bitrate Prescaler
    # Shortened line:
    clock_freq: int | None = Field(default=None, alias="clock")  # Clock frequency Hz
    notes: str | None = None  # Additional notes or platform-specific information

    # From ip -s link show
    tx_packets: int | None = None
    rx_packets: int | None = None
    tx_bytes: int | None = None
    rx_bytes: int | None = None
    tx_errors: int | None = None
    rx_errors: int | None = None
    bus_errors: int | None = None  # General bus errors
    restarts: int | None = None  # Controller restarts

    # Additional details from ip -details link show
    link_type: str | None = Field(default=None, alias="link/can")
    promiscuity: int | None = None
    allmulti: int | None = None
    minmtu: int | None = None
    maxmtu: int | None = None
    parentbus: str | None = None
    parentdev: str | None = None

    # Specific error counters if available (these might vary by controller)
    error_warning: int | None = None  # Entered error warning state count
    error_passive: int | None = None  # Entered error passive state count
    bus_off: int | None = None  # Entered bus off state count

    # Raw details string for any unparsed info, if needed for debugging
    raw_details: str | None = None


class AllCANStats(BaseModel):
    """Statistics for all CAN interfaces."""

    interfaces: dict[str, CANInterfaceStats]


class GitHubReleaseAsset(BaseModel):
    """Represents a downloadable asset attached to a GitHub release."""

    name: str
    browser_download_url: str
    size: int | None = None
    download_count: int | None = None


class GitHubReleaseInfo(BaseModel):
    """Represents metadata about a GitHub release for update checking."""

    tag_name: str | None = None
    name: str | None = None
    body: str | None = None
    html_url: str | None = None
    published_at: str | None = None
    created_at: str | None = None
    assets: list[GitHubReleaseAsset] | None = None
    tarball_url: str | None = None
    zipball_url: str | None = None
    prerelease: bool | None = None
    draft: bool | None = None
    author: dict | None = None  # login, html_url
    discussion_url: str | None = None


class GitHubUpdateStatus(BaseModel):
    """Represents the status and metadata of the latest GitHub release as cached by the server."""

    latest_version: str | None = None
    last_checked: float | None = None
    last_success: float | None = None
    error: str | None = None
    latest_release_info: GitHubReleaseInfo | None = None
    repo: str | None = None
    api_url: str | None = None


# CoachInfo model has been moved to src/common/models.py
# Remove the class definition here.
