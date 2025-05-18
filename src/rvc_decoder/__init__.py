"""
rvc_decoder
===========

Library for loading RV-C specs & mappings and decoding CAN payloads.

This package contains the core decoding logic for interpreting RV-C protocol
messages from the CAN bus. It handles parsing binary data according to the
RV-C specification and mapping decoded values to meaningful entities.

Functions:
    - get_bits: Extract bits from binary data
    - decode_payload: Convert raw CAN data into decoded signal values
    - load_config_data: Load RV-C specification and device mapping files
"""

from rvc_decoder.decode import decode_payload, get_bits, load_config_data

__all__ = [
    "get_bits",
    "decode_payload",
    "load_config_data",
]
