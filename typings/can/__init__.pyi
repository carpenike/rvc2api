"""
Type stub file for Python CAN library.

This file provides basic type hints for commonly used Python CAN components.
Only includes essential functionality used in the rvc2api project.
"""

from typing import Any

class Message:
    """CAN Message class."""

    arbitration_id: int
    data: bytes
    is_extended_id: bool

    def __init__(
        self,
        arbitration_id: int,
        data: bytes | list[int],
        is_extended_id: bool = False,
        **kwargs: Any,
    ) -> None: ...

class BusABC:
    """Abstract Base Class for CAN bus implementations."""

    def send(self, message: Message, timeout: float | None = None) -> None: ...
    async def send_periodic(self, message: Message, period: float) -> Any: ...

def interface(interface: str, channel: str, **kwargs: Any) -> BusABC: ...

class CanError(Exception):
    """Base class for all python-can exceptions."""

    pass

class CanOperationError(CanError):
    """Indicates an operational error occurred in python-can."""

    pass

# Exception namespace in the can module
class Exceptions:
    """Namespace for can exceptions."""

    # Use type annotations instead of direct assignments
    CanError: type[CanError]
    CanOperationError: type[CanOperationError]

# Expose exceptions namespace
exceptions = Exceptions()
