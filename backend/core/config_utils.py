"""
Backend configuration utilities.

Provides configuration path utilities for the backend application.
"""

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# Module-level globals to store determined paths to configuration files.
ACTUAL_SPEC_PATH: str | None = None
ACTUAL_MAP_PATH: str | None = None


def get_actual_paths() -> tuple[str | None, str | None]:
    """
    Determines and returns the actual paths to the RVC specification and device mapping files.

    Returns:
        tuple[str | None, str | None]: A tuple containing the actual path to the RVC specification file
                                       and the actual path to the device mapping file.
    """
    global ACTUAL_SPEC_PATH, ACTUAL_MAP_PATH

    # If paths have already been determined and cached, return them immediately.
    if ACTUAL_SPEC_PATH is not None and ACTUAL_MAP_PATH is not None:
        return ACTUAL_SPEC_PATH, ACTUAL_MAP_PATH

    # Try to get paths from RVC integration module
    try:
        from backend.integrations.rvc.config_loader import get_default_paths

        decoder_default_spec_path, decoder_default_map_path = get_default_paths()
    except ImportError as e:
        logger.warning(f"Could not import backend.integrations.rvc.decode._default_paths: {e}")
        decoder_default_spec_path = None
        decoder_default_map_path = None

    # Check environment overrides
    spec_override_env = os.getenv("RVC_SPEC_PATH")
    mapping_override_env = os.getenv("RVC_COACH_MAPPING_PATH")

    # Determine actual spec path
    if (
        spec_override_env
        and os.path.exists(spec_override_env)
        and os.access(spec_override_env, os.R_OK)
    ):
        ACTUAL_SPEC_PATH = spec_override_env
        logger.info(f"Using RVC Spec Path from environment variable: {spec_override_env}")
    elif decoder_default_spec_path:
        ACTUAL_SPEC_PATH = decoder_default_spec_path
        logger.info(f"Using default RVC Spec Path: {decoder_default_spec_path}")
    else:
        ACTUAL_SPEC_PATH = None
        logger.warning("No RVC spec path available")

    # Determine actual mapping path
    if (
        mapping_override_env
        and os.path.exists(mapping_override_env)
        and os.access(mapping_override_env, os.R_OK)
    ):
        ACTUAL_MAP_PATH = mapping_override_env
        logger.info(f"Using Device Mapping Path from environment variable: {mapping_override_env}")
    elif decoder_default_map_path:
        ACTUAL_MAP_PATH = decoder_default_map_path
        logger.info(f"Using default Device Mapping Path: {decoder_default_map_path}")
    else:
        ACTUAL_MAP_PATH = None
        logger.warning("No device mapping path available")

    return ACTUAL_SPEC_PATH, ACTUAL_MAP_PATH


def get_config_dir() -> Path:
    """
    Get the configuration directory path.

    Returns:
        Path: The path to the configuration directory
    """
    # Get the project root directory (where config/ is located)
    current_file = Path(__file__)
    project_root = current_file.parent.parent.parent  # backend/core/config_utils.py -> project root
    config_dir = project_root / "config"

    if not config_dir.exists():
        logger.warning(f"Configuration directory does not exist: {config_dir}")

    return config_dir


__all__ = ["get_actual_paths", "get_config_dir"]
