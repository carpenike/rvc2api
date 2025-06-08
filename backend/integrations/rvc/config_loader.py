"""
Configuration loader for RV-C spec and device mapping files.

This module handles loading and parsing of RVC specification JSON files
and device mapping YAML files, with support for environment variable overrides
and model-specific mapping selection.
"""

import json
import logging
import os
import pathlib
from typing import Any

import yaml

from backend.core.config import get_rvc_settings
from backend.models.common import CoachInfo

logger = logging.getLogger(__name__)


class ConfigValidationError(Exception):
    """Raised when configuration validation fails."""

    pass


def validate_spec_entry(entry: dict[str, Any], pgn_name: str) -> None:
    """
    Validate a single PGN entry from the RVC spec.

    Args:
        entry: The PGN entry dictionary
        pgn_name: The name of the PGN for error reporting

    Raises:
        ConfigValidationError: If validation fails
    """
    required_keys = ["pgn", "signals"]
    for key in required_keys:
        if key not in entry:
            raise ConfigValidationError(
                f"Invalid PGN entry '{pgn_name}': missing required field '{key}'"
            )

    # Validate signals
    if not isinstance(entry["signals"], list):
        raise ConfigValidationError(f"Invalid PGN entry '{pgn_name}': 'signals' must be a list")

    for i, signal in enumerate(entry["signals"]):
        if not isinstance(signal, dict):
            raise ConfigValidationError(
                f"Invalid signal {i} in PGN '{pgn_name}': signal must be a dictionary"
            )

        signal_required = ["name", "start_bit", "length"]
        for key in signal_required:
            if key not in signal:
                raise ConfigValidationError(
                    f"Invalid signal '{signal.get('name', i)}' in PGN '{pgn_name}': "
                    f"missing required field '{key}'"
                )


def load_rvc_spec(spec_path: str) -> dict[str, Any]:
    """
    Load and validate the RVC specification JSON file.

    Args:
        spec_path: Path to the RVC spec JSON file

    Returns:
        The loaded and validated RVC specification

    Raises:
        FileNotFoundError: If the spec file doesn't exist
        ConfigValidationError: If validation fails
    """
    try:
        logger.info(f"Loading RVC spec from: {spec_path}")
        with open(spec_path, encoding="utf-8") as f:
            rvc_spec = json.load(f)
    except FileNotFoundError:
        logger.error(f"RVC spec file not found: {spec_path}")
        raise
    except json.JSONDecodeError as e:
        raise ConfigValidationError(f"Invalid JSON in RVC spec file: {e}") from e
    except Exception as e:
        logger.error(f"Failed to load RVC spec: {e}")
        raise ConfigValidationError(f"Failed to load RVC spec: {e}") from e

    # Validate the spec structure
    if "pgns" not in rvc_spec:
        raise ConfigValidationError("RVC spec missing required 'pgns' field")

    if not isinstance(rvc_spec["pgns"], dict):
        raise ConfigValidationError("RVC spec 'pgns' field must be a dictionary")

    # Validate each PGN entry
    for pgn_name, pgn_entry in rvc_spec["pgns"].items():
        try:
            validate_spec_entry(pgn_entry, pgn_name)
        except ConfigValidationError as e:
            logger.warning(f"Skipping invalid PGN entry: {e}")
            # Continue loading other entries rather than failing completely

    return rvc_spec


def load_device_mapping(mapping_path: str) -> dict[str, Any]:
    """
    Load the device mapping YAML file.

    Args:
        mapping_path: Path to the device mapping YAML file

    Returns:
        The loaded device mapping

    Raises:
        FileNotFoundError: If the mapping file doesn't exist
    """
    try:
        logger.info(f"Loading device mapping from: {mapping_path}")
        with open(mapping_path, encoding="utf-8") as f:
            device_mapping = yaml.safe_load(f)
    except FileNotFoundError:
        logger.error(f"Device mapping file not found: {mapping_path}")
        raise
    except yaml.YAMLError as e:
        raise ConfigValidationError(f"Invalid YAML in device mapping file: {e}") from e
    except Exception as e:
        logger.error(f"Failed to load device mapping: {e}")
        raise ConfigValidationError(f"Failed to load device mapping: {e}") from e

    if not isinstance(device_mapping, dict):
        raise ConfigValidationError("Device mapping must be a dictionary")

    return device_mapping


def get_default_paths() -> tuple[str, str]:
    """
    Determine default paths for the RVC spec and device mapping files.

    Returns:
        Tuple of (rvc_spec_path, device_mapping_path)

    Raises:
        FileNotFoundError: If required files don't exist
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


def select_coach_mapping_file(config_dir: str | pathlib.Path) -> pathlib.Path:
    """
    Select the appropriate coach mapping file based on environment variables.

    Priority:
    1. RVC_COACH_MODEL environment variable (e.g., "2021_Entegra_Aspire_44R")
    2. Default fallback: "coach_mapping.default.yml"

    Args:
        config_dir: Path to the config directory containing mapping files

    Returns:
        Path to the selected coach mapping file

    Raises:
        FileNotFoundError: If no suitable mapping file is found
    """
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


def extract_coach_info(device_mapping: dict[str, Any], mapping_path: str) -> CoachInfo:
    """
    Extract coach information from the mapping file.

    This extracts coach metadata from either:
    1. The "coach_info" section in the mapping file, or
    2. The filename itself (looking for year_make_model_trim pattern)

    Args:
        device_mapping: The loaded mapping dictionary
        mapping_path: The path to the mapping file

    Returns:
        CoachInfo object with detected coach metadata
    """
    coach_info = CoachInfo(filename=os.path.basename(mapping_path))

    # Try to get metadata from the mapping file first
    # Support both "_coach_info" (legacy) and "coach_info" keys
    info_section = device_mapping.get("coach_info") or device_mapping.get("_coach_info")

    if info_section and isinstance(info_section, dict):
        for field in ["year", "make", "model", "trim", "notes"]:
            if field in info_section:
                setattr(coach_info, field, str(info_section[field]))
        return coach_info

    # Try to parse from filename if no explicit metadata
    basename = os.path.basename(mapping_path)
    if basename.endswith(".yml") or basename.endswith(".yaml"):
        basename = basename[:-4] if basename.endswith(".yml") else basename[:-5]

    # Look for pattern like "2021_Entegra_Aspire_44R"
    parts = basename.split("_")
    # Check if we have enough parts and first part is a year (4 digits)
    if len(parts) >= 4 and parts[0].isdigit() and len(parts[0]) == 4:
        coach_info.year = parts[0]
        coach_info.make = parts[1]
        coach_info.model = parts[2]
        coach_info.trim = "_".join(parts[3:])  # Join remaining parts as trim

    return coach_info
