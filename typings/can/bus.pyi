"""
Type stub file for Python CAN library bus module.

This file provides type hints for bus classes used in the rvc2api project.
"""

from typing import Any

class BusABC:
    """Abstract Base Class for CAN bus implementations."""

    def send(self, message: Any, timeout: float | None = None) -> None: ...
    async def send_periodic(self, message: Any, period: float) -> Any: ...

class Bus(BusABC):
    """CAN bus implementation."""

    def __init__(
        self,
        channel: str | None = None,
        bustype: str | None = None,
        **kwargs: Any,
    ) -> None: ...
