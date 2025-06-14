# NixOS Module Environment Variable Mapping

This document shows exactly which environment variables are set based on your Nix configuration.

## How Environment Mapping Works

The NixOS module uses **conditional environment variable setting**:
- If a Nix option is `null` → No environment variable is set
- If a Nix option has a value → Environment variable is set only if different from backend default
- Backend defaults are the single source of truth

## Examples by Configuration

### Example 1: Bare Minimum
```nix
coachiq.enable = true;
```

**Environment Variables Set:**
```bash
COACHIQ_ENVIRONMENT=production
```

**Backend Uses Its Defaults For:**
- Server: `0.0.0.0:8000`
- Logging: `INFO` level
- All features: As defined in `feature_flags.yaml`
- Persistence: Disabled

### Example 2: Custom Port Only
```nix
coachiq = {
  enable = true;
  settings.server.port = 8080;
};
```

**Environment Variables Set:**
```bash
COACHIQ_ENVIRONMENT=production
COACHIQ_SERVER__PORT=8080
```

**Backend Defaults Still Used For:**
- Host: `0.0.0.0`
- Workers: `1`
- Everything else

### Example 3: Production Configuration
```nix
coachiq = {
  enable = true;
  settings = {
    server = {
      host = "127.0.0.1";
      port = 8443;
    };
    security.secretKeyFile = "/run/secrets/jwt";
    persistence.enabled = true;
    logging.level = "WARNING";
  };
};
```

**Environment Variables Set:**
```bash
COACHIQ_ENVIRONMENT=production
COACHIQ_SERVER__HOST=127.0.0.1
COACHIQ_SERVER__PORT=8443
COACHIQ_SECURITY__SECRET_KEY_FILE=/run/secrets/jwt
COACHIQ_PERSISTENCE__ENABLED=true
COACHIQ_LOGGING__LEVEL=WARNING
```

### Example 4: Feature Enablement
```nix
coachiq = {
  enable = true;
  settings = {
    features = {
      enableJ1939 = true;
      enableVectorSearch = false;  # Explicitly disable
    };
  };
};
```

**Environment Variables Set:**
```bash
COACHIQ_ENVIRONMENT=production
COACHIQ_J1939__ENABLED=true
COACHIQ_FEATURES__ENABLE_VECTOR_SEARCH=false
```

**Note:** `enableVectorSearch` is set because we're explicitly disabling a feature that's enabled by default.

## Complete Mapping Reference

| Nix Option | Condition | Environment Variable | Notes |
|------------|-----------|---------------------|-------|
| `server.host` | If not null | `COACHIQ_SERVER__HOST` | Backend default: "0.0.0.0" |
| `server.port` | If not null | `COACHIQ_SERVER__PORT` | Backend default: 8000 |
| `server.workers` | If not null | `COACHIQ_SERVER__WORKERS` | Backend default: 1 |
| `server.reload` | Never set | - | Controlled by environment detection |
| `server.debug` | If true | `COACHIQ_SERVER__DEBUG` | Backend default: false |
| `logging.level` | If not "INFO" | `COACHIQ_LOGGING__LEVEL` | Only set if different from default |
| `logging.logFile` | If not null | `COACHIQ_LOGGING__LOG_FILE` | No backend default |
| `persistence.enabled` | If true | `COACHIQ_PERSISTENCE__ENABLED` | Backend default: false |
| `persistence.dataDir` | If enabled and not "/var/lib/coachiq" | `COACHIQ_PERSISTENCE__DATA_DIR` | Only if custom path |
| `features.enableJ1939` | If true | `COACHIQ_J1939__ENABLED` | Backend default: false |
| `features.enableVectorSearch` | If false | `COACHIQ_FEATURES__ENABLE_VECTOR_SEARCH` | Backend default: true |
| `features.enableApiDocs` | If false | `COACHIQ_FEATURES__ENABLE_API_DOCS` | Backend default: true |
| `canbus.bustype` | If not "virtual" | `COACHIQ_CAN__BUSTYPE` | Only if not default |
| `canbus.channels` | If not ["virtual0"] | `COACHIQ_CAN__INTERFACES` | Comma-separated |
| `cors.allowedOrigins` | If not ["*"] | `COACHIQ_CORS__ALLOW_ORIGINS` | Comma-separated |

## Special Cases

### Always Set Variables
These are always set by the NixOS module:
- `COACHIQ_ENVIRONMENT=production`

### Never Set Variables
These are intentionally not set to avoid conflicts:
- `COACHIQ_SERVER__RELOAD` - Let backend detect environment
- `COACHIQ_APP_NAME/VERSION` - Only if explicitly configured

### Complex Types
```nix
# Lists become comma-separated
canbus.channels = [ "can0" "can1" ];
# Results in: COACHIQ_CAN__INTERFACES=can0,can1

# Complex mappings use JSON
canbus.interfaceMappings = { house = "can0"; chassis = "can1"; };
# Results in: COACHIQ_CAN__INTERFACE_MAPPINGS='{"house":"can0","chassis":"can1"}'
```

## Verification Commands

### Check What Will Be Set
```bash
# Build the configuration
nixos-rebuild build

# Inspect the service file
cat /nix/store/*-unit-coachiq.service/coachiq.service | grep Environment
```

### Check Running Service
```bash
# View actual environment
systemctl show coachiq -p Environment

# Or more readable
systemctl show coachiq | grep -E '^Environment=' | tr ' ' '\n' | grep COACHIQ
```

### Debug Configuration Issues
```bash
# Test configuration without environment overrides
env -i $(which python) -c "from backend.core.config import get_settings; print(get_settings())"

# Test with specific overrides
COACHIQ_SERVER__PORT=9000 python -c "from backend.core.config import get_settings; print(get_settings().server.port)"
```

## Best Practices

1. **Start with minimal configuration** - Only set what you need
2. **Let backend defaults work** - They're tested and optimized
3. **Use null for "use default"** - Don't duplicate backend defaults
4. **Check effective configuration** - Use validation tools
5. **Avoid environment variable conflicts** - NixOS module handles precedence correctly

## Configuration Precedence Reminder

1. **Environment Variables** (highest) - Set by NixOS module
2. **SQLite Persistence** - User preferences
3. **Configuration Files** - YAML/JSON files
4. **Backend Defaults** (lowest) - In `backend/core/config.py`

The NixOS module only sets environment variables when needed, allowing lower precedence sources to work correctly.
