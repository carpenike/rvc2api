"""
In-Memory Persistence Implementation

Provides in-memory implementations of persistence interfaces for
when persistence is disabled.
"""

import logging

from backend.models.persistence import DashboardConfiguration
from backend.models.unmapped import UnmappedEntryModel
from backend.services.persistence_interface import (
    ConfigRepositoryInterface,
    DashboardRepositoryInterface,
    PersistenceServiceInterface,
    UnmappedRepositoryInterface,
)

logger = logging.getLogger(__name__)


class InMemoryPersistenceService(PersistenceServiceInterface):
    """In-memory persistence service for when persistence is disabled."""

    def __init__(self):
        """Initialize the in-memory persistence service."""
        self.config_repo = InMemoryConfigRepository()
        self.dashboard_repo = InMemoryDashboardRepository()
        self.unmapped_repo = InMemoryUnmappedRepository()

    async def initialize(self) -> None:
        """Initialize the persistence service."""
        logger.info("In-memory persistence service initialized")

    async def health_check(self) -> bool:
        """Check if the persistence service is healthy."""
        return True

    async def close(self) -> None:
        """Close the persistence service."""
        logger.info("In-memory persistence service closed")


class InMemoryConfigRepository(ConfigRepositoryInterface):
    """In-memory implementation of configuration repository."""

    def __init__(self):
        """Initialize the in-memory config repository."""
        self._configs: dict[str, str] = {}

    async def get_user_config(self, key: str) -> str | None:
        """Get a user configuration value."""
        return self._configs.get(key)

    async def set_user_config(self, key: str, value: str) -> None:
        """Set a user configuration value."""
        self._configs[key] = value

    async def get_all_user_configs(self) -> dict[str, str]:
        """Get all user configuration values."""
        return self._configs.copy()

    async def delete_user_config(self, key: str) -> bool:
        """Delete a user configuration value."""
        if key in self._configs:
            del self._configs[key]
            return True
        return False


class InMemoryDashboardRepository(DashboardRepositoryInterface):
    """In-memory implementation of dashboard repository."""

    def __init__(self):
        """Initialize the in-memory dashboard repository."""
        self._dashboards: dict[str, DashboardConfiguration] = {}

    async def get_dashboard(self, dashboard_id: str) -> DashboardConfiguration | None:
        """Get a dashboard by ID."""
        return self._dashboards.get(dashboard_id)

    async def save_dashboard(self, dashboard: DashboardConfiguration) -> None:
        """Save a dashboard configuration."""
        self._dashboards[dashboard.config_name] = dashboard

    async def list_dashboards(self) -> list[DashboardConfiguration]:
        """List all dashboards."""
        return list(self._dashboards.values())

    async def delete_dashboard(self, dashboard_id: str) -> bool:
        """Delete a dashboard by ID."""
        if dashboard_id in self._dashboards:
            del self._dashboards[dashboard_id]
            return True
        return False


class InMemoryUnmappedRepository(UnmappedRepositoryInterface):
    """In-memory implementation of unmapped PGN repository."""

    def __init__(self):
        """Initialize the in-memory unmapped repository."""
        self._unmapped_pgns: dict[int, UnmappedEntryModel] = {}

    async def get_unmapped_pgns(self) -> list[UnmappedEntryModel]:
        """Get all unmapped PGNs."""
        return list(self._unmapped_pgns.values())

    async def save_unmapped_pgn(self, pgn: UnmappedEntryModel) -> None:
        """Save an unmapped PGN."""
        self._unmapped_pgns[pgn.pgn] = pgn

    async def delete_unmapped_pgn(self, pgn: int) -> bool:
        """Delete an unmapped PGN."""
        if pgn in self._unmapped_pgns:
            del self._unmapped_pgns[pgn]
            return True
        return False
