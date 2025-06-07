# Configuration Management System Spec

## Overview

This document defines the architecture and implementation plan for the configuration management system in the `coachiq` project. The system is responsible for providing typed, documented, override-aware configuration values to all backend components.

Configuration values are loaded from the following sources in order of precedence:

1. **Environment Variables** (highest precedence; treated as immutable overrides)
2. **Persistent SQLite Configuration Database** (editable via UI/API)
3. **Pydantic-defined Defaults** (fallbacks embedded in code)

The system provides a unified Pydantic model as the authoritative config object used throughout the backend.

---

## Goals

- ✅ Centralize configuration logic
- ✅ Support Nix/ENV-driven overrides
- ✅ Enable persistent UI-editable config
- ✅ Clearly indicate config source (env, db, default)
- ✅ Provide introspection and API visibility for all config values

---

## Configuration Resolution Strategy

| Priority | Source            | Editable | Notes                                    |
|----------|-------------------|----------|------------------------------------------|
| 1        | Environment Vars   | ❌       | Highest priority, set by Nix or user     |
| 2        | SQLite DB          | ✅       | Settable via UI or CLI                   |
| 3        | Code Default       | ❌       | Fallback from Pydantic schema            |

---

## Pydantic Model

All configuration is defined in a Pydantic model with metadata:

```python
from pydantic import BaseModel, Field
from typing import Literal

class AppConfig(BaseModel):
    can_interface: str = Field(
        default="can0",
        description="CAN bus interface to bind to.",
        env="CAN_INTERFACE"
    )
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO",
        description="Log verbosity.",
        env="LOG_LEVEL"
    )
```

---

## Runtime Load Logic

Config is loaded at startup using the following logic:

```python
def load_config(db=None):
    values = {}
    sources = {}

    for name, field in AppConfig.__fields__.items():
        env_key = field.field_info.extra.get("env")
        if env_key and env_key in os.environ:
            values[name] = os.environ[env_key]
            sources[name] = "env"
        elif db and (db_value := db.get(name)) is not None:
            values[name] = db_value
            sources[name] = "db"
        else:
            values[name] = field.default
            sources[name] = "default"

    return AppConfig(**values), sources
```

The final config is cached with `@lru_cache` or FastAPI dependency injection.

---

## API Endpoints

### `GET /api/config`
Returns current config values, source, and schema metadata.

```json
{
  "config": {
    "can_interface": "can0",
    "log_level": "INFO"
  },
  "sources": {
    "can_interface": "env",
    "log_level": "default"
  },
  "schema": { ...AppConfig.schema() }
}
```

### `PUT /api/config/{key}`
Updates a single config value in the database, unless overridden by an environment variable. Returns `403` if immutable.

---

## Frontend Admin UI (ShadCN)

- Display config as editable form fields
- Use metadata to show:
  - Title and description
  - Current value
  - Source (`env`, `db`, `default`)
  - Lock icon if from `env`

### Actions:
- Save button triggers `PUT /api/config/{key}`
- Read-only fields display "Defined in ENV" badge

---

## Future Enhancements

- [ ] Support live reload via `POST /api/config/reload`
- [ ] Support config categories (e.g. `network`, `logging`)
- [ ] Export Markdown or JSON documentation of config schema
- [ ] CLI: `coachiq config show` and `set`

---

## Implementation Tasks

### ✅ Schema and Loader
- [ ] Define `AppConfig` model with metadata
- [ ] Implement `load_config()` with source detection
- [ ] Expose cached `get_config()` to backend

### ✅ SQLite Storage
- [ ] Define config table schema: `{ key, value }`
- [ ] Load DB values in loader
- [ ] Implement update logic

### ✅ FastAPI Endpoints
- [ ] `GET /api/config`
- [ ] `PUT /api/config/{key}`

### ✅ UI Page
- [ ] Display form with all settings
- [ ] Mark env-overridden settings as read-only
- [ ] Persist editable values via API

---

## File Structure (Proposed)

```
backend/
├── config/
│   ├── models.py          # AppConfig Pydantic model
│   ├── loader.py          # load_config(), get_config()
│   ├── db.py              # DB access helpers
│   └── api.py             # FastAPI routes
```

---

## Summary

This spec defines a robust, extensible, and UI-integrated configuration management system that supports Nix/ENV-driven overrides while allowing user-friendly edits via a persistent database and admin UI.

It ensures:
- Clarity in config precedence
- Maintainability through typed schemas
- Visibility via APIs and UI