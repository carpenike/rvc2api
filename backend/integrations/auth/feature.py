"""
Authentication Feature Integration

This module provides the authentication feature integration for the CoachIQ
feature management system. It handles initialization, dependency management,
and lifecycle management of the authentication system.
"""

import asyncio
import logging
from typing import TYPE_CHECKING, Any

from backend.core.config import get_settings
from backend.core.persistence_feature import get_persistence_feature
from backend.services.auth_manager import AuthManager
from backend.services.auth_repository import AuthRepository
from backend.services.feature_base import Feature


class AuthenticationFeature(Feature):
    """
    Authentication feature integration for CoachIQ.

    This feature provides:
    - Authentication manager initialization
    - Integration with notification system for magic links
    - Authentication mode detection and configuration
    - Dependency injection support for auth manager
    """

    def __init__(self, **kwargs):
        """Initialize the authentication feature."""
        super().__init__(**kwargs)
        self.auth_manager: AuthManager | None = None
        self.auth_repository: AuthRepository | None = None
        self.logger = logging.getLogger(__name__)
        self.settings = get_settings()

    async def startup(self) -> None:
        """Initialize the authentication feature on startup."""
        await super().startup()

        try:
            # Get notification manager if available (optional)
            notification_manager = None
            # TODO: Implement notification manager access when needed

            # Initialize auth repository with database manager from persistence feature (MANDATORY)
            # Get persistence feature using the established pattern
            persistence_feature = get_persistence_feature()
            database_manager = persistence_feature.get_database_manager()

            if not database_manager:
                msg = "Database manager not available - authentication requires mandatory persistence"
                self.logger.error(msg)
                raise RuntimeError(msg)

            # Create the auth repository (MANDATORY)
            auth_repository = AuthRepository(database_manager)
            self.auth_repository = auth_repository
            self.logger.info("Auth repository initialized with mandatory database persistence")

            # Initialize auth manager
            self.auth_manager = AuthManager(
                auth_settings=self.settings.auth,
                notification_manager=notification_manager,
                auth_repository=auth_repository,
            )

            await self.auth_manager.startup()

            self.logger.info("Authentication feature initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize authentication feature: {e}")
            raise

    async def shutdown(self) -> None:
        """Shutdown the authentication feature."""
        if self.auth_manager:
            try:
                await self.auth_manager.shutdown()
                self.logger.info("Authentication feature shutdown complete")
            except Exception as e:
                self.logger.error(f"Error during authentication feature shutdown: {e}")

        await super().shutdown()

    def get_auth_manager(self) -> AuthManager | None:
        """Get the authentication manager instance."""
        return self.auth_manager

    async def health_check(self) -> dict[str, Any]:
        """
        Perform health check on the authentication feature.

        Returns:
            Dict[str, Any]: Health check results
        """
        if not self.auth_manager:
            return {"status": "unhealthy", "error": "Auth manager not initialized"}

        try:
            stats = await self.auth_manager.get_stats()
            return {
                "status": "healthy",
                "auth_mode": stats.get("auth_mode"),
                "jwt_available": stats.get("jwt_available"),
                "secret_key_configured": stats.get("secret_key_configured"),
                "notification_manager_available": stats.get("notification_manager_available"),
            }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    async def get_feature_info(self) -> dict[str, Any]:
        """
        Get feature information and current status.

        Returns:
            Dict[str, Any]: Feature information
        """
        info = {
            "name": "Authentication System",
            "description": "JWT-based authentication with magic links and admin user management",
            "version": "1.0.0",
            "status": "running" if self.auth_manager else "stopped",
        }

        if self.auth_manager:
            try:
                stats = await self.auth_manager.get_stats()
                info.update(
                    {
                        "auth_mode": stats.get("auth_mode"),
                        "dependencies_available": stats.get("jwt_available"),
                        "configuration": {
                            "jwt_algorithm": self.settings.auth.jwt_algorithm,
                            "jwt_expire_minutes": self.settings.auth.jwt_expire_minutes,
                            "magic_link_expire_minutes": self.settings.auth.magic_link_expire_minutes,
                            "enable_magic_links": self.settings.auth.enable_magic_links,
                            "enable_oauth": self.settings.auth.enable_oauth,
                        },
                    }
                )
            except Exception as e:
                info["error"] = str(e)

        return info

    def get_dependencies(self) -> list[str]:
        """
        Get list of feature dependencies.

        Returns:
            list[str]: List of required feature names
        """
        return ["persistence", "notifications"]

    def is_ready(self) -> bool:
        """
        Check if the authentication feature is ready for use.

        Returns:
            bool: True if ready, False otherwise
        """
        return self.auth_manager is not None

    @property
    def health(self) -> str:
        """
        Get the health status of the authentication feature.

        Returns:
            str: Health status ('healthy', 'degraded', or 'failed')
        """
        if not self.enabled:
            return "healthy"  # Disabled features are considered healthy

        if not self.auth_manager:
            return "failed"

        try:
            # Perform a basic health check
            stats = asyncio.run(self.auth_manager.get_stats())
            if stats.get("jwt_available") and stats.get("secret_key_configured"):
                return "healthy"
            return "degraded"
        except Exception:
            return "failed"
