"""
Entity Manager for the rvc2api backend.

This module provides a unified manager for entities that combines configuration
and runtime state management. It replaces the dual-dictionary approach with a
single entity registry that serves as the source of truth.
"""

import logging
import time
from typing import Any

from backend.models.entity_model import Entity, EntityConfig

logger = logging.getLogger(__name__)


class EntityManager:
    """
    Protocol-aware Entity Manager that provides unified entity management.

    This class replaces the separate entity_id_lookup and state dictionaries
    with a single registry of Entity objects that each maintain their own
    configuration and state. It includes protocol ownership and deduplication.
    """

    def __init__(self):
        """Initialize the entity manager."""
        self.entities: dict[str, Entity] = {}
        self.unmapped_entries: dict[str, Any] = {}
        self.unknown_pgns: dict[str, Any] = {}
        self.light_entity_ids: list[str] = []
        self.device_lookup: dict[str, Any] = {}
        self.status_lookup: dict[str, Any] = {}
        # Protocol-specific tracking
        self.protocol_entities: dict[str, set[str]] = {}  # protocol -> entity_ids
        self.physical_id_map: dict[str, str] = {}  # physical_id -> entity_id

    def register_entity(
        self, entity_id: str, config: EntityConfig, protocol: str = "rvc"
    ) -> Entity:
        """
        Register a new entity with the manager, handling protocol ownership and deduplication.

        Args:
            entity_id: Unique identifier for the entity
            config: Entity configuration
            protocol: Protocol attempting to register this entity

        Returns:
            The registered Entity instance (may be existing if physical_id matches)
        """
        # Set protocol in config if not specified
        if "protocol" not in config:
            config["protocol"] = protocol

        # Generate physical_id if not provided
        if "physical_id" not in config:
            # Use entity_id as fallback physical_id
            config["physical_id"] = entity_id

        physical_id = config["physical_id"]

        # Check for existing entity with same physical_id (deduplication)
        if physical_id in self.physical_id_map:
            existing_entity_id = self.physical_id_map[physical_id]
            existing_entity = self.entities[existing_entity_id]

            logger.info(
                f"Entity duplication detected: {entity_id} -> existing {existing_entity_id} (physical_id: {physical_id})"
            )

            # Add as secondary protocol if not already present
            current_protocol = existing_entity.config.get("protocol", "rvc")
            secondary_protocols = existing_entity.config.get("secondary_protocols", [])

            if protocol != current_protocol and protocol not in secondary_protocols:
                secondary_protocols.append(protocol)
                existing_entity.config["secondary_protocols"] = secondary_protocols
                logger.info(f"Added {protocol} as secondary protocol for {existing_entity_id}")

            # Track protocol ownership
            if protocol not in self.protocol_entities:
                self.protocol_entities[protocol] = set()
            self.protocol_entities[protocol].add(existing_entity_id)

            return existing_entity

        # Register new entity
        entity = Entity(entity_id=entity_id, config=config)
        self.entities[entity_id] = entity
        self.physical_id_map[physical_id] = entity_id

        # Track protocol ownership
        entity_protocol = config.get("protocol", protocol)
        if entity_protocol not in self.protocol_entities:
            self.protocol_entities[entity_protocol] = set()
        self.protocol_entities[entity_protocol].add(entity_id)

        # Track light entities for convenience
        if config.get("device_type") == "light":
            self.light_entity_ids.append(entity_id)

        logger.debug(
            f"Registered new entity: {entity_id} (protocol: {entity_protocol}, physical_id: {physical_id})"
        )
        return entity

    def get_entity(self, entity_id: str) -> Entity | None:
        """
        Get an entity by its ID.

        Args:
            entity_id: The ID of the entity to retrieve

        Returns:
            The Entity if found, None otherwise
        """
        return self.entities.get(entity_id)

    def get_all_entities(self) -> dict[str, Entity]:
        """
        Get all registered entities.

        Returns:
            Dictionary of entity_id to Entity
        """
        return self.entities

    def get_entity_ids(self) -> list[str]:
        """
        Get all entity IDs.

        Returns:
            List of entity IDs
        """
        return list(self.entities.keys())

    def filter_entities(
        self, device_type: str | None = None, area: str | None = None, protocol: str | None = None
    ) -> dict[str, Entity]:
        """
        Get entities filtered by device type, area, and/or protocol.

        Args:
            device_type: Optional device type to filter by
            area: Optional area to filter by
            protocol: Optional protocol to filter by (primary or secondary)

        Returns:
            Dictionary of filtered entities
        """
        result = {}
        for entity_id, entity in self.entities.items():
            matches = True

            if device_type is not None and entity.config.get("device_type") != device_type:
                matches = False

            if area is not None and entity.config.get("suggested_area") != area:
                matches = False

            if protocol is not None:
                entity_protocol = entity.config.get("protocol", "rvc")
                secondary_protocols = entity.config.get("secondary_protocols", [])
                if protocol != entity_protocol and protocol not in secondary_protocols:
                    matches = False

            if matches:
                result[entity_id] = entity

        return result

    def get_entities_by_protocol(self, protocol: str) -> dict[str, Entity]:
        """
        Get all entities owned or accessible by a specific protocol.

        Args:
            protocol: Protocol name to filter by

        Returns:
            Dictionary of entities accessible to the protocol
        """
        return self.filter_entities(protocol=protocol)

    def get_protocol_summary(self) -> dict[str, Any]:
        """
        Get summary of entity distribution across protocols.

        Returns:
            Dictionary with protocol entity counts and statistics
        """
        summary = {
            "total_entities": len(self.entities),
            "total_physical_devices": len(self.physical_id_map),
            "protocols": {},
        }

        for protocol, entity_ids in self.protocol_entities.items():
            entities = [self.entities[eid] for eid in entity_ids if eid in self.entities]
            summary["protocols"][protocol] = {
                "entity_count": len(entity_ids),
                "device_types": list({e.config.get("device_type", "unknown") for e in entities}),
                "sample_entities": list(entity_ids)[:5],  # First 5 for preview
            }

        return summary

    def update_entity_state(self, entity_id: str, new_state: dict[str, Any]) -> Entity | None:
        """
        Update an entity's state.

        Args:
            entity_id: ID of the entity to update
            new_state: New state data to apply

        Returns:
            The updated Entity if found, None otherwise
        """
        entity = self.get_entity(entity_id)
        if entity:
            entity.update_state(new_state)
            return entity
        return None

    def bulk_load_entities(self, entity_configs: dict[str, EntityConfig]) -> None:
        """
        Bulk load entities from configuration.

        Args:
            entity_configs: Dictionary of entity_id to EntityConfig
        """
        logger.info(f"Bulk loading {len(entity_configs)} entities")
        self.entities = {}
        self.light_entity_ids = []

        for entity_id, config in entity_configs.items():
            self.register_entity(entity_id, config)

        logger.info(f"Loaded {len(self.entities)} entities ({len(self.light_entity_ids)} lights)")

    def get_light_entity_ids(self) -> list[str]:
        """
        Get IDs of all light entities.

        Returns:
            List of light entity IDs
        """
        return self.light_entity_ids

    def preseed_light_states(
        self, decode_payload_func: Any, device_mapping: dict[str, Any]
    ) -> None:
        """
        Initialize states for all light entities.

        Args:
            decode_payload_func: Function to decode CAN payloads
            device_mapping: Device mapping configuration
        """
        now = time.time()
        logger.info(f"Pre-seeding states for {len(self.light_entity_ids)} light entities")

        for entity_id in self.light_entity_ids:
            entity = self.get_entity(entity_id)
            if not entity:
                logger.warning(f"Pre-seeding: Entity not found: {entity_id}")
                continue

            config = entity.config
            if not config:
                logger.warning(f"Pre-seeding: Missing config for light entity ID: {entity_id}")
                continue

            # Create a payload with initial "off" state
            payload = {
                "entity_id": entity_id,
                "value": {"operating_status": "0"},
                "raw": {"operating_status": 0},
                "state": "off",
                "timestamp": now,
                "suggested_area": config.get("suggested_area", "Unknown"),
                "device_type": config.get("device_type", "light"),
                "capabilities": config.get("capabilities", []),
                "friendly_name": config.get("friendly_name"),
                "groups": config.get("groups", []),
            }

            # Update entity state
            entity.update_state(payload)

        logger.info("Finished pre-seeding light states")

    def to_api_response(self) -> dict[str, dict[str, Any]]:
        """
        Convert all entities to dictionary format for API responses.

        Returns:
            Dictionary of entity_id to state dictionary
        """
        return {entity_id: entity.to_dict() for entity_id, entity in self.entities.items()}
