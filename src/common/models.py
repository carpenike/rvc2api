"""
common.models

Shared Pydantic models for use across rvc2api modules.

CoachInfo:
    Represents coach/model metadata parsed from the mapping YAML or filename, including year, make,
    model, trim, filename, and notes.

UserCoachInfo:
    Represents user-supplied coach information (VIN, serial numbers, owner, etc),
    with common fields and support for arbitrary extra fields.
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


class UserCoachInfo(BaseModel):
    """
    UserCoachInfo

    Represents user-supplied coach information (VIN, serial numbers, owner, etc).
    Common fields are optional; arbitrary extra fields are allowed.

    Attributes:
        vin (str | None): Vehicle Identification Number (optional).
        chassis_serial_number (str | None): Chassis serial number (optional).
        owner (str | None): Owner name (optional).
        custom_notes (str | None): Freeform notes (optional).
        ...any other user-supplied fields are accepted as extra keys.
    """

    vin: str | None = None
    chassis_serial_number: str | None = None
    owner: str | None = None
    custom_notes: str | None = None

    class Config:
        extra = "allow"
