"""
Entities API Router

FastAPI router for managing and interacting with RV-C entities.
This router delegates business logic to the EntityService.

Routes:
- GET /entities: List all entities with optional filtering
- GET /entities/ids: List all entity IDs
- GET /entities/{entity_id}: Get specific entity details
- GET /entities/{entity_id}/history: Get entity history
- POST /entities/{entity_id}/control: Control entity state
- GET /unmapped: List unmapped DGN/instance pairs
- GET /unknown-pgns: List unknown PGN entries
- GET /metadata: Get metadata about entity types and capabilities
"""

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from backend.core.dependencies import get_entity_service, get_feature_manager_from_request
from backend.models.entity import ControlCommand, ControlEntityResponse
from backend.models.unmapped import UnknownPGNEntry, UnmappedEntryModel

logger = logging.getLogger(__name__)

# Create the router
router = APIRouter(prefix="/api", tags=["entities"])


def _check_rvc_feature_enabled(request: Request) -> None:
    """Check if RVC feature is enabled, raise 404 if disabled."""
    feature_manager = get_feature_manager_from_request(request)
    if not feature_manager.is_enabled("rvc"):
        raise HTTPException(status_code=404, detail="rvc feature is disabled")


@router.get(
    "/entities",
    response_model=dict[str, dict[str, Any]],
    summary="List entities",
    description="Return all entities, optionally filtered by device_type and/or area.",
    response_description="Dictionary of entities matching the filter criteria",
)
async def list_entities(
    request: Request,
    device_type: str | None = Query(None, description="Filter by entity device_type"),
    area: str | None = Query(None, description="Filter by entity suggested_area"),
    entity_service: Annotated[Any, Depends(get_entity_service)] = None,
) -> dict[str, dict[str, Any]]:
    """
    Return all entities, optionally filtered by device_type and/or area.

    This endpoint provides access to all known RV-C entities in the system,
    with optional filtering capabilities to narrow down results.
    """
    _check_rvc_feature_enabled(request)
    return await entity_service.list_entities(device_type=device_type, area=area)


@router.get(
    "/entities/ids",
    response_model=list[str],
    summary="List entity IDs",
    description="Return all known entity IDs.",
    response_description="List of all entity IDs in the system",
)
async def list_entity_ids(
    request: Request,
    entity_service: Annotated[Any, Depends(get_entity_service)] = None,
) -> list[str]:
    """Return all known entity IDs."""
    _check_rvc_feature_enabled(request)
    return await entity_service.list_entity_ids()


@router.get(
    "/entities/{entity_id}",
    response_model=dict[str, Any],
    summary="Get entity details",
    description="Return the latest value for one entity.",
    response_description="The entity object with current state",
)
async def get_entity(
    request: Request,
    entity_id: str,
    entity_service: Annotated[Any, Depends(get_entity_service)] = None,
) -> dict[str, Any]:
    """
    Return the latest value for one entity.

    Args:
        entity_id: The ID of the entity to retrieve

    Raises:
        HTTPException: If the entity is not found

    Returns:
        The entity object with current state
    """
    _check_rvc_feature_enabled(request)
    entity = await entity_service.get_entity(entity_id)

    if entity is None:
        raise HTTPException(status_code=404, detail=f"Entity '{entity_id}' not found")

    return entity


@router.get(
    "/entities/{entity_id}/history",
    response_model=list[dict[str, Any]],
    summary="Get entity history",
    description="Return the history of state changes for a specific entity.",
    response_description="List of historical state entries",
)
async def get_entity_history(
    request: Request,
    entity_id: str,
    limit: int | None = Query(None, description="Maximum number of history entries to return"),
    since: float | None = Query(None, description="Unix timestamp to filter history from"),
    entity_service: Annotated[Any, Depends(get_entity_service)] = None,
) -> list[dict[str, Any]]:
    """
    Return the history of state changes for a specific entity.

    Args:
        entity_id: The ID of the entity
        limit: Maximum number of history entries to return
        since: Unix timestamp to filter history from

    Raises:
        HTTPException: If the entity is not found

    Returns:
        List of historical state entries
    """
    _check_rvc_feature_enabled(request)
    history_data = await entity_service.get_entity_history(entity_id, limit=limit, since=since)

    if history_data is None:
        raise HTTPException(status_code=404, detail=f"Entity '{entity_id}' not found")

    return history_data


@router.post(
    "/entities/{entity_id}/control",
    response_model=ControlEntityResponse,
    summary="Control entity",
    description="Send a control command to an entity.",
    response_description="Control command response with execution details",
)
async def control_entity(
    request: Request,
    entity_id: str,
    command: ControlCommand,
    entity_service: Annotated[Any, Depends(get_entity_service)] = None,
) -> ControlEntityResponse:
    """
    Send a control command to an entity.

    This endpoint allows controlling RV-C entities by sending appropriate
    CAN bus commands. The command is validated and executed if the entity
    supports the requested operation.

    Args:
        entity_id: The ID of the entity to control
        command: The control command to execute

    Raises:
        HTTPException: If the entity is not found or command is invalid

    Returns:
        Control command response with execution details
    """
    _check_rvc_feature_enabled(request)
    result = await entity_service.control_entity(entity_id, command)
    return result


@router.get(
    "/unmapped",
    response_model=dict[str, UnmappedEntryModel],
    summary="List unmapped entries",
    description="Return DGN/instance pairs observed on the CAN bus but not mapped to entities.",
    response_description="Dictionary of unmapped DGN/instance pairs",
)
async def get_unmapped_entries(
    request: Request,
    entity_service: Annotated[Any, Depends(get_entity_service)] = None,
) -> dict[str, UnmappedEntryModel]:
    """
    Return DGN/instance pairs observed on the CAN bus but not mapped to entities.

    This endpoint provides visibility into RV-C messages that are being
    received but don't have corresponding entity mappings in the configuration.
    """
    _check_rvc_feature_enabled(request)
    return await entity_service.get_unmapped_entries()


@router.get(
    "/unknown-pgns",
    response_model=dict[str, UnknownPGNEntry],
    summary="List unknown PGNs",
    description="Return PGN entries that were observed but not recognized.",
    response_description="Dictionary of unknown PGN entries",
)
async def get_unknown_pgns(
    request: Request,
    entity_service: Annotated[Any, Depends(get_entity_service)] = None,
) -> dict[str, UnknownPGNEntry]:
    """
    Return PGN entries that were observed but not recognized.

    This endpoint provides visibility into CAN bus messages with PGNs
    that are not defined in the RV-C specification or configuration.
    """
    _check_rvc_feature_enabled(request)
    return await entity_service.get_unknown_pgns()


@router.get(
    "/metadata",
    response_model=dict[str, list[str]],
    summary="Get entity metadata",
    description="Return metadata about available entity types, areas, and capabilities.",
    response_description="Dictionary containing metadata about the entity system",
)
async def get_metadata(
    request: Request,
    entity_service: Annotated[Any, Depends(get_entity_service)] = None,
) -> dict[str, list[str]]:
    """
    Return metadata about available entity types, areas, and capabilities.

    This endpoint provides information about the entity system structure,
    including available device types, areas, and supported commands.
    """
    _check_rvc_feature_enabled(request)
    return await entity_service.get_metadata()


@router.get(
    "/missing-dgns",
    response_model=dict[int, dict],
    summary="List missing DGNs",
    description="Return DGNs that were encountered during decoding but not found in the specification.",
    response_description="Dictionary of missing DGN entries with encounter metadata",
)
async def get_missing_dgns_endpoint(request: Request) -> dict[int, dict]:
    """
    Return DGNs that were encountered during decoding but not found in the specification.

    This endpoint provides visibility into DGNs that are being received on the CAN bus
    but are not defined in the RV-C specification. This helps identify potential
    gaps in the protocol implementation or new DGNs that need to be added.

    Returns:
        Dictionary mapping DGN IDs to metadata including:
        - dgn_id: The numeric DGN ID
        - dgn_hex: Hexadecimal representation
        - first_seen: Timestamp when first encountered
        - encounter_count: Number of times encountered
        - can_ids: Set of CAN IDs where this DGN was seen
        - contexts: Set of contexts where this DGN was encountered
    """
    _check_rvc_feature_enabled(request)

    try:
        # Import here to avoid circular imports and unused import warnings
        from backend.integrations.rvc.decode import get_missing_dgns

        missing_dgns = get_missing_dgns()

        # Convert sets to lists for JSON serialization
        for dgn_data in missing_dgns.values():
            if "can_ids" in dgn_data:
                dgn_data["can_ids"] = list(dgn_data["can_ids"])
            if "contexts" in dgn_data:
                dgn_data["contexts"] = list(dgn_data["contexts"])

        return missing_dgns

    except ImportError as e:
        raise HTTPException(status_code=500, detail=f"RVC decode module unavailable: {e}") from e
