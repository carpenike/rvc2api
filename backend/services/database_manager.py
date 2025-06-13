"""
Database Manager

Enhanced database connection management with multi-backend support using SQLAlchemy 2.0.
Provides connection pooling, health checks, and migration support for the persistence layer.
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import TYPE_CHECKING, cast

from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncSession

if TYPE_CHECKING:
    from sqlalchemy.engine import Inspector

from backend.models.database import Base
from backend.services.database_engine import DatabaseEngine, DatabaseSettings

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Enhanced database manager with multi-backend support using SQLAlchemy 2.0.

    Provides a robust foundation for database operations with proper connection
    management, health monitoring, and migration support across different backends.
    """

    def __init__(
        self,
        database_settings: DatabaseSettings | None = None,
        database_path: Path | None = None,
    ):
        """
        Initialize the database manager.

        Args:
            database_settings: Database configuration settings
            database_path: Legacy parameter for SQLite path (deprecated)
        """
        # Handle legacy database_path parameter
        if database_path and database_settings is None:
            settings = DatabaseSettings()
            settings.sqlite_path = str(database_path)
            database_settings = settings

        self._engine = DatabaseEngine(database_settings)
        self._initialized = False

    @property
    def engine(self) -> DatabaseEngine:
        """Get the database engine."""
        return self._engine

    @property
    def backend(self) -> str:
        """Get the database backend type."""
        return self._engine.backend.value

    async def initialize(self) -> bool:
        """
        Initialize the database manager.

        Creates the database, runs migrations, and verifies connectivity.

        Returns:
            True if initialization successful, False otherwise
        """
        if self._initialized:
            logger.warning("Database manager already initialized")
            return True

        try:
            # Check if we're in null backend mode (no persistence)
            database_url = self._engine.settings.get_database_url()
            if database_url == "null://memory":
                logger.info("Database manager initialized in null mode - no persistence enabled")
                self._initialized = True
                return True

            # Initialize the database engine
            await self._engine.initialize()

            # Create tables if they don't exist
            await self._create_tables()

            # Verify health
            if not await self.health_check():
                logger.error("Database health check failed after initialization")
                return False

            self._initialized = True
            logger.info(f"Database manager initialized successfully with {self.backend} backend")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize database manager: {e}")
            return False

    async def _create_tables(self) -> None:
        """Create database tables using SQLAlchemy metadata."""
        # Skip table creation for null backend
        database_url = self._engine.settings.get_database_url()
        if database_url == "null://memory":
            logger.debug("Skipping table creation for null backend")
            return

        if not self._engine._engine:
            msg = "Database engine not initialized"
            raise RuntimeError(msg)

        try:
            async with self._engine._engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created/verified successfully")
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            raise

    async def health_check(self) -> bool:
        """
        Perform a health check on the database connection.

        Returns:
            True if the database is healthy, False otherwise
        """
        # During initialization, we can check health without requiring _initialized flag
        # After initialization, we check both _initialized and engine health
        if hasattr(self, '_engine') and self._engine:
            return await self._engine.health_check()

        return False

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get an async database session context manager.

        Yields:
            AsyncSession instance for database operations

        Raises:
            RuntimeError: If the manager is not initialized
        """
        if not self._initialized:
            msg = "Database manager not initialized"
            raise RuntimeError(msg)

        # Handle null backend (no persistence)
        database_url = self._engine.settings.get_database_url()
        if database_url == "null://memory":
            logger.warning("Database session requested but persistence is disabled")
            yield None  # type: ignore
            return

        # Use the engine's get_session method directly since it's already an async generator
        async for session in self._engine.get_session():
            yield session

    async def execute_raw_query(self, query: str, params: dict | None = None) -> list[dict]:
        """
        Execute a raw SQL query and return results.

        Args:
            query: SQL query string
            params: Optional query parameters

        Returns:
            List of dictionaries representing query results
        """
        # Handle null backend (no persistence)
        database_url = self._engine.settings.get_database_url()
        if database_url == "null://memory":
            logger.warning("Raw query requested but persistence is disabled")
            return []

        async with self.get_session() as session:
            result = await session.execute(text(query), params or {})
            return [dict(row._mapping) for row in result.fetchall()]

    async def get_table_info(self) -> dict[str, dict]:
        """
        Get information about database tables.

        Returns:
            Dictionary with table information
        """
        # Handle null backend (no persistence)
        database_url = self._engine.settings.get_database_url()
        if database_url == "null://memory":
            logger.warning("Table info requested but persistence is disabled")
            return {}

        table_info = {}
        async with self.get_session() as session:
            if session.bind is None:
                msg = "Database session has no bind"
                raise RuntimeError(msg)
            inspector = cast("Inspector", inspect(session.bind))

            # Get table names and columns
            table_names = inspector.get_table_names()
            for table_name in table_names:
                columns = inspector.get_columns(table_name)
                table_info[table_name] = {
                    "columns": [
                        {
                            "name": col["name"],
                            "type": str(col["type"]),
                            "nullable": col["nullable"],
                            "default": col["default"],
                        }
                        for col in columns
                    ]
                }
        return table_info

    async def cleanup(self) -> None:
        """Clean up database resources."""
        if self._initialized:
            await self._engine.cleanup()
            self._initialized = False
            logger.info("Database manager cleaned up successfully")

    async def shutdown(self) -> None:
        """Shutdown the database manager (alias for cleanup)."""
        await self.cleanup()
