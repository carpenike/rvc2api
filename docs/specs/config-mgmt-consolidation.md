# Configuration Management System Specification

- **Feature Name:** Consolidated Configuration Management System
- **Status:** Proposed
- **Date:** 2025-06-07
- **Author(s):** GitHub Copilot
- **Related Spec:** `/docs/specs/config-mgmt-consolidation.md` (original draft)
- **Related ADR:** [To be created]

**Summary:**
Implement a comprehensive configuration management system that consolidates environment variables, persistent database storage, and Pydantic defaults with full API/UI visibility and override capabilities. The system will extend the existing `backend/core/config.py` structure while adding database persistence and administrative UI capabilities.

---

## Summary of Enhancements

This specification has been enhanced to include **CAN Interface Mapping System** alongside the core configuration management functionality. Key additions:

### CAN Interface Mapping Features

1. **Logical Interface Names**: Coach mapping files can use intuitive names like `house` and `chassis` instead of `can0`, `can1`
2. **Runtime Resolution**: System automatically resolves logical names to physical interfaces at runtime
3. **Configuration Flexibility**: Interface mappings configurable via environment variables or database
4. **Backward Compatibility**: Existing physical interface names continue to work unchanged
5. **Validation APIs**: Endpoints to validate and manage interface mappings
6. **Migration Tools**: Automated conversion from physical to logical interface names

### Integration Benefits

- **Portable Configurations**: Coach mapping files work across different hardware setups
- **Improved Readability**: `interface: house` is clearer than `interface: can1`
- **Centralized Management**: All interface mappings managed through the configuration system
- **Type Safety**: Full Pydantic validation for interface mappings
- **API Documentation**: OpenAPI schema includes interface mapping endpoints

This enhancement aligns perfectly with the configuration management system's principles of type safety, source transparency, and runtime editability while solving the specific problem of hardcoded CAN interface names in coach mapping files.

---

## Architecture Overview

### Configuration Sources (Priority Order)

1. **Environment Variables** (Highest - Immutable overrides from Nix/deployment)
2. **SQLite Database** (Middle - Runtime editable via UI/API)
3. **Pydantic Defaults** (Lowest - Code-defined fallbacks)

### Design Principles

- **Type Safety**: All configuration uses Pydantic models with full type validation
- **Source Transparency**: Always know where each config value comes from
- **Runtime Editability**: UI/API can modify database-stored values
- **Override Protection**: Environment variables cannot be overridden by UI
- **Schema Documentation**: Self-documenting configuration with descriptions and validation

---

## Current State Analysis

The existing `backend/core/config.py` already provides:

- ✅ Pydantic Settings with environment variable support
- ✅ Structured configuration sections (Server, CORS, Database, etc.)
- ✅ Type validation and field descriptions
- ✅ Environment variable parsing with prefixes
- ✅ Caching via `@lru_cache`

**What's Missing:**

- ❌ Database persistence for runtime configuration changes
- ❌ Source tracking (env vs default vs database)
- ❌ API endpoints for configuration management
- ❌ Administrative UI for configuration editing
- ❌ Runtime configuration reload capabilities
- ❌ CAN interface mapping for logical names (house/chassis vs can0/can1)

---

## Implementation Plan

### Phase 1: Core Configuration Infrastructure (Current Implementation)

#### 1.1 Enhanced Configuration Models

**Location:** `backend/core/config.py` (extend existing)

```python
from typing import Literal, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum

class ConfigSource(str, Enum):
    """Configuration value source tracking."""
    ENVIRONMENT = "environment"
    DATABASE = "database"  # TODO: Implement when persistence module is ready
    DEFAULT = "default"

class ConfigValue(BaseModel):
    """Enhanced configuration value with source tracking."""
    value: Any
    source: ConfigSource
    is_editable: bool  # False if from environment
    description: str
    field_type: str

class ConfigSchema(BaseModel):
    """Complete configuration schema with metadata."""
    values: Dict[str, ConfigValue]
    sections: Dict[str, Dict[str, ConfigValue]]
```

#### 1.2 Database Persistence Layer (STUBBED - Future Implementation)

**Location:** `backend/core/config_persistence.py` (new file - stub implementation)

```python
from typing import Optional, Dict, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class ConfigDatabase:
    """
    STUB: SQLite-based configuration persistence.

    This is a placeholder implementation that returns None for all operations.
    Will be implemented when the persistence module is ready.
    """

    def __init__(self, db_path: Path):
        self.db_path = db_path
        logger.info(f"ConfigDatabase stub initialized with path: {db_path}")
        # TODO: Implement actual database initialization when persistence module is ready

    def get_value(self, key: str) -> Optional[Any]:
        """STUB: Get configuration value from database."""
        logger.debug(f"ConfigDatabase.get_value({key}) - returning None (stub)")
        return None  # Always return None until persistence is implemented

    def set_value(self, key: str, value: Any) -> None:
        """STUB: Set configuration value in database."""
        logger.debug(f"ConfigDatabase.set_value({key}, {value}) - no-op (stub)")
        # TODO: Implement when persistence module is ready

    def get_all_values(self) -> Dict[str, Any]:
        """STUB: Get all configuration values from database."""
        logger.debug("ConfigDatabase.get_all_values() - returning empty dict (stub)")
        return {}  # Always return empty until persistence is implemented

    def delete_value(self, key: str) -> None:
        """STUB: Remove configuration value from database."""
        logger.debug(f"ConfigDatabase.delete_value({key}) - no-op (stub)")
        # TODO: Implement when persistence module is ready
```

#### 1.3 Configuration Loader Enhancement

**Location:** `backend/core/config_loader.py` (new file)

```python
from functools import lru_cache
from typing import Dict, Any, Tuple
import os
import logging
from pathlib import Path

from .config import Settings
from .config_persistence import ConfigDatabase

logger = logging.getLogger(__name__)

class ConfigurationManager:
    """
    Manages configuration loading with source tracking.

    Currently supports Environment Variables and Pydantic Defaults.
    Database persistence is stubbed and will be implemented when the
    persistence module is ready.
    """

    def __init__(self, db_path: Path):
        # Use stubbed database implementation for now
        self.db = ConfigDatabase(db_path)

    def load_configuration(self) -> Tuple[Settings, Dict[str, str]]:
        """
        Load configuration with full source tracking.

        Returns:
            Tuple of (Settings instance, source mapping)
        """
        values = {}
        sources = {}

        # Get Pydantic model fields
        for field_name, field_info in Settings.__fields__.items():
            env_key = self._get_env_key(field_name, field_info)

            # Check environment first (highest priority)
            if env_key and env_key in os.environ:
                values[field_name] = os.environ[env_key]
                sources[field_name] = "environment"
                logger.debug(f"Config {field_name}: using environment value from {env_key}")

            # Check database second (stubbed - always returns None for now)
            elif (db_value := self.db.get_value(field_name)) is not None:
                values[field_name] = db_value
                sources[field_name] = "database"
                logger.debug(f"Config {field_name}: using database value")

            # Use default last
            else:
                values[field_name] = field_info.default
                sources[field_name] = "default"
                logger.debug(f"Config {field_name}: using default value")

        config = Settings(**values)
        return config, sources

    def _get_env_key(self, field_name: str, field_info) -> str:
        """Extract environment variable key from field info."""
        # Handle the env_prefix pattern used in your existing Settings classes
        env_prefix = getattr(field_info.annotation, 'env_prefix', 'COACHIQ_')
        return f"{env_prefix}{field_name.upper()}"

    def update_config_value(self, key: str, value: Any) -> bool:
        """
        Update a configuration value in the database.

        Args:
            key: Configuration key to update
            value: New value to set

        Returns:
            True if updated successfully, False if overridden by environment
        """
        # Check if value is from environment (immutable)
        _, sources = self.load_configuration()
        if sources.get(key) == "environment":
            logger.warning(f"Cannot update {key}: overridden by environment variable")
            return False

        # Update database (stubbed for now)
        self.db.set_value(key, value)

        # Clear cache to force reload
        get_configuration_manager.cache_clear()

        logger.info(f"Updated configuration {key} = {value}")
        return True

@lru_cache
def get_configuration_manager() -> ConfigurationManager:
    """Cached configuration manager instance."""
    # TODO: Get db_path from environment or settings when persistence module is ready
    db_path = Path("data/config.db")
    return ConfigurationManager(db_path)

@lru_cache
def get_current_config() -> Settings:
    """Get current configuration (cached)."""
    config_mgr = get_configuration_manager()
    config, _ = config_mgr.load_configuration()
    return config
```

### Phase 2: API Integration (Current Implementation - With Stubs)

#### 2.1 Configuration API Router

**Location:** `backend/api/routers/config.py` (new file)

```python
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from ...core.config_loader import get_configuration_manager, ConfigurationManager, get_current_config
from ...core.config import Settings

router = APIRouter(prefix="/config", tags=["configuration"])

@router.get("/")
async def get_configuration(
    config_mgr: ConfigurationManager = Depends(get_configuration_manager)
):
    """
    Get complete configuration with source information.

    Returns:
        - All configuration values
        - Source of each value (environment/database/default)
        - Editability status (false for environment variables)
        - Field descriptions and types

    Note: Database persistence is currently stubbed. All non-environment
    values will show as "default" source until persistence is implemented.
    """
    config, sources = config_mgr.load_configuration()

    # Transform to response format
    response = {
        "values": {},
        "sources": sources,
        "schema": {}
    }

    # Add configuration values and metadata
    for field_name, field_info in Settings.__fields__.items():
        value = getattr(config, field_name)
        source = sources.get(field_name, "default")

        response["values"][field_name] = {
            "value": value,
            "source": source,
            "is_editable": source != "environment",
            "description": field_info.description or "",
            "field_type": str(field_info.annotation)
        }

    return response

@router.put("/{key}")
async def update_configuration_value(
    key: str,
    request: Dict[str, Any],  # {"value": new_value}
    config_mgr: ConfigurationManager = Depends(get_configuration_manager)
):
    """
    Update a single configuration value.

    Args:
        key: Configuration key to update
        request: {"value": new_value}

    Returns:
        Updated configuration value info

    Raises:
        403: If value is overridden by environment variable
        422: If value validation fails

    Note: Database persistence is currently stubbed. This endpoint will
    accept updates but they won't persist until the persistence module
    is implemented.
    """
    if "value" not in request:
        raise HTTPException(400, "Request must contain 'value' field")

    new_value = request["value"]

    # Validate key exists in Settings
    if not hasattr(Settings, key):
        raise HTTPException(404, f"Configuration key '{key}' not found")

    # Check if value is from environment (immutable)
    _, sources = config_mgr.load_configuration()
    if sources.get(key) == "environment":
        raise HTTPException(403, f"Cannot override environment variable '{key}'")

    # TODO: Add Pydantic validation here

    # Update value (currently stubbed)
    success = config_mgr.update_config_value(key, new_value)
    if not success:
        raise HTTPException(403, f"Cannot update '{key}': overridden by environment")

    # Return updated value info
    config, updated_sources = config_mgr.load_configuration()
    value = getattr(config, key)

    return {
        "key": key,
        "value": value,
        "source": updated_sources.get(key, "default"),
        "is_editable": updated_sources.get(key) != "environment",
        "message": "Value updated successfully (Note: Persistence is stubbed)"
    }

@router.post("/reload")
async def reload_configuration():
    """
    Reload configuration from all sources.

    Clears caches and forces configuration reload.
    """
    # Clear caches
    get_configuration_manager.cache_clear()
    get_current_config.cache_clear()

    return {
        "message": "Configuration reloaded successfully",
        "note": "Database persistence is currently stubbed"
    }
```

#### 2.2 Integration with Main Router

**Location:** `backend/api/router_config.py` (extend existing)

```python
# Add configuration router
from .routers.config import router as config_router

def create_api_router():
    router = APIRouter()
    # ... existing routers ...
    router.include_router(config_router, prefix="/api")
    return router
```

### Phase 3: Frontend UI Integration

#### 3.1 Configuration Admin Page

**Location:** `frontend/src/pages/ConfigPage.tsx` (new file)

```typescript
import { useState, useEffect } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Lock, Save, RotateCcw } from "lucide-react";

interface ConfigValue {
  value: any;
  source: "environment" | "database" | "default";
  is_editable: boolean;
  description: string;
  field_type: string;
}

interface ConfigSchema {
  values: Record<string, ConfigValue>;
  sections: Record<string, Record<string, ConfigValue>>;
}

export function ConfigPage() {
  const [config, setConfig] = useState<ConfigSchema | null>(null);
  const [editedValues, setEditedValues] = useState<Record<string, any>>({});

  // Fetch configuration
  // Render form with sections
  // Handle value editing
  // Save changes via API

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Configuration</h1>
        <div className="space-x-2">
          <Button variant="outline" onClick={handleReload}>
            <RotateCcw className="w-4 h-4 mr-2" />
            Reload
          </Button>
          <Button onClick={handleSave} disabled={!hasChanges}>
            <Save className="w-4 h-4 mr-2" />
            Save Changes
          </Button>
        </div>
      </div>

      {/* Configuration sections */}
      {Object.entries(config?.sections || {}).map(([section, values]) => (
        <Card key={section}>
          <CardHeader>
            <CardTitle>{section}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {Object.entries(values).map(([key, configValue]) => (
              <ConfigField
                key={key}
                name={key}
                config={configValue}
                value={editedValues[key] ?? configValue.value}
                onChange={(value) =>
                  setEditedValues((prev) => ({ ...prev, [key]: value }))
                }
              />
            ))}
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function ConfigField({ name, config, value, onChange }) {
  const isLocked = config.source === "environment";

  return (
    <div className="flex items-center space-x-4">
      <div className="flex-1">
        <label className="block text-sm font-medium mb-1">
          {name}
          {isLocked && <Lock className="inline w-3 h-3 ml-1" />}
        </label>
        <Input
          value={value}
          onChange={(e) => onChange(e.target.value)}
          disabled={isLocked}
          className={isLocked ? "bg-gray-50" : ""}
        />
        <p className="text-xs text-gray-500 mt-1">{config.description}</p>
      </div>
      <div className="flex flex-col items-end space-y-1">
        <Badge
          variant={
            config.source === "environment"
              ? "destructive"
              : config.source === "database"
              ? "default"
              : "secondary"
          }
        >
          {config.source}
        </Badge>
        <span className="text-xs text-gray-400">{config.field_type}</span>
      </div>
    </div>
  );
}
```

#### 3.2 Navigation Integration

**Location:** `frontend/src/components/Layout/Sidebar.tsx` (extend existing)

```typescript
// Add configuration link to admin section
<SidebarItem
  href="/config"
  icon={Settings}
  label="Configuration"
  adminOnly={true}
/>
```

### Phase 4: Testing & Documentation

#### 4.1 Unit Tests

**Location:** `tests/test_config_management.py` (new file)

```python
import pytest
import tempfile
from pathlib import Path
from backend.core.config_loader import ConfigurationManager
from backend.core.config import Settings

class TestConfigurationManager:
    def test_environment_override(self):
        """Test environment variables take precedence."""

    def test_database_persistence(self):
        """Test database value storage and retrieval."""

    def test_default_fallback(self):
        """Test fallback to Pydantic defaults."""

    def test_source_tracking(self):
        """Test configuration source tracking."""

class TestConfigurationAPI:
    def test_get_configuration(self):
        """Test configuration API endpoint."""

    def test_update_configuration(self):
        """Test configuration update endpoint."""

    def test_environment_protection(self):
        """Test environment variable protection."""
```

#### 4.2 API Documentation

```python
# Enhanced docstrings for OpenAPI schema generation
@router.get("/",
    summary="Get Configuration",
    description="""
    Retrieve the complete application configuration including:
    - Current values for all settings
    - Source of each value (environment/database/default)
    - Whether each value can be edited via API
    - Field descriptions and validation rules
    """,
    response_description="Complete configuration schema with metadata"
)
```

---

## Database Schema

```sql
-- Configuration persistence table
CREATE TABLE config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,  -- JSON-serialized value
    value_type TEXT NOT NULL,  -- For type reconstruction
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by TEXT  -- Future: user tracking
);

CREATE INDEX idx_config_updated_at ON config(updated_at);
```

---

## CAN Interface Mapping System

### Overview

Implements a logical CAN interface mapping system to decouple physical CAN device names (`can0`, `can1`) from coach mapping files, enabling portable configuration files that work across different hardware setups.

### Configuration Structure

#### Enhanced CANSettings (backend/core/config.py)

```python
class CANInterfaceMapping(BaseModel):
    """Logical to physical CAN interface mapping."""
    logical_name: str = Field(description="Logical interface name (e.g., 'house', 'chassis')")
    physical_interface: str = Field(description="Physical CAN interface (e.g., 'can0', 'can1')")
    description: str = Field(default="", description="Human-readable description")

class CANSettings(BaseSettings):
    """Enhanced CAN bus configuration with interface mapping."""

    model_config = SettingsConfigDict(env_prefix="COACHIQ_CAN__", case_sensitive=False)

    # Existing fields...
    interface: str = Field(default="can0", description="CAN interface name (deprecated)")
    interfaces: list[str] = Field(default=["can0"], description="CAN interface names")

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

    def resolve_interface(self, interface_name: str) -> str:
        """
        Resolve logical interface name to physical interface.

        Args:
            interface_name: Logical name (e.g., 'house') or physical name (e.g., 'can0')

        Returns:
            Physical interface name

        Raises:
            ValueError: If logical interface is not mapped
        """
        # If it's already a physical interface, return as-is
        if interface_name.startswith("can") or interface_name.startswith("vcan"):
            return interface_name

        # Look up logical mapping
        if interface_name in self.interface_mappings:
            return self.interface_mappings[interface_name]

        raise ValueError(f"Unknown logical CAN interface: {interface_name}")

    def get_all_physical_interfaces(self) -> list[str]:
        """Get all configured physical interfaces."""
        return list(set(self.interface_mappings.values()))
```

#### Environment Variable Configuration

```bash
# Interface mapping via environment variables
COACHIQ_CAN__INTERFACE_MAPPINGS="house:can0,chassis:can1,engine:can2"

# Or using JSON format
COACHIQ_CAN__INTERFACE_MAPPINGS='{"house": "can0", "chassis": "can1", "engine": "can2"}'
```

### Coach Mapping File Updates

#### Before (Physical Interfaces)

```yaml
# config/2021_Entegra_Aspire_44R.yml
"1FEDA":
  "25":
    - entity_id: light_kitchen_overhead
      interface: can1 # Physical interface
      # ...
```

#### After (Logical Interfaces)

```yaml
# config/2021_Entegra_Aspire_44R.yml
"1FEDA":
  "25":
    - entity_id: light_kitchen_overhead
      interface: house # Logical interface
      # ...
```

### Runtime Interface Resolution

#### CAN Service Integration

```python
# backend/services/can_service.py
from backend.core.config import get_current_config

class CANService:
    def __init__(self):
        self.config = get_current_config()

    def resolve_device_interface(self, device_config: dict) -> str:
        """Resolve device interface from config."""
        logical_interface = device_config.get("interface", "house")
        return self.config.can.resolve_interface(logical_interface)

    def setup_can_listeners(self, devices: list[dict]):
        """Set up CAN listeners with resolved interfaces."""
        for device in devices:
            physical_interface = self.resolve_device_interface(device)
            # Use physical_interface for actual CAN setup...
```

### API Endpoints

#### Configuration API Extension

```python
# backend/api/routers/config.py

@router.get("/interfaces", response_model=dict[str, str])
async def get_can_interface_mappings():
    """
    Get current CAN interface mappings.

    Returns:
        Dictionary mapping logical names to physical interfaces
    """
    config = get_current_config()
    return config.can.interface_mappings

@router.post("/interfaces/validate")
async def validate_interface_mapping(mapping: dict[str, str]):
    """
    Validate a proposed interface mapping.

    Args:
        mapping: Proposed logical to physical interface mapping

    Returns:
        Validation results with any issues found
    """
    issues = []

    # Check for duplicate physical interfaces
    physical_interfaces = list(mapping.values())
    if len(physical_interfaces) != len(set(physical_interfaces)):
        issues.append("Duplicate physical interfaces detected")

    # Validate physical interface names
    for logical, physical in mapping.items():
        if not physical.startswith(("can", "vcan")):
            issues.append(f"Invalid physical interface: {physical}")

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "mapping": mapping
    }

@router.get("/interfaces/usage")
async def get_interface_usage():
    """
    Get usage statistics for CAN interfaces.

    Returns:
        Statistics about which interfaces are used by which devices
    """
    # This would analyze coach mapping files to show interface usage
    pass
```

### Migration Tools

#### Coach Mapping Migration Script

```python
# scripts/migrate_coach_mappings.py
import yaml
from pathlib import Path
from typing import Dict, Any

class CoachMappingMigrator:
    """Migrate coach mapping files from physical to logical interfaces."""

    def __init__(self, interface_mapping: Dict[str, str]):
        # Reverse mapping: physical -> logical
        self.reverse_mapping = {v: k for k, v in interface_mapping.items()}

    def migrate_file(self, file_path: Path) -> bool:
        """
        Migrate a single coach mapping file.

        Returns:
            True if file was modified, False if no changes needed
        """
        with open(file_path, 'r') as f:
            data = yaml.safe_load(f)

        modified = self._migrate_data(data)

        if modified:
            with open(file_path, 'w') as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False)

        return modified

    def _migrate_data(self, data: Any) -> bool:
        """Recursively migrate interface references in data structure."""
        modified = False

        if isinstance(data, dict):
            if 'interface' in data and isinstance(data['interface'], str):
                physical = data['interface']
                if physical in self.reverse_mapping:
                    data['interface'] = self.reverse_mapping[physical]
                    modified = True

            for value in data.values():
                if self._migrate_data(value):
                    modified = True

        elif isinstance(data, list):
            for item in data:
                if self._migrate_data(item):
                    modified = True

        return modified

# Usage
if __name__ == "__main__":
    migrator = CoachMappingMigrator({
        "house": "can0",
        "chassis": "can1"
    })

    config_dir = Path("config")
    for yml_file in config_dir.glob("*.yml"):
        if migrator.migrate_file(yml_file):
            print(f"Migrated: {yml_file}")
```

### Validation and Error Handling

#### Startup Validation

```python
# backend/core/startup_validation.py

def validate_can_configuration():
    """Validate CAN configuration on startup."""
    config = get_current_config()
    issues = []

    # Check for missing logical interface definitions
    coach_mapping_files = Path("config").glob("*.yml")
    used_interfaces = set()

    for file_path in coach_mapping_files:
        with open(file_path, 'r') as f:
            data = yaml.safe_load(f)
        used_interfaces.update(extract_interface_names(data))

    # Check if all used logical interfaces are mapped
    unmapped = used_interfaces - set(config.can.interface_mappings.keys())
    if unmapped:
        issues.append(f"Unmapped logical interfaces: {unmapped}")

    # Log validation results
    if issues:
        logger.error("CAN configuration validation failed:")
        for issue in issues:
            logger.error(f"  - {issue}")
        raise ValueError("Invalid CAN configuration")
    else:
        logger.info("CAN configuration validation passed")
```

### Benefits

1. **Portability**: Coach mapping files work across different hardware setups
2. **Clarity**: Logical names (`house`, `chassis`) are more intuitive than `can0`, `can1`
3. **Flexibility**: Easy to reconfigure physical interfaces without touching mapping files
4. **Validation**: Built-in validation prevents configuration errors
5. **Migration**: Automated tools to convert existing configurations
6. **Backward Compatibility**: Still supports direct physical interface names

---

## File Structure (Updated)

```
backend/
├── core/
│   ├── config.py              # Enhanced Settings classes
│   ├── config_loader.py       # ConfigurationManager (new)
│   ├── config_persistence.py  # SQLite database layer (new)
│   └── dependencies.py        # DI integration (extend)
├── api/routers/
│   └── config.py              # Configuration API endpoints (new)
└── models/
    └── config.py              # Configuration response models (new)

frontend/src/
├── pages/
│   └── ConfigPage.tsx         # Admin configuration UI (new)
├── components/config/
│   ├── ConfigField.tsx        # Individual field component (new)
│   └── ConfigSection.tsx      # Section grouping component (new)
└── types/
    └── config.ts              # TypeScript types (new)

tests/
├── test_config_management.py  # Core config tests (new)
├── test_config_api.py         # API endpoint tests (new)
└── test_config_ui.py          # Frontend component tests (new)
```

---

## Migration Strategy

### Phase 1: Core Infrastructure (Current Sprint)

- ✅ Extend current `backend/core/config.py` with source tracking
- ✅ Add stubbed database persistence layer
- ✅ Implement configuration manager with env + default support
- ✅ Add configuration API endpoints (with stubbed persistence)
- ✅ Maintain full backward compatibility with existing Settings usage
- ✅ Add CAN interface mapping system for logical interface names

### Phase 2: Frontend Integration (Next Sprint)

- ✅ Build admin UI as new page
- ✅ Show configuration values and sources
- ✅ Handle environment variable protection in UI
- ✅ No changes to existing application usage
- ✅ Add CAN interface mapping management in admin UI

### Phase 3: Persistence Implementation (Future Sprint)

- 🔄 Design and implement persistence module
- 🔄 Replace stubbed `ConfigDatabase` with real SQLite implementation
- 🔄 Add database schema and migrations
- 🔄 Enable runtime configuration editing

### Phase 4: Enhanced Features (Future)

- 🔄 Configuration validation and rollback
- 🔄 Audit logging for configuration changes
- 🔄 Configuration export/import functionality
- 🔄 Multi-environment configuration profiles
- 🔄 Coach mapping migration tools and validation
- 🔄 Advanced CAN interface diagnostics and validation

### Benefits of Phased Approach

#### Immediate (Phase 1)

- **Source Visibility**: See where each configuration value comes from
- **Environment Safety**: Prevents accidental override of deployment settings
- **API Foundation**: Configuration management endpoints ready for UI

#### Short Term (Phase 2)

- **Admin Interface**: Centralized configuration management UI
- **Operational Insight**: Clear view of all application settings
- **Preparation**: UI ready for database persistence when implemented

#### Long Term (Phase 3+)

- **Runtime Changes**: Modify settings without application restart
- **Persistence**: Settings survive application restarts
- **Audit Trail**: Track who changed what and when

## Current Implementation Scope (Phase 1)

### What We're Building Now

#### ✅ Environment + Default Configuration

- Source tracking for environment variables vs Pydantic defaults
- Configuration management API with proper source indication
- Admin UI showing configuration values and their sources
- Protection against environment variable override attempts

#### ✅ Stubbed Database Layer

- `ConfigDatabase` class with proper interface but no-op implementation
- Logging to indicate when stub methods are called
- Clear TODOs for when persistence module is ready
- API endpoints that work but indicate persistence is stubbed

#### ✅ Foundation for Future Persistence

- Complete API surface ready for real database implementation
- Frontend UI designed to handle database-persisted values
- Configuration loader architecture that supports all three sources
- Clean separation between stub and real implementations

#### ✅ CAN Interface Mapping System

- Enhanced `CANSettings` with logical-to-physical interface mapping
- API endpoints for interface mapping management and validation
- Runtime interface resolution for coach mapping files
- Backward compatibility with existing physical interface names
- Foundation for coach mapping migration tools

### What We're NOT Building Yet

#### ❌ SQLite Database Implementation

- Actual database schema and table creation
- Real persistence of configuration changes
- Database migrations and versioning
- Transaction handling and error recovery

#### ❌ Advanced Features

- Configuration change auditing
- Multi-user configuration management
- Configuration validation and rollback
- Import/export functionality
- Coach mapping file migration automation
- Advanced CAN interface diagnostics

### Implementation Benefits

Even with stubbed persistence, this implementation provides:

1. **Immediate Value**: Clear visibility into configuration sources
2. **Environment Safety**: Prevents accidental override of deployment settings
3. **Development Foundation**: Complete architecture ready for persistence
4. **User Experience**: Admin interface shows current state and planned features
5. **Clean Architecture**: Separation of concerns makes persistence easy to add later

### Success Metrics for Phase 1

- [ ] ✅ All existing configuration continues to work unchanged
- [ ] ✅ New API shows configuration values with source tracking
- [ ] ✅ Environment variables are clearly marked as immutable
- [ ] ✅ Admin UI displays configuration with appropriate editing controls
- [ ] ✅ All code passes linting and type checking
- [ ] ✅ Comprehensive test coverage for implemented functionality
- [ ] ✅ Clear documentation of stubbed vs implemented features
- [ ] ✅ Logging indicates when stub implementations are called
- [ ] ✅ CAN interface mapping system functional with logical interface resolution
- [ ] ✅ API endpoints for interface mapping validation and management work
- [ ] ✅ Backward compatibility maintained for existing coach mapping files

This approach allows us to build and test the complete configuration management foundation while waiting for the persistence module to be designed and implemented.

### For Developers

- **Type Safety**: Full Pydantic validation and IDE support
- **Debugging**: Always know configuration source
- **Testing**: Easy to mock and override settings

### For Administrators

- **Runtime Changes**: Modify settings without restarts
- **Visibility**: See all configuration in one place
- **Safety**: Environment variables protected from accidental changes

### For Deployment

- **Nix Integration**: Environment variables work seamlessly
- **Flexibility**: Choose between static (env) and dynamic (DB) configuration
- **Auditability**: Track configuration changes over time

---

## Success Criteria

- [ ] All existing configuration continues to work unchanged
- [ ] New database-persisted settings can be edited via UI
- [ ] Environment variables cannot be overridden by API/UI
- [ ] Configuration source is always visible and accurate
- [ ] CAN interface mappings resolve correctly at runtime
- [ ] Coach mapping files support both logical and physical interface names
- [ ] Migration tools can convert existing configurations
- [ ] API provides complete configuration schema and metadata
- [ ] Frontend admin interface is intuitive and responsive
- [ ] All changes are covered by comprehensive tests
- [ ] Configuration reloading works without application restart
- [ ] Performance impact is minimal (proper caching)
- [ ] Documentation is complete and up-to-date

This specification provides a comprehensive, backwards-compatible approach to consolidated configuration management that leverages your existing Pydantic Settings foundation while adding the database persistence and administrative capabilities outlined in the original plan.
