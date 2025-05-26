"""
RV-C protocol integration.

This package contains components for decoding and encoding RV-C protocol messages.
It provides the core functionality for interpreting RV-C protocol messages from
the CAN bus, handling the parsing of binary data according to the RV-C specification,
and mapping decoded values to meaningful entities.

Functions:
    - get_bits: Extract bits from binary data
    - decode_payload: Convert raw CAN data into decoded signal values
    - load_config_data: Load RV-C specification and device mapping files
"""

from backend.integrations.rvc.decode import (
    decode_payload,
    get_bits,
    load_config_data,
)

__all__ = ["decode_payload", "get_bits", "load_config_data"]
