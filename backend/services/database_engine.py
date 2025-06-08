"""
Database Engine and Configuration

Backend database engine configuration using SQLAlchemy 2.0+
with support for SQLite, PostgreSQL, and other backends.
"""

import logging
from collections.abc import AsyncGenerator
from enum import Enum
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import QueuePool, StaticPool, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

logger = logging.getLogger(__name__)


class DatabaseBackend(str, Enum):
    """Supported database backends."""

    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    NULL = "null"  # Special backend for no-database mode


class DatabaseSettings(BaseSettings):
    """Database configuration settings with multi-backend support."""

    model_config = SettingsConfigDict(env_prefix="COACHIQ_DATABASE__", case_sensitive=False)

    # Backend selection
    backend: DatabaseBackend = Field(
        default=DatabaseBackend.SQLITE, description="Database backend to use"
    )

    def get_effective_backend(self) -> DatabaseBackend:
        """Get the effective database backend, with dynamic null detection."""
        # Check if we're in null mode based on persistence settings
        if self.backend == DatabaseBackend.SQLITE:
            db_path = self.get_database_path()
            if db_path == ":null:":
                return DatabaseBackend.NULL
        return self.backend

    # SQLite settings - integrate with persistence system
    sqlite_path: str = Field(
        default="backend/data/coachiq.db", description="Path to SQLite database file"
    )
    sqlite_timeout: int = Field(default=30, description="SQLite connection timeout in seconds")

    # PostgreSQL settings
    postgres_host: str = Field(default="localhost", description="PostgreSQL host")
    postgres_port: int = Field(default=5432, description="PostgreSQL port")
    postgres_user: str = Field(default="rvc2api", description="PostgreSQL username")
    postgres_password: str = Field(default="", description="PostgreSQL password")
    postgres_database: str = Field(default="rvc2api", description="PostgreSQL database name")
    postgres_schema: str = Field(default="public", description="PostgreSQL schema name")

    # Connection pool settings
    pool_size: int = Field(default=5, description="Connection pool size", ge=1, le=20)
    max_overflow: int = Field(default=10, description="Maximum pool overflow", ge=0, le=50)
    pool_timeout: int = Field(default=30, description="Pool connection timeout", ge=1, le=300)
    pool_recycle: int = Field(
        default=3600, description="Pool connection recycle time in seconds", ge=300
    )

    # Performance settings
    echo_sql: bool = Field(default=False, description="Log SQL statements")
    echo_pool: bool = Field(default=False, description="Log connection pool events")

    def get_database_path(self) -> str:
        """
        Get the resolved database path using the persistence system.

        For SQLite, this will use the configured persistence data directory
        when persistence is enabled, or fall back to the default path.

        In development mode with persistence enabled, uses a development-friendly
        path in the project directory rather than system paths.

        Returns:
            Resolved database file path
        """
        if self.backend != DatabaseBackend.SQLITE:
            return self.sqlite_path

        # Get persistence settings to resolve the proper path
        try:
            from backend.core.config import get_settings

            settings = get_settings()
            persistence_settings = settings.persistence

            # Check if persistence is disabled - return null backend indication
            if not persistence_settings.enabled:
                logger.info("Persistence disabled - database operations will be skipped")
                return ":null:"

            if persistence_settings.enabled:
                # In development mode, use a development-friendly path
                if settings.is_development():
                    # Use project-relative path for development
                    dev_data_dir = Path("backend/data/persistent")
                    db_dir = dev_data_dir / "database"
                    return str(db_dir / "coachiq.db")
                else:
                    # Use the configured persistent data directory for production
                    db_dir = persistence_settings.get_database_dir()
                    return str(db_dir / "coachiq.db")
        except Exception:
            # Fall back to configured path if persistence system is unavailable
            pass

        return self.sqlite_path

    @field_validator("postgres_password", mode="before")
    @classmethod
    def encode_password(cls, v: str) -> str:
        """URL-encode the password to handle special characters."""
        return quote_plus(v) if v else v

    def get_database_url(self) -> str:
        """
        Get the database URL for the configured backend.

        Returns:
            Database URL string for SQLAlchemy
        """
        if self.backend == DatabaseBackend.SQLITE:
            db_path = self.get_database_path()

            # Handle null backend for no-persistence mode
            if db_path == ":null:":
                return "null://memory"

            return f"sqlite+aiosqlite:///{db_path}"

        elif self.backend == DatabaseBackend.POSTGRESQL:
            return (
                f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
                f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_database}"
            )

        elif self.backend == DatabaseBackend.MYSQL:
            # Note: Would need aiomysql dependency
            return (
                f"mysql+aiomysql://{self.postgres_user}:{self.postgres_password}"
                f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_database}"
            )

        elif self.backend == DatabaseBackend.NULL:
            return "null://memory"

        else:
            raise ValueError(f"Unsupported database backend: {self.backend}")

    def get_engine_kwargs(self) -> dict[str, Any]:
        """
        Get SQLAlchemy engine configuration for the backend.

        Returns:
            Dictionary of engine configuration options
        """
        base_kwargs: dict[str, Any] = {
            "echo": self.echo_sql,
            "echo_pool": self.echo_pool,
        }

        if self.backend == DatabaseBackend.SQLITE:
            # SQLite-specific configuration
            base_kwargs.update(
                {
                    "poolclass": StaticPool,
                    "connect_args": {
                        "check_same_thread": False,
                        "timeout": self.sqlite_timeout,
                    },
                }
            )
        elif self.backend == DatabaseBackend.POSTGRESQL:
            # PostgreSQL-specific configuration
            base_kwargs.update(
                {
                    "poolclass": QueuePool,
                    "pool_size": self.pool_size,
                    "max_overflow": self.max_overflow,
                    "pool_timeout": self.pool_timeout,
                    "pool_recycle": self.pool_recycle,
                    "connect_args": {
                        "server_settings": {
                            "search_path": self.postgres_schema,
                            "timezone": "UTC",
                        }
                    },
                }
            )
        elif self.backend == DatabaseBackend.MYSQL:
            # MySQL-specific configuration
            base_kwargs.update(
                {
                    "poolclass": QueuePool,
                    "pool_size": self.pool_size,
                    "max_overflow": self.max_overflow,
                    "pool_timeout": self.pool_timeout,
                    "pool_recycle": self.pool_recycle,
                }
            )

        return base_kwargs


class DatabaseEngine:
    """
    Multi-backend database engine manager using SQLAlchemy 2.0.

    Provides a unified interface for database operations across different
    backends with proper connection pooling and session management.
    """

    def __init__(self, settings: DatabaseSettings | None = None):
        """
        Initialize the database engine.

        Args:
            settings: Database configuration settings
        """
        self._settings = settings or DatabaseSettings()
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None

    async def _ensure_sqlite_directory(self) -> None:
        """Ensure the SQLite database directory exists."""
        db_path = Path(self._settings.get_database_path())
        db_dir = db_path.parent

        if not db_dir.exists():
            logger.info(f"Creating database directory: {db_dir}")
            db_dir.mkdir(parents=True, exist_ok=True)

    @property
    def settings(self) -> DatabaseSettings:
        """Get database settings."""
        return self._settings

    @property
    def backend(self) -> DatabaseBackend:
        """Get the configured database backend."""
        return self._settings.get_effective_backend()

    async def initialize(self) -> None:
        """Initialize the database engine and session factory."""
        if self._engine is not None:
            logger.warning("Database engine already initialized")
            return

        try:
            database_url = self._settings.get_database_url()

            # Check for null backend (no persistence)
            if database_url == "null://memory":
                logger.info("Persistence disabled - skipping database engine initialization")
                return

            # Ensure database directory exists for SQLite
            if self._settings.backend == DatabaseBackend.SQLITE:
                await self._ensure_sqlite_directory()

            engine_kwargs = self._settings.get_engine_kwargs()

            logger.info(
                f"Initializing database engine for {self._settings.backend.value} "
                f"with URL: {database_url.split('://', 1)[0]}://***"
            )

            self._engine = create_async_engine(database_url, **engine_kwargs)

            self._session_factory = async_sessionmaker(
                bind=self._engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=True,
                autocommit=False,
            )

            # Test the connection
            await self.health_check()

            logger.info(f"Database engine initialized successfully for {self._settings.backend}")

        except Exception as e:
            logger.error(f"Failed to initialize database engine: {e}")
            raise

    async def health_check(self) -> bool:
        """
        Perform a health check on the database connection.

        Returns:
            True if the database is healthy, False otherwise
        """
        # Handle null backend (no persistence)
        database_url = self._settings.get_database_url()
        if database_url == "null://memory":
            return True

        if not self._engine:
            return False

        try:
            async with self._engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get an async database session.

        Yields:
            AsyncSession instance for database operations

        Raises:
            RuntimeError: If the engine is not initialized
        """
        # Handle null backend (no persistence)
        database_url = self._settings.get_database_url()
        if database_url == "null://memory":
            logger.warning("Database session requested but persistence is disabled")
            yield None  # type: ignore
            return

        if not self._session_factory:
            raise RuntimeError("Database engine not initialized")

        async with self._session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def close(self) -> None:
        """Close the database engine and all connections."""
        if self._engine:
            logger.info("Closing database engine")
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None

    async def cleanup(self) -> None:
        """Cleanup database resources (alias for close)."""
        await self.close()

    def get_sync_url(self) -> str:
        """
        Get the synchronous database URL for migrations (Alembic).

        Returns:
            Synchronous database URL string
        """
        async_url = self._settings.get_database_url()

        # Handle null backend (no persistence)
        if async_url == "null://memory":
            return "null://memory"

        # Convert async URLs to sync URLs for Alembic
        if "sqlite+aiosqlite" in async_url:
            return async_url.replace("sqlite+aiosqlite", "sqlite")
        elif "postgresql+asyncpg" in async_url:
            return async_url.replace("postgresql+asyncpg", "postgresql+psycopg2")
        elif "mysql+aiomysql" in async_url:
            return async_url.replace("mysql+aiomysql", "mysql+pymysql")

        return async_url


class NullDatabaseEngine:
    """
    Null database engine for memory-only operation.

    This engine provides the same interface as DatabaseEngine but performs
    no actual database operations, allowing the application to run without
    any persistent storage when persistence is disabled.
    """

    def __init__(self, settings: "DatabaseSettings | None" = None):
        """Initialize the null database engine."""
        self._settings = settings or DatabaseSettings()
        self._settings.backend = DatabaseBackend.NULL

    @property
    def settings(self) -> "DatabaseSettings":
        """Get database settings."""
        return self._settings

    @property
    def backend(self) -> DatabaseBackend:
        """Get the configured database backend."""
        return DatabaseBackend.NULL

    async def initialize(self) -> None:
        """No-op initialization for null engine."""
        logger.info("Null database engine initialized - no persistence enabled")

    async def health_check(self) -> bool:
        """Always return healthy for null engine."""
        return True

    async def get_session(self) -> AsyncGenerator[None, None]:
        """Null session that yields nothing."""
        logger.warning("Database session requested but persistence is disabled")
        yield None

    async def close(self) -> None:
        """No-op close for null engine."""
        logger.debug("Null database engine closed")

    async def cleanup(self) -> None:
        """No-op cleanup for null engine."""
        await self.close()

    def get_sync_url(self) -> str:
        """Return a placeholder URL for null engine."""
        return "null://memory"


# Global database engine instance
_db_engine: DatabaseEngine | NullDatabaseEngine | None = None


def get_database_engine() -> DatabaseEngine | NullDatabaseEngine:
    """
    Get the global database engine instance.

    Returns:
        DatabaseEngine or NullDatabaseEngine instance

    Raises:
        RuntimeError: If the engine is not initialized
    """
    global _db_engine
    if _db_engine is None:
        raise RuntimeError("Database engine not initialized")
    return _db_engine


async def initialize_database_engine(
    settings: DatabaseSettings | None = None,
) -> DatabaseEngine | NullDatabaseEngine:
    """
    Initialize the global database engine.

    Args:
        settings: Database configuration settings

    Returns:
        Initialized DatabaseEngine instance (or NullDatabaseEngine for no-persistence mode)
    """
    global _db_engine

    # Create settings if not provided
    if settings is None:
        settings = DatabaseSettings()

    # Check if we should use null backend (no persistence)
    if settings.get_effective_backend() == DatabaseBackend.NULL:
        logger.info("Initializing null database engine - no persistence enabled")
        engine = NullDatabaseEngine(settings)
    else:
        engine = DatabaseEngine(settings)

    _db_engine = engine
    await engine.initialize()
    return engine


async def close_database_engine() -> None:
    """Close the global database engine."""
    global _db_engine
    if _db_engine:
        await _db_engine.close()
        _db_engine = None
