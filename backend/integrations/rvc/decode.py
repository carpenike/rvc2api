"""
backend.integrations.rvc.decode

Core decoding logic for RV-C CAN frames, including loading of spec and device mapping data.

Functions:
    - get_bits: Extracts a little-endian bitfield from a CAN payload
    - decode_payload: Decodes all signals in a spec entry
    - load_config_data: Loads and parses RVC spec and device mapping,
    returning all lookup tables and coach metadata

Notes:
    - CoachInfo includes year, make, model, trim, filename, and notes fields.
    - Mapping/model selection logic supports model-specific mapping files and full-path overrides.
"""

import json
import logging
import os
import pathlib

import yaml

from backend.core.config import get_rvc_settings
from backend.models.common import CoachInfo

logger = logging.getLogger(__name__)  # Added named logger


# Global storage for missing DGNs - can be accessed for monitoring and debugging
_missing_dgns_storage: dict[int, dict] = {}


def get_missing_dgns() -> dict[int, dict]:
    """
    Get the current storage of missing DGNs that were encountered during decoding.

    Returns:
        Dictionary mapping DGN IDs to metadata about when/how they were encountered
    """
    return _missing_dgns_storage.copy()


def clear_missing_dgns() -> None:
    """Clear the missing DGNs storage."""
    global _missing_dgns_storage
    _missing_dgns_storage.clear()


def record_missing_dgn(dgn_id: int, can_id: int | None = None, context: str | None = None) -> None:
    """
    Record a missing DGN for future processing.

    Args:
        dgn_id: The DGN ID that was not found in the specification
        can_id: Optional CAN ID where this DGN was encountered
        context: Optional context string describing where/how this was encountered
    """
    if dgn_id not in _missing_dgns_storage:
        _missing_dgns_storage[dgn_id] = {
            "dgn_id": dgn_id,
            "dgn_hex": f"{dgn_id:X}",
            "first_seen": None,
            "encounter_count": 0,
            "can_ids": set(),
            "contexts": set(),
        }

    entry = _missing_dgns_storage[dgn_id]
    entry["encounter_count"] += 1

    if can_id is not None:
        entry["can_ids"].add(can_id)

    if context:
        entry["contexts"].add(context)

    # Set first seen timestamp if not already set
    if entry["first_seen"] is None:
        import time

        entry["first_seen"] = time.time()

    logger.debug(f"Missing DGN recorded: {dgn_id:X} (count: {entry['encounter_count']})")


def _default_paths():
    """
    Determine default paths for the rvc spec and device mapping files using the centralized config service.

    Returns a tuple of (rvc_spec_path, device_mapping_path) where device_mapping_path
    is selected based on configuration or falls back to default.
    """
    try:
        rvc_settings = get_rvc_settings()

        # Get paths from the config service - let it handle all fallback logic
        spec_path = rvc_settings.get_spec_path()
        coach_mapping_path = rvc_settings.get_coach_mapping_path()

        # Validate that the files exist
        if not spec_path.exists():
            raise FileNotFoundError(f"RVC spec file not found: {spec_path}")

        if not coach_mapping_path.exists():
            raise FileNotFoundError(f"Coach mapping file not found: {coach_mapping_path}")

        logger.debug(f"Using RVC config files - spec: {spec_path}, mapping: {coach_mapping_path}")
        return (str(spec_path), str(coach_mapping_path))

    except Exception as e:
        logger.error(f"Failed to get RVC config paths: {e}")
        raise


def _select_coach_mapping_file(config_dir) -> pathlib.Path:
    """
    Select the appropriate coach mapping file based on environment variables.

    Priority:
    1. RVC_COACH_MODEL environment variable (e.g., "2021_Entegra_Aspire_44R")
    2. Default fallback: "coach_mapping.default.yml"

    Args:
        config_dir: Path to the config directory containing mapping files

    Returns:
        Path to the selected coach mapping file
    """
    import pathlib

    config_dir = pathlib.Path(config_dir)

    # Check for model selector environment variable
    model_selector = os.getenv("RVC_COACH_MODEL")
    if model_selector:
        # Normalize selector: replace spaces with underscores, lowercase, strip extension if present
        selector_norm = os.path.splitext(model_selector.replace(" ", "_").lower())[0]

        try:
            # Find available mapping files
            available_mappings = [
                fname
                for fname in os.listdir(config_dir)
                if os.path.splitext(fname)[1].lower() in (".yml", ".yaml")
            ]

            # Search for matching file
            for fname in available_mappings:
                base, ext = os.path.splitext(fname)
                base_norm = base.replace(" ", "_").lower()

                if base_norm == selector_norm:
                    candidate = config_dir / fname
                    if candidate.is_file():
                        logger.info(
                            f"Model selector '{model_selector}' -> Using mapping file: {candidate}"
                        )
                        return candidate

            # Model selector specified but file not found
            logger.warning(f"Requested model mapping '{model_selector}' not found in {config_dir}.")
            logger.warning(f"Available mapping files: {available_mappings}")
            logger.warning("Falling back to default mapping")

        except Exception as e:
            logger.warning(f"Could not scan mapping directory '{config_dir}': {e}")

    # Fallback to default mapping
    default_mapping = config_dir / "coach_mapping.default.yml"
    if default_mapping.is_file():
        logger.debug(f"Using default coach mapping: {default_mapping}")
        return default_mapping

    # Last resort - raise error if default is not found
    raise FileNotFoundError(f"Default coach mapping file not found: {default_mapping}")


def get_bits(data_bytes: bytes, start_bit: int, length: int) -> int:
    """
    Extract a little-endian bitfield from an 8-byte CAN payload.
    """
    raw_int = int.from_bytes(data_bytes, byteorder="little")
    mask = (1 << length) - 1
    return (raw_int >> start_bit) & mask


def decode_payload(entry: dict, data_bytes: bytes) -> tuple[dict[str, str], dict[str, int]]:
    """
    Decode all 'signals' in a spec entry:
      - raw_values: the integer bitfields
      - decoded: human-readable strings (with scale/offset/enum logic)

    Returns:
      tuple(decoded: dict[str,str], raw_values: dict[str,int])
    """
    decoded = {}
    raw_values = {}

    for sig in entry.get("signals", []):
        raw = get_bits(data_bytes, sig["start_bit"], sig["length"])
        raw_values[sig["name"]] = raw

        # apply scale/offset
        val = raw * sig.get("scale", 1) + sig.get("offset", 0)
        unit = sig.get("unit", "")

        # enum lookup if present
        if "enum" in sig:
            formatted = sig["enum"].get(str(raw))
            if formatted is None:
                formatted = f"UNKNOWN ({raw})"
        elif sig.get("scale", 1) != 1 or sig.get("offset", 0) != 0 or isinstance(val, float):
            formatted = f"{val:.2f}{unit}"
        else:
            formatted = f"{int(val)}{unit}"

        decoded[sig["name"]] = formatted

    return decoded, raw_values


def decode_payload_safe(
    dgn_dict: dict[int, dict], dgn_id: int, data_bytes: bytes
) -> tuple[dict[str, str], dict[str, int], bool]:
    """
    Safely decode a payload, handling missing DGNs gracefully.

    Args:
        dgn_dict: Dictionary mapping DGNs to specification entries
        dgn_id: The DGN ID to decode
        data_bytes: The CAN payload bytes

    Returns:
        tuple containing:
            - decoded: Dictionary of decoded signal values (empty if DGN missing)
            - raw_values: Dictionary of raw signal values (empty if DGN missing)
            - success: Boolean indicating if decoding was successful
    """
    if dgn_id not in dgn_dict:
        record_missing_dgn(dgn_id, context="decode_payload_safe")
        logger.warning(f"DGN {dgn_id:X} not found in specification - storing for future processing")
        return {}, {}, False

    try:
        entry = dgn_dict[dgn_id]
        decoded, raw_values = decode_payload(entry, data_bytes)
        return decoded, raw_values, True
    except Exception as e:
        logger.error(f"Error decoding DGN {dgn_id:X}: {e}")
        record_missing_dgn(dgn_id, context=f"decode_error: {e!s}")
        return {}, {}, False


def load_config_data(
    rvc_spec_path_override: str | None = None,
    device_mapping_path_override: str | None = None,
) -> tuple[
    dict[int, dict],  # dgn_dict
    dict,  # spec_meta
    dict[tuple[str, str], dict],  # mapping_dict
    dict[tuple[str, str], dict],  # entity_map
    set[str],  # entity_ids
    dict[str, dict],  # inst_map
    dict[str, dict],  # unique_instances
    dict[str, str],  # pgn_hex_to_name_map
    dict,  # dgn_pairs
    CoachInfo,  # coach_info
]:
    """
    Load and parse RVC spec and device mapping data.

    Args:
        rvc_spec_path_override: Optional path override for RVC spec JSON
        device_mapping_path_override: Optional path override for device mapping YAML

    Returns:
        tuple containing:
            - dgn_dict: Dictionary mapping DGNs to specification entries
            - spec_meta: Metadata from the RVC spec
            - mapping_dict: Dictionary mapping (DGN, instance) pairs to device entries
            - entity_map: Dictionary mapping entity IDs to device entries
            - entity_ids: Set of all entity IDs for validation
            - inst_map: Dictionary mapping entity IDs to (dgn_hex, instance) pairs
            - unique_instances: Dictionary of DGN instances with only one device
            - pgn_hex_to_name_map: Dictionary mapping DGN hex strings to PGN names
            - dgn_pairs: Dictionary mapping DGNs to useful metadata for faster lookups
            - coach_info: CoachInfo object with detected coach metadata
    """
    # Get default paths if not overridden
    rvc_spec_path, device_mapping_path = _default_paths()
    if rvc_spec_path_override:
        rvc_spec_path = rvc_spec_path_override
    if device_mapping_path_override:
        device_mapping_path = device_mapping_path_override

    # Load RVC spec
    try:
        logger.info(f"Loading RVC spec from: {rvc_spec_path}")
        with open(rvc_spec_path, encoding="utf-8") as f:
            rvc_spec = json.load(f)
    except FileNotFoundError:
        logger.error(f"RVC spec file not found: {rvc_spec_path}")
        raise
    except Exception as e:
        logger.error(f"Failed to load RVC spec: {e}")
        raise

    # Load device mapping
    try:
        logger.info(f"Loading device mapping from: {device_mapping_path}")
        with open(device_mapping_path, encoding="utf-8") as f:
            device_mapping = yaml.safe_load(f)
    except FileNotFoundError:
        logger.error(f"Device mapping file not found: {device_mapping_path}")
        raise
    except Exception as e:
        logger.error(f"Failed to load device mapping: {e}")
        raise

    # Process DGN dictionary
    dgn_dict = {}
    pgn_hex_to_name_map = {}
    rvc_spec_dgn_pairs = {}

    for pgn_name, pgn_entry in rvc_spec["pgns"].items():
        pgn = int(pgn_entry["pgn"], 16)
        priority = int(pgn_entry.get("priority", "6"), 16)
        dgn = (priority << 18) | pgn
        dgn_dict[dgn] = pgn_entry
        pgn_hex_to_name_map[pgn_entry["pgn"]] = pgn_name
        rvc_spec_dgn_pairs[pgn_entry["pgn"]] = {
            "dgn": dgn,
            "name": pgn_name,
        }

    # Extract dgn_pairs from device mapping (command PGN -> status PGN mapping)
    dgn_pairs = device_mapping.get("dgn_pairs", {})

    # Extract spec metadata
    spec_meta = {
        "version": rvc_spec.get("version", "unknown"),
        "source": rvc_spec.get("source", "unknown"),
        "rvc_verison": rvc_spec.get("rvc_version", "unknown"),
    }

    # Extract coach info from mapping file
    coach_info = _extract_coach_info(device_mapping, device_mapping_path)

    # Process mapping dictionary
    mapping_dict = {}
    entity_map = {}
    entity_ids = set()
    inst_map = {}
    unique_instances = {}

    for dgn_hex, instance_dict in device_mapping.items():
        if dgn_hex.startswith("#") or dgn_hex.startswith("_"):
            # Skip comment lines
            continue

        # Skip metadata sections
        if dgn_hex in (
            "coach_info",
            "dgn_pairs",
            "templates",
            "global_defaults",
            "areas",
            "lighting_scenes",
            "lighting_groups",
            "validation_rules",
            "file_metadata",
            "can_interface_mapping",
        ):
            continue

        for instance_id, devices in instance_dict.items():
            if not isinstance(devices, list):
                continue  # Skip non-list entries

            mapping_dict[(dgn_hex, str(instance_id))] = devices

            if len(devices) == 1:
                # Only store uniquely identifiable instances
                unique_instances.setdefault(dgn_hex, {})[str(instance_id)] = devices[0]

            for device in devices:
                entity_id = device.get("entity_id")
                if entity_id:
                    entity_ids.add(entity_id)
                    entity_map[(dgn_hex, instance_id)] = device
                    inst_map[entity_id] = {
                        "dgn_hex": dgn_hex,
                        "instance": instance_id,
                    }

    return (
        dgn_dict,
        spec_meta,
        mapping_dict,
        entity_map,
        entity_ids,
        inst_map,
        unique_instances,
        pgn_hex_to_name_map,
        dgn_pairs,
        coach_info,
    )


def _extract_coach_info(device_mapping: dict, mapping_path: str) -> CoachInfo:
    """
    Extract coach information from the mapping file.

    This extracts coach metadata from either:
    1. The "_coach_info" section in the mapping file, or
    2. The filename itself (looking for year_make_model_trim pattern)

    Args:
        device_mapping: The loaded mapping dictionary
        mapping_path: The path to the mapping file

    Returns:
        CoachInfo object with detected coach metadata
    """
    coach_info = CoachInfo(filename=os.path.basename(mapping_path))

    # Try to get metadata from the mapping file first
    if "_coach_info" in device_mapping:
        info = device_mapping["_coach_info"]
        if isinstance(info, dict):
            for field in ["year", "make", "model", "trim", "notes"]:
                if field in info:
                    setattr(coach_info, field, str(info[field]))
            return coach_info

    # Try to parse from filename if no explicit metadata
    basename = os.path.basename(mapping_path)
    if basename.endswith(".yml") or basename.endswith(".yaml"):
        basename = basename[:-4] if basename.endswith(".yml") else basename[:-5]

    # Look for pattern like "2021_Entegra_Aspire_44R.yml"
    parts = basename.split("_")
    # Check if we have enough parts and first part is a year (4 digits)
    if len(parts) >= 4 and parts[0].isdigit() and len(parts[0]) == 4:
        coach_info.year = parts[0]
        coach_info.make = parts[1]
        coach_info.model = parts[2]
        coach_info.trim = "_".join(parts[3:])  # Join remaining parts as trim

    return coach_info
