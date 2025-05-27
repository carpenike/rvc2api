"""
Test data factories for generating consistent test data.

This module provides factory functions for creating test data objects
with realistic and consistent properties across all tests.
"""

import random
from datetime import UTC, datetime
from typing import Any
from unittest.mock import Mock


class EntityFactory:
    """Factory for creating entity test data."""

    @staticmethod
    def create_entity(
        entity_id: int | None = None,
        name: str | None = None,
        entity_type: str = "sensor",
        value: float | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """
        Create a test entity with realistic properties.

        Args:
            entity_id: Unique identifier for the entity
            name: Human-readable name for the entity
            entity_type: Type of entity (sensor, actuator, controller)
            value: Current value of the entity
            **kwargs: Additional properties to override defaults

        Returns:
            Dictionary representing an entity
        """
        entity_id = entity_id or random.randint(1, 1000)
        name = name or f"Test {entity_type.title()} {entity_id}"
        value = value if value is not None else round(random.uniform(0, 100), 2)

        entity = {
            "id": entity_id,
            "name": name,
            "type": entity_type,
            "value": value,
            "unit": _get_unit_for_type(entity_type),
            "timestamp": datetime.now(UTC).isoformat(),
            "properties": {
                "min_value": 0,
                "max_value": 200,
                "precision": 1,
                "source": "test",
            },
            "metadata": {
                "created_at": datetime.now(UTC).isoformat(),
                "updated_at": datetime.now(UTC).isoformat(),
                "version": 1,
            },
        }

        # Override with any provided kwargs
        entity.update(kwargs)
        return entity

    @staticmethod
    def create_multiple_entities(count: int = 5, **kwargs) -> list[dict[str, Any]]:
        """
        Create multiple test entities.

        Args:
            count: Number of entities to create
            **kwargs: Properties to apply to all entities

        Returns:
            List of entity dictionaries
        """
        return [EntityFactory.create_entity(entity_id=i + 1, **kwargs) for i in range(count)]

    @staticmethod
    def create_temperature_sensor(
        entity_id: int | None = None, temperature: float | None = None
    ) -> dict[str, Any]:
        """Create a temperature sensor entity."""
        temperature = temperature if temperature is not None else round(random.uniform(-10, 50), 1)
        return EntityFactory.create_entity(
            entity_id=entity_id,
            entity_type="temperature_sensor",
            value=temperature,
            unit="°C",
            properties={
                "min_value": -40,
                "max_value": 80,
                "precision": 0.1,
                "sensor_type": "digital",
            },
        )

    @staticmethod
    def create_pressure_sensor(
        entity_id: int | None = None, pressure: float | None = None
    ) -> dict[str, Any]:
        """Create a pressure sensor entity."""
        pressure = pressure if pressure is not None else round(random.uniform(900, 1100), 2)
        return EntityFactory.create_entity(
            entity_id=entity_id,
            entity_type="pressure_sensor",
            value=pressure,
            unit="hPa",
            properties={
                "min_value": 800,
                "max_value": 1200,
                "precision": 0.01,
                "sensor_type": "analog",
            },
        )

    @staticmethod
    def create_light_controller(
        entity_id: int | None = None, brightness: float | None = None
    ) -> dict[str, Any]:
        """Create a light controller entity."""
        brightness = brightness if brightness is not None else random.randint(0, 100)
        return EntityFactory.create_entity(
            entity_id=entity_id,
            entity_type="light_controller",
            value=brightness,
            unit="%",
            properties={
                "min_value": 0,
                "max_value": 100,
                "precision": 1,
                "controllable": True,
                "dimmable": True,
            },
        )


class CANMessageFactory:
    """Factory for creating CAN message test data."""

    @staticmethod
    def create_can_message(
        arbitration_id: int | None = None,
        data: list[int] | None = None,
        is_extended_id: bool = True,
        timestamp: float | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """
        Create a test CAN message.

        Args:
            arbitration_id: CAN message ID
            data: Message data bytes
            is_extended_id: Whether to use extended frame format
            timestamp: Message timestamp
            **kwargs: Additional properties

        Returns:
            Dictionary representing a CAN message
        """
        arbitration_id = arbitration_id or 0x18FEF100
        data = data or [random.randint(0, 255) for _ in range(8)]
        timestamp = timestamp or datetime.now(UTC).timestamp()

        message = {
            "arbitration_id": arbitration_id,
            "data": data[:8],  # Ensure max 8 bytes
            "is_extended_id": is_extended_id,
            "timestamp": timestamp,
            "dlc": len(data[:8]),
            "channel": "vcan0",
        }

        message.update(kwargs)
        return message

    @staticmethod
    def create_rvc_message(
        dgn: int | None = None, source_address: int = 0x10, data: list[int] | None = None, **kwargs
    ) -> dict[str, Any]:
        """
        Create an RV-C protocol message.

        Args:
            dgn: Data Group Number
            source_address: Source address
            data: Message data
            **kwargs: Additional properties

        Returns:
            Dictionary representing an RV-C message
        """
        dgn = dgn or 0xFEF1  # Generic Status DGN
        arbitration_id = 0x18000000 | (dgn << 8) | source_address
        data = data or [0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08]

        return CANMessageFactory.create_can_message(
            arbitration_id=arbitration_id,
            data=data,
            dgn=dgn,
            source_address=source_address,
            protocol="rvc",
            **kwargs,
        )

    @staticmethod
    def create_multiple_messages(count: int = 10, **kwargs) -> list[dict[str, Any]]:
        """Create multiple CAN messages."""
        return [CANMessageFactory.create_can_message(**kwargs) for _ in range(count)]


class ConfigFactory:
    """Factory for creating configuration test data."""

    @staticmethod
    def create_config(
        can_interface: str = "vcan0", log_level: str = "INFO", **kwargs
    ) -> dict[str, Any]:
        """
        Create test configuration data.

        Args:
            can_interface: CAN interface name
            log_level: Logging level
            **kwargs: Additional configuration options

        Returns:
            Dictionary representing configuration
        """
        config = {
            "can_interface": can_interface,
            "log_level": log_level,
            "features": {
                "entity_discovery": True,
                "can_logging": False,
                "websocket_streaming": True,
                "rvc_decoding": True,
            },
            "thresholds": {
                "temperature_warning": 80,
                "temperature_critical": 90,
                "pressure_warning": 1050,
                "pressure_critical": 1100,
            },
            "limits": {
                "max_entities": 1000,
                "max_message_rate": 1000,
                "connection_timeout": 30,
            },
            "api": {
                "host": "localhost",
                "port": 8000,
                "cors_origins": ["*"],
                "enable_docs": True,
            },
        }

        config.update(kwargs)
        return config

    @staticmethod
    def create_feature_flags(**kwargs) -> dict[str, bool]:
        """Create feature flag configuration."""
        flags = {
            "enable_can_interface": True,
            "enable_websockets": True,
            "enable_rvc_decoding": True,
            "enable_entity_discovery": True,
            "enable_performance_monitoring": False,
            "enable_debug_logging": False,
        }

        flags.update(kwargs)
        return flags


class MockFactory:
    """Factory for creating mock objects with common configurations."""

    @staticmethod
    def create_mock_entity_service() -> Mock:
        """Create a mock EntityService with common methods."""
        mock = Mock()
        mock.get_all.return_value = EntityFactory.create_multiple_entities(3)
        mock.get_by_id.return_value = EntityFactory.create_entity()
        mock.create.return_value = EntityFactory.create_entity()
        mock.update.return_value = EntityFactory.create_entity()
        mock.delete.return_value = True
        return mock

    @staticmethod
    def create_mock_can_service() -> Mock:
        """Create a mock CANService with common methods."""
        mock = Mock()
        mock.send_message.return_value = True
        mock.receive_message.return_value = CANMessageFactory.create_can_message()
        mock.get_status.return_value = {"connected": True, "message_count": 100}
        mock.start.return_value = None
        mock.stop.return_value = None
        return mock

    @staticmethod
    def create_mock_app_state() -> Mock:
        """Create a mock AppState with common methods."""
        mock = Mock()
        mock.get_entity.return_value = EntityFactory.create_entity()
        mock.get_all_entities.return_value = EntityFactory.create_multiple_entities(5)
        mock.update_entity.return_value = None
        mock.create_entity.return_value = EntityFactory.create_entity()
        mock.delete_entity.return_value = True
        return mock


def _get_unit_for_type(entity_type: str) -> str:
    """Get appropriate unit for entity type."""
    unit_mapping = {
        "temperature_sensor": "°C",
        "pressure_sensor": "hPa",
        "humidity_sensor": "%",
        "voltage_sensor": "V",
        "current_sensor": "A",
        "light_controller": "%",
        "switch": "on/off",
        "valve": "%",
        "pump": "rpm",
        "sensor": "units",
        "actuator": "units",
        "controller": "units",
    }
    return unit_mapping.get(entity_type, "units")


# Convenience functions for quick test data creation
def quick_entity(entity_id: int = 1, **kwargs) -> dict[str, Any]:
    """Quickly create a test entity."""
    return EntityFactory.create_entity(entity_id=entity_id, **kwargs)


def quick_can_message(**kwargs) -> dict[str, Any]:
    """Quickly create a test CAN message."""
    return CANMessageFactory.create_can_message(**kwargs)


def quick_config(**kwargs) -> dict[str, Any]:
    """Quickly create test configuration."""
    return ConfigFactory.create_config(**kwargs)
