# Revised Configuration Management System Specification

- **Feature Name:** Configuration Management Enhancement
- **Status:** Revised Plan
- **Date:** 2024-12-07
- **Author:** Claude Code Analysis
- **Supersedes:** Original config-mgmt-consolidation.md

**Summary:**
Enhance the existing robust Pydantic Settings and Feature Manager architecture with configuration APIs, CAN interface mapping, and runtime editability while maintaining the current in-memory, service-oriented design patterns.

---

## Architecture Philosophy

### Design Principles

1. **Leverage Existing Excellence**: Build on proven Pydantic Settings + Feature Manager foundation
2. **In-Memory Consistency**: Maintain current in-memory state management patterns
3. **Service-Oriented**: Follow existing service architecture patterns
4. **Feature-Driven**: Use feature manager for configuration management capabilities
5. **Minimal Disruption**: Enhance rather than replace existing systems

### Current Architecture Strengths

✅ **Pydantic Settings System**
- Type-safe configuration with validation
- Environment variable support with `COACHIQ_` prefix
- Nested configuration classes (Server, CORS, CAN, etc.)
- Resource discovery with Nix compatibility

✅ **Feature Manager System**
- YAML-driven feature definitions
- Dependency resolution with topological sort
- Startup/shutdown lifecycle management
- Runtime configuration overrides

✅ **Service Architecture**
- Clean dependency injection via FastAPI state
- Service-oriented design with clear separation
- Request-based dependency access

✅ **In-Memory State Management**
- EntityManager for unified state
- AppState for application-wide data
- WebSocket integration for real-time updates

---

## Enhanced Configuration System

### Phase 1: CAN Interface Mapping Service

Implement logical CAN interface mapping as a new service following existing patterns.

#### New Service: `CANInterfaceService`

**Location:** `backend/services/can_interface_service.py`

```python
from typing import Dict, Any
import logging
from backend.core.config import get_settings

logger = logging.getLogger(__name__)

class CANInterfaceService:
    """Service for managing CAN interface mappings and resolution."""

    def __init__(self):
        self.settings = get_settings()
        self._interface_mappings = self._load_interface_mappings()

    def _load_interface_mappings(self) -> Dict[str, str]:
        """Load interface mappings from settings."""
        return self.settings.can.interface_mappings.copy()

    def resolve_interface(self, logical_name: str) -> str:
        """
        Resolve logical interface name to physical interface.

        Args:
            logical_name: Logical interface name (e.g., 'house', 'chassis')

        Returns:
            Physical interface name (e.g., 'can0', 'can1')

        Raises:
            ValueError: If logical interface is not mapped
        """
        # If it's already physical, return as-is
        if logical_name.startswith(('can', 'vcan')):
            return logical_name

        if logical_name in self._interface_mappings:
            return self._interface_mappings[logical_name]

        raise ValueError(f"Unknown logical CAN interface: {logical_name}")

    def get_all_mappings(self) -> Dict[str, str]:
        """Get all current interface mappings."""
        return self._interface_mappings.copy()

    def update_mapping(self, logical_name: str, physical_interface: str) -> None:
        """Update interface mapping (runtime only)."""
        self._interface_mappings[logical_name] = physical_interface
        logger.info(f"Updated interface mapping: {logical_name} -> {physical_interface}")

    def validate_mapping(self, mappings: Dict[str, str]) -> Dict[str, Any]:
        """Validate interface mappings."""
        issues = []

        # Check for duplicate physical interfaces
        physical_interfaces = list(mappings.values())
        if len(physical_interfaces) != len(set(physical_interfaces)):
            issues.append("Duplicate physical interfaces detected")

        # Validate physical interface names
        for logical, physical in mappings.items():
            if not physical.startswith(('can', 'vcan')):
                issues.append(f"Invalid physical interface: {physical}")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "mapping": mappings
        }
```

#### Enhanced CANSettings

**Location:** `backend/core/config.py` (extend existing)

```python
class CANSettings(BaseSettings):
    """Enhanced CAN bus configuration with interface mapping."""

    model_config = SettingsConfigDict(env_prefix="COACHIQ_CAN__", case_sensitive=False)

    # Existing fields
    interface: str = Field(default="can0", description="Primary CAN interface")
    interfaces: list[str] = Field(default=["can0"], description="CAN interface names")
    bustype: str = Field(default="socketcan", description="CAN bus type")
    bitrate: int = Field(default=500000, description="CAN bus bitrate")

    # New interface mapping
    interface_mappings: dict[str, str] = Field(
        default={"house": "can0", "chassis": "can1"},
        description="Logical to physical interface mapping"
    )

    @field_validator("interface_mappings", mode="before")
    @classmethod
    def parse_interface_mappings(cls, v):
        """Parse interface mappings from environment variable."""
        if isinstance(v, str):
            # Support format: "house:can0,chassis:can1"
            mappings = {}
            for pair in v.split(","):
                if ":" in pair:
                    logical, physical = pair.split(":", 1)
                    mappings[logical.strip()] = physical.strip()
            return mappings
        return v
```

#### Feature Registration

**Location:** `backend/services/feature_flags.yaml` (extend existing)

```yaml
# Add to existing feature_flags.yaml
can_interface_mapping:
  enabled: true
  core: false
  depends_on: [can_interface]
  description: "Logical CAN interface mapping service for portable coach configurations"
```

### Phase 2: Configuration API Enhancement

Add configuration endpoints that work with existing settings and feature systems.

#### Configuration Router

**Location:** `backend/api/routers/config.py` (new file)

```python
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from backend.core.config import get_settings
from backend.core.dependencies import get_can_interface_service, get_feature_manager_from_request

router = APIRouter(prefix="/config", tags=["configuration"])

@router.get("/settings")
async def get_settings_overview():
    """
    Get current application settings with source information.

    Returns configuration values showing which come from environment
    variables vs defaults, without exposing sensitive information.
    """
    settings = get_settings()

    # Build response with source tracking
    config_dict = settings.get_config_dict(hide_secrets=True)

    # Add source information for each setting
    # Environment variables are marked as immutable
    response = {
        "sections": {},
        "metadata": {
            "environment": settings.environment,
            "debug": settings.debug,
            "source_priority": ["environment", "default"]
        }
    }

    for section_name, section_data in config_dict.items():
        if isinstance(section_data, dict):
            response["sections"][section_name] = {
                "values": section_data,
                "editable": section_name not in ["security", "server"],  # Example logic
                "source": "environment" if f"COACHIQ_{section_name.upper()}" in os.environ else "default"
            }

    return response

@router.get("/features")
async def get_feature_status(feature_manager = Depends(get_feature_manager_from_request)):
    """Get current feature status and availability."""
    all_features = feature_manager.get_all_features()

    return {
        "features": {
            name: {
                "enabled": getattr(feature, "enabled", False),
                "core": getattr(feature, "core", False),
                "dependencies": getattr(feature, "dependencies", []),
                "description": getattr(feature, "description", "")
            }
            for name, feature in all_features.items()
        },
        "enabled_count": len(feature_manager.get_enabled_features()),
        "core_count": len(feature_manager.get_core_features())
    }

@router.get("/can/interfaces")
async def get_can_interface_mappings(can_service = Depends(get_can_interface_service)):
    """Get current CAN interface mappings."""
    return {
        "mappings": can_service.get_all_mappings(),
        "validation": can_service.validate_mapping(can_service.get_all_mappings())
    }

@router.put("/can/interfaces/{logical_name}")
async def update_can_interface_mapping(
    logical_name: str,
    request: Dict[str, str],  # {"physical_interface": "can1"}
    can_service = Depends(get_can_interface_service)
):
    """Update a CAN interface mapping (runtime only)."""
    if "physical_interface" not in request:
        raise HTTPException(400, "Request must contain 'physical_interface' field")

    physical_interface = request["physical_interface"]

    # Validate the mapping
    test_mappings = can_service.get_all_mappings()
    test_mappings[logical_name] = physical_interface
    validation = can_service.validate_mapping(test_mappings)

    if not validation["valid"]:
        raise HTTPException(400, f"Invalid mapping: {', '.join(validation['issues'])}")

    can_service.update_mapping(logical_name, physical_interface)

    return {
        "logical_name": logical_name,
        "physical_interface": physical_interface,
        "message": "Interface mapping updated (runtime only)"
    }

@router.post("/can/interfaces/validate")
async def validate_interface_mappings(
    mappings: Dict[str, str],
    can_service = Depends(get_can_interface_service)
):
    """Validate a set of interface mappings."""
    return can_service.validate_mapping(mappings)
```

### Phase 3: Runtime Configuration Updates

Enhance existing services to support runtime configuration changes.

#### Enhanced Feature Manager Integration

**Location:** `backend/services/feature_manager.py` (extend existing)

```python
# Add methods to existing FeatureManager class

class FeatureManager:
    # ... existing methods ...

    def update_feature_state(self, feature_name: str, enabled: bool) -> bool:
        """
        Update feature enabled state at runtime.

        Args:
            feature_name: Name of feature to update
            enabled: New enabled state

        Returns:
            True if updated successfully, False if feature not found
        """
        feature = self._features.get(feature_name)
        if not feature:
            return False

        if feature.enabled != enabled:
            logger.info(f"Updating feature '{feature_name}' enabled state: {feature.enabled} -> {enabled}")
            feature.enabled = enabled

        return True

    def get_configuration_metadata(self) -> Dict[str, Any]:
        """Get metadata about current configuration."""
        return {
            "total_features": len(self._features),
            "enabled_features": len(self.get_enabled_features()),
            "core_features": len(self.get_core_features()),
            "feature_dependencies": {
                name: getattr(feature, "dependencies", [])
                for name, feature in self._features.items()
            }
        }
```

### Phase 4: Coach Mapping Integration

Integrate coach mapping configuration with the enhanced settings system.

#### Coach Mapping Service

**Location:** `backend/services/coach_mapping_service.py` (new file)

```python
from typing import Dict, Any, List
import yaml
from pathlib import Path
from backend.core.config import get_rvc_settings
from backend.integrations.rvc.decode import load_config_data

class CoachMappingService:
    """Service for managing coach mapping configurations."""

    def __init__(self, can_interface_service):
        self.rvc_settings = get_rvc_settings()
        self.can_interface_service = can_interface_service
        self._mapping_cache = None

    def get_current_mapping(self) -> Dict[str, Any]:
        """Get current coach mapping with resolved interfaces."""
        if self._mapping_cache is None:
            self._load_mapping()
        return self._mapping_cache

    def _load_mapping(self):
        """Load coach mapping from file with interface resolution."""
        mapping_path = self.rvc_settings.get_coach_mapping_path()

        with open(mapping_path, 'r') as f:
            raw_mapping = yaml.safe_load(f)

        # Resolve logical interfaces to physical interfaces
        self._mapping_cache = self._resolve_interfaces(raw_mapping)

    def _resolve_interfaces(self, mapping: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve logical interfaces to physical interfaces throughout mapping."""
        def resolve_recursive(obj):
            if isinstance(obj, dict):
                if 'interface' in obj:
                    logical_interface = obj['interface']
                    try:
                        obj['interface'] = self.can_interface_service.resolve_interface(logical_interface)
                        obj['_logical_interface'] = logical_interface  # Keep for reference
                    except ValueError:
                        # Keep original if can't resolve
                        pass

                for value in obj.values():
                    resolve_recursive(value)

            elif isinstance(obj, list):
                for item in obj:
                    resolve_recursive(item)

        resolved = mapping.copy()
        resolve_recursive(resolved)
        return resolved

    def reload_mapping(self):
        """Reload coach mapping from file."""
        self._mapping_cache = None
        self._load_mapping()

    def get_mapping_metadata(self) -> Dict[str, Any]:
        """Get metadata about current coach mapping."""
        mapping = self.get_current_mapping()

        # Extract metadata
        coach_info = mapping.get('coach_info', {})
        file_metadata = mapping.get('file_metadata', {})

        # Count devices and interfaces
        device_count = 0
        interfaces_used = set()

        for dgn_hex, instances in mapping.items():
            if dgn_hex.startswith(('1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D', 'E', 'F')):
                for instance_id, devices in instances.items():
                    if isinstance(devices, list):
                        device_count += len(devices)
                        for device in devices:
                            if isinstance(device, dict) and 'interface' in device:
                                interfaces_used.add(device['interface'])

        return {
            "coach_info": coach_info,
            "file_metadata": file_metadata,
            "device_count": device_count,
            "interfaces_used": list(interfaces_used),
            "mapping_path": str(self.rvc_settings.get_coach_mapping_path())
        }
```

---

## Implementation Plan

### Phase 1: CAN Interface Service (1-2 days)
1. ✅ Enhanced `CANSettings` with interface mappings
2. ✅ New `CANInterfaceService` following existing service patterns
3. ✅ Feature registration in `feature_flags.yaml`
4. ✅ Dependency injection setup

### Phase 2: Configuration API (2-3 days)
1. ✅ Configuration router with settings and feature endpoints
2. ✅ CAN interface mapping API endpoints
3. ✅ Integration with existing router configuration
4. ✅ API documentation

### Phase 3: Runtime Updates (1-2 days)
1. ✅ Enhanced feature manager with runtime updates
2. ✅ Configuration change notifications via WebSocket
3. ✅ Cache invalidation for settings changes

### Phase 4: Coach Mapping Integration (2-3 days)
1. ✅ Coach mapping service with interface resolution
2. ✅ Integration with existing decode logic
3. ✅ API endpoints for coach mapping management

---

## Benefits of Revised Approach

### Architectural Consistency
- ✅ Leverages existing Pydantic Settings excellence
- ✅ Follows established service patterns
- ✅ Uses proven feature manager system
- ✅ Maintains in-memory state consistency

### Implementation Simplicity
- ✅ No database complexity or stub implementations
- ✅ Builds on well-understood patterns
- ✅ Minimal disruption to existing code
- ✅ Clear upgrade path

### Functionality Delivered
- ✅ CAN interface mapping with logical names
- ✅ Runtime configuration updates
- ✅ Configuration API with source tracking
- ✅ Coach mapping integration
- ✅ Type safety and validation

### Maintenance Benefits
- ✅ Consistent with existing architecture
- ✅ Easier to understand and modify
- ✅ Less code to maintain
- ✅ Natural extension points

---

## Comparison with Original Plan

| Aspect | Original Plan | Revised Plan |
|--------|---------------|--------------|
| **Database** | SQLite with stubs | In-memory (consistent) |
| **Complexity** | High (new systems) | Low (extend existing) |
| **Disruption** | High (new patterns) | Minimal (familiar patterns) |
| **Implementation** | 3-4 weeks | 1-2 weeks |
| **Maintenance** | Complex | Simple |
| **Architecture Fit** | Poor | Excellent |

---

## Success Criteria

- [ ] CAN interface mapping resolves logical to physical interfaces
- [ ] Configuration API provides settings and feature visibility
- [ ] Runtime configuration updates work without restart
- [ ] Coach mapping integrates with interface resolution
- [ ] All changes follow existing architectural patterns
- [ ] No disruption to existing functionality
- [ ] Type safety maintained throughout
- [ ] Performance impact is minimal

This revised approach delivers the same functionality with significantly less complexity while maintaining perfect architectural consistency with the existing excellent codebase.
