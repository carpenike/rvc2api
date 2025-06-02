"""
RV-C feature module for the feature management system.

This module provides a Feature class implementation for RV-C protocol integration,
allowing it to be dynamically enabled/disabled and managed by the FeatureManager.
"""

import logging
from typing import Any

from backend.services.feature_base import Feature

logger = logging.getLogger(__name__)


class RVCFeature(Feature):
    """
    RVC protocol integration feature.

    This feature manages the RV-C protocol integration, providing decoding and encoding
    of RV-C messages and maintaining state related to RV-C devices.
    """

    def __init__(
        self,
        name: str = "rvc",
        enabled: bool = True,
        core: bool = True,
        config: dict[str, Any] | None = None,
        dependencies: list[str] | None = None,
    ):
        """
        Initialize the RVC feature.

        Args:
            name: The name of the feature (default: "rvc")
            enabled: Whether the feature is enabled (default: True)
            core: Whether this is a core feature (default: True)
            config: Optional configuration dictionary
            dependencies: List of feature names this feature depends on
        """
        super().__init__(name=name, enabled=enabled, core=core, dependencies=dependencies)
        self.config = config or {}
        self._rvc_spec_path = self.config.get("rvc_spec_path")
        self._device_mapping_path = self.config.get("device_mapping_path")
        self._data_loaded = False

    async def startup(self) -> None:
        """
        Start the RVC feature.

        This loads the RVC spec and device mapping data.
        """
        logger.info("Starting RVC feature")
        await self._load_rvc_data()

    async def shutdown(self) -> None:
        """
        Stop the RVC feature.
        """
        logger.info("Stopping RVC feature")
        self._data_loaded = False

    async def _load_rvc_data(self) -> None:
        """
        Load RVC spec and device mapping data.
        """
        from backend.core.config import get_settings
        from backend.integrations.rvc.decode import load_config_data

        try:
            # Get settings to check for environment variable overrides
            settings = get_settings()

            # Use environment variables if available, otherwise fall back to config or defaults
            spec_path_override = None
            map_path_override = None

            if settings.rvc_spec_path:
                spec_path_override = str(settings.rvc_spec_path)
                logger.info(f"Using RVC spec path from environment: {spec_path_override}")
            elif self._rvc_spec_path:
                spec_path_override = self._rvc_spec_path
                logger.info(f"Using RVC spec path from config: {spec_path_override}")

            if settings.rvc_coach_mapping_path:
                map_path_override = str(settings.rvc_coach_mapping_path)
                logger.info(f"Using device mapping path from environment: {map_path_override}")
            elif self._device_mapping_path:
                map_path_override = self._device_mapping_path
                logger.info(f"Using device mapping path from config: {map_path_override}")

            # Load data using the override paths (load_config_data will handle defaults if None)
            (
                self.dgn_dict,
                self.spec_meta,
                self.mapping_dict,
                self.entity_map,
                self.entity_ids,
                self.inst_map,
                self.unique_instances,
                self.pgn_hex_to_name_map,
                self.dgn_pairs,
                self.coach_info,
            ) = load_config_data(
                rvc_spec_path_override=spec_path_override,
                device_mapping_path_override=map_path_override,
            )
            self._data_loaded = True
            logger.info(f"RVC data loaded - coach: {self.coach_info}")
        except FileNotFoundError as e:
            logger.warning(f"RVC configuration files not found: {e}")
            self._data_loaded = False
        except Exception as e:
            logger.error(f"Failed to load RVC data: {e}")
            self._data_loaded = False

    def is_data_loaded(self) -> bool:
        """
        Check if RVC data is loaded.

        Returns:
            True if data is loaded, False otherwise
        """
        return self._data_loaded

    @property
    def health(self) -> str:
        """
        Returns the health status of the feature.

        Returns:
            - "disabled": Feature is not enabled
            - "healthy": Feature is functioning correctly
            - "degraded": Feature has non-critical issues
            - "unhealthy": Feature is not functioning correctly
        """
        if not self.enabled:
            return "disabled"

        if self.is_data_loaded():
            return "healthy"
        else:
            return "unhealthy"
