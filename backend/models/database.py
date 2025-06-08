"""
Database Models Base

SQLAlchemy declarative base and common model mixins for the persistence layer.
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """
    SQLAlchemy declarative base class.

    Provides common functionality for all database models.
    """

    # Enable better repr for debugging
    def __repr__(self) -> str:
        """Return a string representation of the model."""
        attrs = []
        for column in self.__table__.columns:
            value = getattr(self, column.name, None)
            if value is not None:
                attrs.append(f"{column.name}={value!r}")
        return f"{self.__class__.__name__}({', '.join(attrs)})"


class TimestampMixin:
    """Mixin for models that need created_at and updated_at timestamps."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Record creation timestamp",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Record last update timestamp",
    )


class UUIDMixin:
    """Mixin for models that use UUID primary keys."""

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Primary key UUID",
    )


class SoftDeleteMixin:
    """Mixin for models that support soft deletion."""

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Soft deletion timestamp"
    )

    @property
    def is_deleted(self) -> bool:
        """Check if the record is soft deleted."""
        return self.deleted_at is not None

    def soft_delete(self) -> None:
        """Mark the record as soft deleted."""
        self.deleted_at = datetime.utcnow()

    def restore(self) -> None:
        """Restore a soft deleted record."""
        self.deleted_at = None


class BaseModel(Base, TimestampMixin, UUIDMixin):
    """
    Base model class with common fields.

    Includes:
    - UUID primary key
    - Created/updated timestamps
    - Common utilities
    """

    __abstract__ = True

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the model to a dictionary.

        Returns:
            Dictionary representation of the model
        """
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime | uuid.UUID):
                result[column.name] = str(value)
            else:
                result[column.name] = value
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BaseModel":
        """
        Create a model instance from a dictionary.

        Args:
            data: Dictionary with model data

        Returns:
            Model instance
        """
        # Filter out keys that don't correspond to model columns
        valid_keys = {column.name for column in cls.__table__.columns}
        filtered_data = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered_data)


class ConfigurationModel(BaseModel):
    """
    Model for storing application configuration data.

    Used for user preferences, feature toggles, and other configurable settings.
    """

    __tablename__ = "configurations"

    namespace: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="Configuration namespace"
    )
    key: Mapped[str] = mapped_column(String(255), nullable=False, comment="Configuration key")
    value: Mapped[str] = mapped_column(
        String(4000), nullable=False, comment="Configuration value (JSON string)"
    )
    description: Mapped[str | None] = mapped_column(
        String(500), nullable=True, comment="Human-readable description"
    )
    category: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Configuration category for grouping"
    )

    __table_args__ = (UniqueConstraint("namespace", "key", name="uq_configuration_namespace_key"),)


class BackupMetadata(BaseModel):
    """
    Model for tracking database backup metadata.

    Stores information about backup files for management and cleanup.
    """

    __tablename__ = "backup_metadata"

    file_path: Mapped[str] = mapped_column(
        String(500), nullable=False, comment="Full path to backup file"
    )
    file_size_bytes: Mapped[int] = mapped_column(
        nullable=False, comment="Backup file size in bytes"
    )
    database_name: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Name of the backed up database"
    )
    backup_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="manual",
        comment="Type of backup (manual, automatic, scheduled)",
    )
    checksum: Mapped[str | None] = mapped_column(
        String(64), nullable=True, comment="SHA-256 checksum of backup file"
    )


class DashboardModel(BaseModel):
    """
    Model for dashboard configurations.

    Stores dashboard layouts, settings, and default status.
    """

    __tablename__ = "dashboards"

    name: Mapped[str] = mapped_column(String(255), nullable=False, comment="Dashboard name")
    config: Mapped[str] = mapped_column(
        String(10000), nullable=False, comment="Dashboard configuration (JSON string)"
    )
    is_default: Mapped[bool] = mapped_column(
        nullable=False, default=False, comment="Whether this is the default dashboard"
    )
    description: Mapped[str | None] = mapped_column(
        String(500), nullable=True, comment="Dashboard description"
    )
