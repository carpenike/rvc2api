"""
Unit tests for the configuration module (core_daemon.config).

These tests cover the various functions responsible for:
- Logger configuration (`configure_logger`):
    - Default log levels.
    - Log level overrides via environment variables.
    - Handling of invalid log level settings.
    - Clearing of existing log handlers.
- Actual path determination for spec and map files (`get_actual_paths`):
    - Usage of default paths.
    - Overrides via environment variables (CAN_SPEC_PATH, CAN_MAP_PATH).
    - Fallback to defaults if environment-specified paths are invalid.
    - Idempotency of path resolution.
- FastAPI application settings (`get_fastapi_config`):
    - Default application title, description, and root path.
    - Overrides via environment variables (RVC2API_TITLE, etc.).
- CAN bus settings (`get_canbus_config`):
    - Default CAN channels, bus type, and bitrate.
    - Overrides via environment variables (CAN_CHANNELS, etc.).
    - Correct parsing of channel lists and bitrate.
- Static file and template path resolution (`get_static_paths`):
    - Successful path resolution using `importlib.resources`.
    - Successful fallback to `__file__`-based resolution.
    - Error handling and logging for invalid or non-directory paths.
    - Logging of critical errors if essential paths cannot be determined.

The `reset_env_and_logger_state_and_config_globals` fixture ensures that each test
runs with a clean environment and that global states within the config module
(like cached paths) are reset.
"""

import logging
import os
from unittest.mock import MagicMock, call, patch

import pytest

import core_daemon.config as config_module  # To reset global paths
from core_daemon.config import (
    configure_logger,
    get_actual_paths,
    get_canbus_config,
    get_fastapi_config,
    get_static_paths,
)
from core_daemon.config import module_logger as config_module_logger

# Store original os.environ for restoration
ORIGINAL_ENV = os.environ.copy()


@pytest.fixture(autouse=True)
def reset_env_and_logger_state_and_config_globals():  # Renamed for clarity
    """Ensures a clean environment, logger state, and config module globals for each test."""
    os.environ.clear()
    os.environ.update(ORIGINAL_ENV)

    # Reset root logger handlers and level
    root_logger = logging.getLogger()
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)
    root_logger.setLevel(logging.WARNING)

    # Reset config_module_logger
    for handler in list(config_module_logger.handlers):
        config_module_logger.removeHandler(handler)
    config_module_logger.propagate = False
    config_module_logger.setLevel(logging.INFO)

    # Reset global path variables in config module
    config_module.ACTUAL_SPEC_PATH = None
    config_module.ACTUAL_MAP_PATH = None

    yield

    os.environ.clear()
    os.environ.update(ORIGINAL_ENV)
    config_module.ACTUAL_SPEC_PATH = None
    config_module.ACTUAL_MAP_PATH = None


@patch("core_daemon.config.coloredlogs.install")
@patch("core_daemon.config.logging.getLogger")
def test_configure_logger_defaults(mock_get_logger, mock_coloredlogs_install):
    """
    Test `configure_logger` with default LOG_LEVEL (INFO). Ensures correct setup of
    root logger and coloredlogs.
    """
    mock_root_logger = MagicMock(spec=logging.Logger)
    mock_get_logger.return_value = mock_root_logger

    if "LOG_LEVEL" in os.environ:
        del os.environ["LOG_LEVEL"]

    returned_logger = configure_logger()

    mock_get_logger.assert_called_once_with()  # Called to get the root logger
    mock_root_logger.setLevel.assert_called_once_with(logging.DEBUG)
    mock_coloredlogs_install.assert_called_once()
    args, kwargs = mock_coloredlogs_install.call_args
    assert kwargs["level"] == logging.INFO
    assert kwargs["logger"] == mock_root_logger
    assert returned_logger == mock_root_logger
    assert mock_root_logger.removeHandler.call_count == len(mock_root_logger.handlers)


@patch("core_daemon.config.coloredlogs.install")
@patch("core_daemon.config.logging.getLogger")
def test_configure_logger_with_env_var_debug(mock_get_logger, mock_coloredlogs_install):
    """
    Test `configure_logger` correctly uses the LOG_LEVEL from environment
    variables (e.g., DEBUG).
    """
    mock_root_logger = MagicMock(spec=logging.Logger)
    mock_get_logger.return_value = mock_root_logger
    os.environ["LOG_LEVEL"] = "DEBUG"

    configure_logger()

    mock_root_logger.setLevel.assert_called_once_with(logging.DEBUG)
    mock_coloredlogs_install.assert_called_once()
    args, kwargs = mock_coloredlogs_install.call_args
    assert kwargs["level"] == logging.DEBUG


@patch("core_daemon.config.coloredlogs.install")
@patch("core_daemon.config.logging.getLogger")
@patch.object(config_module_logger, "warning")  # Patch the logger used by config.py
def test_configure_logger_invalid_env_var(
    mock_config_logger_warning, mock_get_logger, mock_coloredlogs_install
):
    """
    Test `configure_logger` handles an invalid LOG_LEVEL, defaulting to INFO and
    logging a warning.
    """
    mock_root_logger = MagicMock(spec=logging.Logger)
    mock_get_logger.return_value = mock_root_logger
    os.environ["LOG_LEVEL"] = "INVALID_LEVEL"

    configure_logger()

    mock_root_logger.setLevel.assert_called_once_with(logging.DEBUG)
    mock_coloredlogs_install.assert_called_once()
    args, kwargs = mock_coloredlogs_install.call_args
    assert kwargs["level"] == logging.INFO  # Should default to INFO

    mock_config_logger_warning.assert_called_once_with(
        "Invalid LOG_LEVEL 'INVALID_LEVEL'. Defaulting to INFO."
    )


@patch("core_daemon.config.coloredlogs.install")
@patch("core_daemon.config.logging.getLogger")
def test_configure_logger_handler_clearing(mock_get_logger, mock_coloredlogs_install):
    """
    Test `configure_logger` clears any existing handlers from the root logger
    before adding its own.
    """
    mock_root_logger = MagicMock(spec=logging.Logger)
    # Simulate existing handlers
    mock_handler1 = MagicMock(spec=logging.Handler)
    mock_handler2 = MagicMock(spec=logging.Handler)
    mock_root_logger.handlers = [mock_handler1, mock_handler2]

    mock_get_logger.return_value = mock_root_logger

    if "LOG_LEVEL" in os.environ:
        del os.environ["LOG_LEVEL"]

    configure_logger()

    # Check that removeHandler was called for each simulated existing handler
    mock_root_logger.removeHandler.assert_has_calls(
        [call(mock_handler1), call(mock_handler2)], any_order=True
    )
    assert mock_root_logger.removeHandler.call_count == 2


@patch("core_daemon.config.coloredlogs.install")
@patch("core_daemon.config.logging.getLogger")
def test_configure_logger_root_level_set_to_debug(mock_get_logger, mock_coloredlogs_install):
    """
    Test `configure_logger` sets the root logger's level to DEBUG to allow
    handlers to filter effectively.
    """
    mock_root_logger = MagicMock(spec=logging.Logger)
    mock_get_logger.return_value = mock_root_logger

    if "LOG_LEVEL" in os.environ:
        del os.environ["LOG_LEVEL"]  # Use default LOG_LEVEL (INFO for coloredlogs)

    configure_logger()

    # Crucially, the root logger itself should be set to DEBUG to capture all levels
    # which are then filtered by handlers.
    mock_root_logger.setLevel.assert_called_once_with(logging.DEBUG)


# --- Tests for get_actual_paths ---

MOCK_DEFAULT_SPEC_PATH = "/default/rvc.json"
MOCK_DEFAULT_MAP_PATH = "/default/device_mapping.yml"
MOCK_ENV_SPEC_PATH = "/env/spec/rvc_custom.json"
MOCK_ENV_MAP_PATH = "/env/map/mapping_custom.yml"


@patch("core_daemon.config.os.access")
@patch("core_daemon.config.os.path.exists")
@patch("rvc_decoder.decode._default_paths")
@patch.object(config_module_logger, "info")
@patch.object(config_module_logger, "warning")
def test_get_actual_paths_defaults(
    mock_logger_warning, mock_logger_info, mock_default_paths_fn, mock_path_exists, mock_os_access
):
    """
    Test `get_actual_paths` uses default spec and map paths when no environment
    variables are set.
    """
    mock_default_paths_fn.return_value = (MOCK_DEFAULT_SPEC_PATH, MOCK_DEFAULT_MAP_PATH)
    # Ensure env vars are not set
    if "CAN_SPEC_PATH" in os.environ:
        del os.environ["CAN_SPEC_PATH"]
    if "CAN_MAP_PATH" in os.environ:
        del os.environ["CAN_MAP_PATH"]

    spec_path, map_path = get_actual_paths()

    assert spec_path == MOCK_DEFAULT_SPEC_PATH
    assert map_path == MOCK_DEFAULT_MAP_PATH
    assert config_module.ACTUAL_SPEC_PATH == MOCK_DEFAULT_SPEC_PATH
    assert config_module.ACTUAL_MAP_PATH == MOCK_DEFAULT_MAP_PATH
    mock_default_paths_fn.assert_called_once()
    mock_logger_warning.assert_not_called()
    # Check info logs for using determined paths
    mock_logger_info.assert_any_call(
        f"UI will attempt to display RVC spec from: {MOCK_DEFAULT_SPEC_PATH}"
    )
    mock_logger_info.assert_any_call(
        f"UI will attempt to display device mapping from: {MOCK_DEFAULT_MAP_PATH}"
    )


@patch("core_daemon.config.os.access")
@patch("core_daemon.config.os.path.exists")
@patch("rvc_decoder.decode._default_paths")
@patch.object(config_module_logger, "info")
@patch.object(config_module_logger, "warning")
def test_get_actual_paths_env_vars_valid(
    mock_logger_warning, mock_logger_info, mock_default_paths_fn, mock_path_exists, mock_os_access
):
    """
    Test `get_actual_paths` correctly uses paths from CAN_SPEC_PATH and CAN_MAP_PATH
    env vars when valid.
    """
    mock_default_paths_fn.return_value = (MOCK_DEFAULT_SPEC_PATH, MOCK_DEFAULT_MAP_PATH)
    mock_path_exists.return_value = True
    mock_os_access.return_value = True
    os.environ["CAN_SPEC_PATH"] = MOCK_ENV_SPEC_PATH
    os.environ["CAN_MAP_PATH"] = MOCK_ENV_MAP_PATH

    spec_path, map_path = get_actual_paths()

    assert spec_path == MOCK_ENV_SPEC_PATH
    assert map_path == MOCK_ENV_MAP_PATH
    assert config_module.ACTUAL_SPEC_PATH == MOCK_ENV_SPEC_PATH
    assert config_module.ACTUAL_MAP_PATH == MOCK_ENV_MAP_PATH
    mock_default_paths_fn.assert_called_once()  # Still called to get defaults as a base
    mock_logger_warning.assert_not_called()
    mock_logger_info.assert_any_call(
        f"UI will attempt to display RVC spec from: {MOCK_ENV_SPEC_PATH}"
    )
    mock_logger_info.assert_any_call(
        f"UI will attempt to display device mapping from: {MOCK_ENV_MAP_PATH}"
    )


@patch("core_daemon.config.os.access")
@patch("core_daemon.config.os.path.exists")
@patch("rvc_decoder.decode._default_paths")
@patch.object(config_module_logger, "warning")
def test_get_actual_paths_env_spec_invalid_exists(
    mock_logger_warning, mock_default_paths_fn, mock_path_exists, mock_os_access
):
    """
    Test `get_actual_paths` falls back to default spec path if CAN_SPEC_PATH is
    invalid (e.g., non-existent).
    """
    mock_default_paths_fn.return_value = (MOCK_DEFAULT_SPEC_PATH, MOCK_DEFAULT_MAP_PATH)

    # Spec path from env does not exist, map path from env is valid
    def side_effect_exists(path):
        if path == MOCK_ENV_SPEC_PATH:
            return False
        return path == MOCK_ENV_MAP_PATH

    mock_path_exists.side_effect = side_effect_exists
    mock_os_access.return_value = True  # Assume readable if exists

    os.environ["CAN_SPEC_PATH"] = MOCK_ENV_SPEC_PATH
    os.environ["CAN_MAP_PATH"] = MOCK_ENV_MAP_PATH

    spec_path, map_path = get_actual_paths()

    assert spec_path == MOCK_DEFAULT_SPEC_PATH  # Fallback for spec
    assert map_path == MOCK_ENV_MAP_PATH  # Env var for map
    mock_logger_warning.assert_any_call(
        f"Override RVC Spec Path '{MOCK_ENV_SPEC_PATH}' is missing or unreadable. "
        f"Core logic will attempt to use bundled default: '{MOCK_DEFAULT_SPEC_PATH}'"
    )


@patch("core_daemon.config.os.access")
@patch("core_daemon.config.os.path.exists")
@patch("rvc_decoder.decode._default_paths")
@patch.object(config_module_logger, "warning")
def test_get_actual_paths_env_map_invalid_access(
    mock_logger_warning, mock_default_paths_fn, mock_path_exists, mock_os_access
):
    """
    Test `get_actual_paths` falls back to default map path if CAN_MAP_PATH is
    invalid (e.g., not readable).
    """
    mock_default_paths_fn.return_value = (MOCK_DEFAULT_SPEC_PATH, MOCK_DEFAULT_MAP_PATH)

    # Spec path from env is valid, map path from env exists but not readable
    def side_effect_access(path, mode):
        return path != MOCK_ENV_MAP_PATH  # Assume spec path is readable

    mock_path_exists.return_value = True  # Assume both exist
    mock_os_access.side_effect = side_effect_access

    os.environ["CAN_SPEC_PATH"] = MOCK_ENV_SPEC_PATH
    os.environ["CAN_MAP_PATH"] = MOCK_ENV_MAP_PATH

    spec_path, map_path = get_actual_paths()

    assert spec_path == MOCK_ENV_SPEC_PATH  # Env var for spec
    assert map_path == MOCK_DEFAULT_MAP_PATH  # Fallback for map
    mock_logger_warning.assert_any_call(
        f"Override Device Mapping Path '{MOCK_ENV_MAP_PATH}' is missing or unreadable. "
        f"Core logic will attempt to use bundled default: '{MOCK_DEFAULT_MAP_PATH}'"
    )


@patch("core_daemon.config.os.access")
@patch("core_daemon.config.os.path.exists")
@patch("rvc_decoder.decode._default_paths")
@patch.object(config_module_logger, "info")
def test_get_actual_paths_idempotency(
    mock_logger_info, mock_default_paths_fn, mock_path_exists, mock_os_access
):
    """
    Test `get_actual_paths` is idempotent, returning cached paths on
    subsequent calls without re-computation.
    """
    mock_default_paths_fn.return_value = (MOCK_DEFAULT_SPEC_PATH, MOCK_DEFAULT_MAP_PATH)
    mock_path_exists.return_value = True
    mock_os_access.return_value = True
    os.environ["CAN_SPEC_PATH"] = MOCK_ENV_SPEC_PATH
    os.environ["CAN_MAP_PATH"] = MOCK_ENV_MAP_PATH

    # Call first time
    spec_path1, map_path1 = get_actual_paths()
    assert spec_path1 == MOCK_ENV_SPEC_PATH
    assert map_path1 == MOCK_ENV_MAP_PATH
    mock_default_paths_fn.assert_called_once()
    # Info logs for UI paths are called on the first determination
    first_call_info_count = mock_logger_info.call_count

    # Call second time
    spec_path2, map_path2 = get_actual_paths()
    assert spec_path2 == MOCK_ENV_SPEC_PATH
    assert map_path2 == MOCK_ENV_MAP_PATH

    # Ensure _default_paths and os checks were not called again
    mock_default_paths_fn.assert_called_once()
    # mock_path_exists and mock_os_access counts depend on how many times they are called
    # for spec and map. If both are from env, each is called once for spec, once for map.
    # For this test, the key is that their call counts do NOT increase on the second
    # call to get_actual_paths. So, we record their call counts after the first call and
    # assert they are the same after the second.

    path_exists_call_count_after_first = mock_path_exists.call_count
    os_access_call_count_after_first = mock_os_access.call_count

    # Call get_actual_paths again
    get_actual_paths()

    assert mock_path_exists.call_count == path_exists_call_count_after_first
    assert mock_os_access.call_count == os_access_call_count_after_first

    # Info logs for UI paths should not be repeated if paths are already determined.
    # The function has an optional debug log "Returning already determined actual paths."
    # which is commented out in the source. If it were active, call_count would increase.
    # For now, assuming no new "UI will attempt to display..." logs.
    assert mock_logger_info.call_count == first_call_info_count


# --- Tests for get_fastapi_config ---


def test_get_fastapi_config_defaults():
    """
    Test `get_fastapi_config` returns default FastAPI settings when no
    relevant environment variables are set.
    """
    # Ensure relevant env vars are not set
    if "RVC2API_TITLE" in os.environ:
        del os.environ["RVC2API_TITLE"]
    if "RVC2API_SERVER_DESCRIPTION" in os.environ:
        del os.environ["RVC2API_SERVER_DESCRIPTION"]
    if "RVC2API_ROOT_PATH" in os.environ:
        del os.environ["RVC2API_ROOT_PATH"]

    config = get_fastapi_config()
    assert config["title"] == "rvc2api"
    assert config["server_description"] == "RV-C to API Bridge"
    assert config["root_path"] == ""


def test_get_fastapi_config_env_vars():
    """Test `get_fastapi_config` correctly uses FastAPI settings from environment variables."""
    os.environ["RVC2API_TITLE"] = "Test Title"
    os.environ["RVC2API_SERVER_DESCRIPTION"] = "Test Description"
    os.environ["RVC2API_ROOT_PATH"] = "/test/api"

    config = get_fastapi_config()
    assert config["title"] == "Test Title"
    assert config["server_description"] == "Test Description"
    assert config["root_path"] == "/test/api"


# --- Tests for get_canbus_config ---


def test_get_canbus_config_defaults():
    """
    Test `get_canbus_config` returns default CAN bus settings when no relevant
    environment variables are set.
    """
    # Ensure relevant env vars are not set
    if "CAN_CHANNELS" in os.environ:
        del os.environ["CAN_CHANNELS"]
    if "CAN_BUSTYPE" in os.environ:
        del os.environ["CAN_BUSTYPE"]
    if "CAN_BITRATE" in os.environ:
        del os.environ["CAN_BITRATE"]

    config = get_canbus_config()
    assert config["channels"] == ["can0", "can1"]
    assert config["bustype"] == "socketcan"
    assert config["bitrate"] == 500000


def test_get_canbus_config_env_vars():
    """Test `get_canbus_config` correctly uses CAN bus settings from environment variables."""
    os.environ["CAN_CHANNELS"] = "can2,can3"
    os.environ["CAN_BUSTYPE"] = "pcan"
    os.environ["CAN_BITRATE"] = "250000"

    config = get_canbus_config()
    assert config["channels"] == ["can2", "can3"]
    assert config["bustype"] == "pcan"
    assert config["bitrate"] == 250000


def test_get_canbus_config_single_channel():
    """
    Test `get_canbus_config` correctly parses a single CAN channel from the
    environment variable.
    """
    os.environ["CAN_CHANNELS"] = "can0"
    config = get_canbus_config()
    assert config["channels"] == ["can0"]


def test_get_canbus_config_bitrate_conversion():
    """
    Test `get_canbus_config` correctly converts the CAN_BITRATE
    environment variable to an integer.
    """
    os.environ["CAN_BITRATE"] = "1000000"
    config = get_canbus_config()
    assert isinstance(config["bitrate"], int)
    assert config["bitrate"] == 1000000


# --- Tests for get_static_paths ---

# Mock paths for importlib.resources
MOCK_STATIC_PATH_LIB = "/resolved/via/importlib/static"
MOCK_TEMPLATES_PATH_LIB = "/resolved/via/importlib/templates"
MOCK_WEB_UI_PATH_LIB = "/resolved/via/importlib/web_ui"

# Mock paths for __file__ fallback
MOCK_CONFIG_FILE_PATH = "/src/core_daemon/config.py"
MOCK_CORE_DAEMON_DIR_FALLBACK = "/src/core_daemon"
MOCK_WEB_UI_DIR_FALLBACK = "/src/core_daemon/web_ui"
MOCK_STATIC_DIR_FALLBACK = "/src/core_daemon/web_ui/static"
MOCK_TEMPLATES_DIR_FALLBACK = "/src/core_daemon/web_ui/templates"


@patch("core_daemon.config.os.path.isdir")
@patch("core_daemon.config.importlib.resources.files")
@patch.object(config_module_logger, "info")
@patch.object(config_module_logger, "error")
@patch.object(config_module_logger, "critical")
def test_get_static_paths_importlib_resources_success(
    mock_logger_critical,
    mock_logger_error,
    mock_logger_info,
    mock_importlib_files,
    mock_os_path_isdir,
):
    """Test `get_static_paths` successfully resolves UI paths using `importlib.resources`."""
    mock_os_path_isdir.return_value = True  # All resolved paths are valid directories

    def mock_files_side_effect(package_path):
        mock_traversable = MagicMock()
        if package_path == "core_daemon.web_ui.static":
            mock_traversable.__str__ = MagicMock(return_value=MOCK_STATIC_PATH_LIB)
            mock_traversable.is_dir.return_value = True
        elif package_path == "core_daemon.web_ui.templates":
            mock_traversable.__str__ = MagicMock(return_value=MOCK_TEMPLATES_PATH_LIB)
            mock_traversable.is_dir.return_value = True
        elif package_path == "core_daemon.web_ui":
            mock_traversable.__str__ = MagicMock(return_value=MOCK_WEB_UI_PATH_LIB)
            mock_traversable.is_dir.return_value = True
        else:
            raise ValueError(f"Unexpected package_path: {package_path}")
        return mock_traversable

    mock_importlib_files.side_effect = mock_files_side_effect

    paths = get_static_paths()

    assert paths["static_dir"] == MOCK_STATIC_PATH_LIB
    assert paths["templates_dir"] == MOCK_TEMPLATES_PATH_LIB
    assert paths["web_ui_dir"] == MOCK_WEB_UI_PATH_LIB
    mock_logger_info.assert_any_call("Attempting to get static paths using importlib.resources...")
    mock_logger_info.assert_any_call(
        f"importlib.resources resolved static_dir: {MOCK_STATIC_PATH_LIB}"
    )
    mock_logger_info.assert_any_call(
        f"importlib.resources resolved templates_dir: {MOCK_TEMPLATES_PATH_LIB}"
    )
    mock_logger_info.assert_any_call(
        f"importlib.resources resolved web_ui_dir: {MOCK_WEB_UI_PATH_LIB}"
    )
    mock_logger_info.assert_any_call(f"Final static_dir to be used: {MOCK_STATIC_PATH_LIB}")
    mock_logger_info.assert_any_call(f"Final templates_dir to be used: {MOCK_TEMPLATES_PATH_LIB}")
    mock_logger_info.assert_any_call(f"Final web_ui_dir to be used: {MOCK_WEB_UI_PATH_LIB}")
    mock_logger_error.assert_not_called()
    mock_logger_critical.assert_not_called()


@patch("core_daemon.config.os.path.isdir")
@patch("core_daemon.config.importlib.resources.files")
@patch("core_daemon.config.os.path.abspath")
@patch("core_daemon.config.os.path.dirname")
@patch("core_daemon.config.os.path.join")
@patch.object(config_module_logger, "info")
@patch.object(config_module_logger, "error")
@patch.object(config_module_logger, "critical")
def test_get_static_paths_fallback_success(
    mock_logger_critical,
    mock_logger_error,
    mock_logger_info,
    mock_os_path_join,
    mock_os_path_dirname,
    mock_os_path_abspath,
    mock_importlib_files,
    mock_os_path_isdir,
):
    """
    Test `get_static_paths` successfully falls back to `__file__`-based UI path resolution
    when `importlib.resources` fails.
    """
    mock_importlib_files.side_effect = Exception("Importlib error")
    mock_os_path_isdir.return_value = True  # All fallback paths are valid directories
    mock_os_path_abspath.return_value = MOCK_CONFIG_FILE_PATH

    # Mock os.path.dirname to return parent directories as expected
    def dirname_side_effect(path):
        if path == MOCK_CONFIG_FILE_PATH:
            return MOCK_CORE_DAEMON_DIR_FALLBACK  # Parent of config.py is core_daemon/
        # Add more specific mocks if other dirname calls are made, though not expected here
        return os.path.dirname(path)  # Default to actual dirname for unexpected calls

    mock_os_path_dirname.side_effect = dirname_side_effect

    # Mock os.path.join to construct paths as expected
    def join_side_effect(*args):
        if args == (MOCK_CORE_DAEMON_DIR_FALLBACK, "web_ui"):
            return MOCK_WEB_UI_DIR_FALLBACK
        if args == (MOCK_WEB_UI_DIR_FALLBACK, "static"):
            return MOCK_STATIC_DIR_FALLBACK
        if args == (MOCK_WEB_UI_DIR_FALLBACK, "templates"):
            return MOCK_TEMPLATES_DIR_FALLBACK
        return os.path.join(*args)  # Default to actual join

    mock_os_path_join.side_effect = join_side_effect

    paths = get_static_paths()

    assert paths["static_dir"] == MOCK_STATIC_DIR_FALLBACK
    assert paths["templates_dir"] == MOCK_TEMPLATES_DIR_FALLBACK
    assert paths["web_ui_dir"] == MOCK_WEB_UI_DIR_FALLBACK
    mock_logger_error.assert_any_call(
        "Error using importlib.resources ('Importlib error')."
        "Falling back to __file__-based path resolution.",
        exc_info=True,
    )
    mock_logger_info.assert_any_call(f"Fallback resolved static_dir: {MOCK_STATIC_DIR_FALLBACK}")
    mock_logger_info.assert_any_call(
        f"Fallback resolved templates_dir: {MOCK_TEMPLATES_DIR_FALLBACK}"
    )
    mock_logger_info.assert_any_call(f"Fallback resolved web_ui_dir: {MOCK_WEB_UI_DIR_FALLBACK}")
    mock_logger_critical.assert_not_called()


@patch("core_daemon.config.os.path.isdir")
@patch("core_daemon.config.importlib.resources.files")
@patch.object(config_module_logger, "critical")
def test_get_static_paths_importlib_final_validation_fails_static(
    mock_logger_critical, mock_importlib_files, mock_os_path_isdir
):
    """
    Test `get_static_paths` logs a critical error if the static dir (via importlib)
    fails final validation (isdir).
    """

    # importlib.resources resolves paths, but static_dir fails os.path.isdir validation
    def isdir_side_effect(path):
        return path != MOCK_STATIC_PATH_LIB

    mock_os_path_isdir.side_effect = isdir_side_effect

    def mock_files_side_effect(package_path):
        mock_traversable = MagicMock()
        if package_path == "core_daemon.web_ui.static":
            mock_traversable.__str__ = MagicMock(return_value=MOCK_STATIC_PATH_LIB)
            mock_traversable.is_dir.return_value = True
        elif package_path == "core_daemon.web_ui.templates":
            mock_traversable.__str__ = MagicMock(return_value=MOCK_TEMPLATES_PATH_LIB)
            mock_traversable.is_dir.return_value = True
        elif package_path == "core_daemon.web_ui":
            mock_traversable.__str__ = MagicMock(return_value=MOCK_WEB_UI_PATH_LIB)
            mock_traversable.is_dir.return_value = True
        return mock_traversable

    mock_importlib_files.side_effect = mock_files_side_effect

    get_static_paths()
    mock_logger_critical.assert_any_call(
        f"CRITICAL FAILURE: Final static_dir ('{MOCK_STATIC_PATH_LIB}')is invalid"
        "or not a directory. Static files will likely fail to serve."
    )


@patch("core_daemon.config.os.path.isdir")
@patch("core_daemon.config.importlib.resources.files")
@patch("core_daemon.config.os.path.abspath")
@patch("core_daemon.config.os.path.dirname")
@patch("core_daemon.config.os.path.join")
@patch.object(config_module_logger, "critical")
def test_get_static_paths_fallback_final_validation_fails_templates(
    mock_logger_critical,
    mock_os_path_join,
    mock_os_path_dirname,
    mock_os_path_abspath,
    mock_importlib_files,
    mock_os_path_isdir,
):
    """
    Test `get_static_paths` logs a critical error if the templates dir (via fallback)
    fails final validation (isdir).
    """
    mock_importlib_files.side_effect = Exception("Importlib error")  # Force fallback

    # Fallback resolves paths, but templates_dir fails os.path.isdir validation
    def isdir_side_effect(path):
        return path != MOCK_TEMPLATES_DIR_FALLBACK

    mock_os_path_isdir.side_effect = isdir_side_effect

    mock_os_path_abspath.return_value = MOCK_CONFIG_FILE_PATH
    mock_os_path_dirname.return_value = MOCK_CORE_DAEMON_DIR_FALLBACK  # Simplified for this test

    def join_side_effect(*args):
        if args == (MOCK_CORE_DAEMON_DIR_FALLBACK, "web_ui"):
            return MOCK_WEB_UI_DIR_FALLBACK
        if args == (MOCK_WEB_UI_DIR_FALLBACK, "static"):
            return MOCK_STATIC_DIR_FALLBACK
        if args == (MOCK_WEB_UI_DIR_FALLBACK, "templates"):
            return MOCK_TEMPLATES_DIR_FALLBACK
        return os.path.join(*args)

    mock_os_path_join.side_effect = join_side_effect

    get_static_paths()
    mock_logger_critical.assert_any_call(
        f"CRITICAL FAILURE: Final templates_dir ('{MOCK_TEMPLATES_DIR_FALLBACK}')"
        "is invalid or not a directory. Templates will likely fail to load."
    )


@patch("core_daemon.config.os.path.isdir")
@patch("core_daemon.config.importlib.resources.files")
@patch.object(config_module_logger, "error")
def test_get_static_paths_importlib_resource_is_not_dir(
    mock_logger_error, mock_importlib_files, mock_os_path_isdir
):
    """
    Test `get_static_paths` logs an error and triggers fallback if `importlib.resources`
    resolves a path that is not a directory.
    """
    mock_os_path_isdir.return_value = True  # Assume fallback validation would pass if reached

    def mock_files_side_effect(package_path):
        mock_traversable = MagicMock()
        if package_path == "core_daemon.web_ui.static":
            mock_traversable.__str__ = MagicMock(return_value=MOCK_STATIC_PATH_LIB)
            mock_traversable.is_dir.return_value = False  # Static is not a dir
        elif package_path == "core_daemon.web_ui.templates":
            mock_traversable.__str__ = MagicMock(return_value=MOCK_TEMPLATES_PATH_LIB)
            mock_traversable.is_dir.return_value = True
        elif package_path == "core_daemon.web_ui":
            # Simulate web_ui path itself not being a directory directly
            mock_traversable.is_dir.return_value = False
            # __str__ might still be called, so give it a value
            mock_traversable.__str__ = MagicMock(return_value="dummy_web_ui_path_not_dir")
        else:
            raise ValueError(f"Unexpected package_path: {package_path}")
        return mock_traversable

    mock_importlib_files.side_effect = mock_files_side_effect

    # Patch fallback os calls to avoid errors if fallback is triggered
    with patch("core_daemon.config.os.path.abspath"), patch(
        "core_daemon.config.os.path.dirname"
    ), patch("core_daemon.config.os.path.join"):
        get_static_paths()

    mock_logger_error.assert_any_call(
        "'core_daemon.web_ui.static' resolved by importlib.resources is not a directory."
    )
    # Also check that the fallback was triggered due to the ValueError raised internally
    mock_logger_error.assert_any_call(
        "Error using importlib.resources (''core_daemon.web_ui.static' "
        "is not a directory via importlib.resources'). Falling back to "
        "__file__-based path resolution.",
        exc_info=True,
    )


@patch("core_daemon.config.os.path.isdir")
@patch("core_daemon.config.importlib.resources.files")
@patch.object(config_module_logger, "info")
@patch.object(config_module_logger, "error")
def test_get_static_paths_importlib_derive_web_ui_dir(
    mock_logger_error, mock_logger_info, mock_importlib_files, mock_os_path_isdir
):
    """
    Test `get_static_paths` successfully derives web_ui_dir from static_dir
    when importlib.resources.files("core_daemon.web_ui").is_dir() is False,
    but static and templates dirs are resolved correctly.
    """
    mock_os_path_isdir.return_value = True  # All resolved paths are valid directories

    # Store the original os.path.dirname to mock it and restore later
    original_os_path_dirname = os.path.dirname

    def mock_files_side_effect(package_path):
        mock_traversable = MagicMock()
        if package_path == "core_daemon.web_ui.static":
            mock_traversable.__str__ = MagicMock(return_value=MOCK_STATIC_PATH_LIB)
            mock_traversable.is_dir.return_value = True
        elif package_path == "core_daemon.web_ui.templates":
            mock_traversable.__str__ = MagicMock(return_value=MOCK_TEMPLATES_PATH_LIB)
            mock_traversable.is_dir.return_value = True
        elif package_path == "core_daemon.web_ui":
            # Simulate web_ui path itself not being a directory directly
            mock_traversable.is_dir.return_value = False
            # __str__ might still be called, so give it a value
            mock_traversable.__str__ = MagicMock(return_value="dummy_web_ui_path_not_dir")
        else:
            raise ValueError(f"Unexpected package_path: {package_path}")
        return mock_traversable

    mock_importlib_files.side_effect = mock_files_side_effect

    # Mock os.path.dirname specifically for deriving web_ui_dir from static_dir
    def mocked_dirname(path):
        if path == MOCK_STATIC_PATH_LIB:
            return MOCK_WEB_UI_PATH_LIB  # Expected derived path
        return original_os_path_dirname(path)  # Fallback to real dirname for other calls

    with patch("core_daemon.config.os.path.dirname", side_effect=mocked_dirname):
        paths = get_static_paths()

    assert paths["static_dir"] == MOCK_STATIC_PATH_LIB
    assert paths["templates_dir"] == MOCK_TEMPLATES_PATH_LIB
    assert paths["web_ui_dir"] == MOCK_WEB_UI_PATH_LIB  # Crucially, this should be derived

    mock_logger_info.assert_any_call(
        f"Derived web_ui_dir from static_dir('{MOCK_STATIC_PATH_LIB}'): {MOCK_WEB_UI_PATH_LIB}"
    )
    mock_logger_error.assert_not_called()  # No errors expected in this scenario
