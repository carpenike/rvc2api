"""
Core decoding logic for RV-C CAN frames.

This module handles the low-level bit extraction and signal decoding
for RV-C messages based on the specification.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class DecodingError(Exception):
    """Raised when decoding fails."""

    pass


def get_bits(data_bytes: bytes, start_bit: int, length: int) -> int:
    """
    Extract a little-endian bitfield from a CAN payload.

    Args:
        data_bytes: The CAN data bytes (typically 8 bytes)
        start_bit: The starting bit position (0-based)
        length: The number of bits to extract

    Returns:
        The extracted integer value

    Raises:
        DecodingError: If the bit range is invalid
    """
    # Validate inputs
    if not data_bytes:
        raise DecodingError("Empty data bytes")

    total_bits = len(data_bytes) * 8

    if start_bit < 0:
        raise DecodingError(f"Invalid start_bit: {start_bit} (must be >= 0)")

    if length <= 0:
        raise DecodingError(f"Invalid length: {length} (must be > 0)")

    if start_bit + length > total_bits:
        raise DecodingError(
            f"Bit range {start_bit}:{start_bit + length} exceeds data size "
            f"({total_bits} bits available)"
        )

    # For very long fields (> 64 bits), we need special handling
    if length > 64:
        logger.warning(
            f"Extracting field longer than 64 bits ({length} bits) - results may be truncated"
        )

    # Convert to integer using little-endian byte order
    raw_int = int.from_bytes(data_bytes, byteorder="little")

    # Extract the bits
    mask = (1 << length) - 1
    return (raw_int >> start_bit) & mask


def decode_signal(signal: dict[str, Any], data_bytes: bytes) -> tuple[Any, int]:
    """
    Decode a single signal from CAN data.

    Args:
        signal: Signal definition from the RVC spec
        data_bytes: The CAN data bytes

    Returns:
        Tuple of (decoded_value, raw_value)

    Raises:
        DecodingError: If decoding fails
    """
    try:
        # Extract raw bits
        start_bit = signal.get("start_bit", 0)
        length = signal.get("length", 8)
        raw_value = get_bits(data_bytes, start_bit, length)

        # Apply scale and offset
        scale = signal.get("scale", 1)
        offset = signal.get("offset", 0)

        # Calculate physical value
        physical_value = raw_value * scale + offset

        # Handle enumerated values
        if "enum" in signal:
            enum_map = signal["enum"]
            # Try to find the enumerated string
            enum_str = enum_map.get(str(raw_value))
            if enum_str is not None:
                return enum_str, raw_value
            else:
                # Return unknown enum value
                return f"UNKNOWN ({raw_value})", raw_value

        # Format based on data type
        unit = signal.get("unit", "")

        # Check if this should be an integer or float
        if scale != 1 or offset != 0 or isinstance(physical_value, float):
            # Format as float with appropriate precision
            if abs(physical_value) < 0.01 and physical_value != 0:
                # Very small numbers - use scientific notation
                formatted = f"{physical_value:.2e}{unit}"
            else:
                # Normal range - use fixed decimal
                formatted = f"{physical_value:.2f}{unit}"
        else:
            # Integer value
            formatted = f"{int(physical_value)}{unit}"

        return formatted, raw_value

    except Exception as e:
        raise DecodingError(
            f"Failed to decode signal '{signal.get('name', 'unknown')}': {e}"
        ) from e


def decode_payload(
    entry: dict[str, Any], data_bytes: bytes
) -> tuple[dict[str, str], dict[str, int]]:
    """
    Decode all signals in a spec entry.

    Args:
        entry: The PGN entry from the RVC spec containing signal definitions
        data_bytes: The CAN data bytes to decode

    Returns:
        Tuple of:
            - decoded: Dictionary of signal names to human-readable strings
            - raw_values: Dictionary of signal names to raw integer values

    Raises:
        DecodingError: If decoding fails
    """
    decoded = {}
    raw_values = {}

    signals = entry.get("signals", [])
    if not signals:
        logger.warning(f"No signals defined for PGN {entry.get('pgn', 'unknown')}")
        return decoded, raw_values

    for signal in signals:
        signal_name = signal.get("name", "unknown")

        try:
            decoded_value, raw_value = decode_signal(signal, data_bytes)
            decoded[signal_name] = decoded_value
            raw_values[signal_name] = raw_value

        except DecodingError as e:
            logger.error(f"Failed to decode signal '{signal_name}': {e}")
            # Continue with other signals
            decoded[signal_name] = "ERROR"
            raw_values[signal_name] = 0
        except Exception as e:
            logger.error(f"Unexpected error decoding signal '{signal_name}': {e}")
            decoded[signal_name] = "ERROR"
            raw_values[signal_name] = 0

    return decoded, raw_values


def decode_string_payload(data_bytes: bytes, encoding: str = "utf-8") -> str:
    """
    Decode a string payload from multi-packet messages.

    This is used for PGNs like Product Identification (1FEF2) that contain
    string fields rather than bit-packed data.

    Args:
        data_bytes: The reassembled payload bytes
        encoding: String encoding to use (default: utf-8)

    Returns:
        The decoded string, with null bytes and padding removed
    """
    try:
        # Remove null bytes and padding
        data = data_bytes.rstrip(b"\x00\xff")

        # Decode to string
        text = data.decode(encoding, errors="replace")

        # Clean up any remaining non-printable characters
        text = "".join(char for char in text if char.isprintable() or char.isspace())

        return text.strip()

    except Exception as e:
        logger.error(f"Failed to decode string payload: {e}")
        return f"<decode error: {e}>"


def decode_product_id(data_bytes: bytes) -> dict[str, str]:
    """
    Decode a Product Identification message (PGN 1FEF2).

    This message contains:
    - Bytes 0-1: Make (manufacturer) code
    - Bytes 2-16: Model string (null-terminated)
    - Bytes 17-31: Serial number string (null-terminated)
    - Bytes 32-36: Unit number string (null-terminated)

    Args:
        data_bytes: The complete reassembled message payload

    Returns:
        Dictionary with decoded fields
    """
    try:
        result = {}

        # Make code (2 bytes, little-endian)
        if len(data_bytes) >= 2:
            make_code = int.from_bytes(data_bytes[0:2], "little")
            result["make_code"] = str(make_code)

        # Model string (15 bytes max)
        if len(data_bytes) >= 17:
            model = decode_string_payload(data_bytes[2:17])
            result["model"] = model

        # Serial number string (15 bytes max)
        if len(data_bytes) >= 32:
            serial = decode_string_payload(data_bytes[17:32])
            result["serial_number"] = serial

        # Unit number string (5 bytes max)
        if len(data_bytes) >= 37:
            unit = decode_string_payload(data_bytes[32:37])
            result["unit_number"] = unit

        return result

    except Exception as e:
        logger.error(f"Failed to decode product ID: {e}")
        return {"error": str(e)}
