# CoachIQ Configuration Guide

## Configuration Precedence

CoachIQ uses a layered configuration system with the following precedence (highest to lowest):

1. **Environment Variables** - Always wins
2. **SQLite Persistence** - User preferences stored in database
3. **Configuration Files** - YAML/JSON files
4. **Backend Defaults** - Hardcoded in application

## Configuration Methods

### 1. Environment Variables

All settings can be configured via environment variables using the `COACHIQ_` prefix:

```bash
# Simple values
export COACHIQ_SERVER__PORT=8080
export COACHIQ_LOGGING__LEVEL=DEBUG

# Nested values use double underscore
export COACHIQ_FEATURES__ENABLE_J1939=true
export COACHIQ_RVC__ENABLE_ENCODER=false

# Lists use comma separation
export COACHIQ_CAN__INTERFACES=can0,can1,vcan0

# Complex mappings use JSON
export COACHIQ_CAN__INTERFACE_MAPPINGS='{"house":"can0","chassis":"can1"}'
```

### 2. NixOS Module

For NixOS deployments, use the provided module:

```nix
{
  coachiq.enable = true;
  coachiq.settings = {
    server.port = 8080;
    logging.level = "DEBUG";
    features.enableJ1939 = true;
  };
}
```

The Nix module provides:
- Type checking at build time
- Automatic systemd service generation
- Proper secret management integration
- Health checks and monitoring

### 3. Docker Compose

For Docker deployments:

```yaml
version: '3.8'
services:
  coachiq:
    image: coachiq:latest
    environment:
      COACHIQ_SERVER__PORT: 8080
      COACHIQ_PERSISTENCE__ENABLED: "true"
      COACHIQ_PERSISTENCE__DATA_DIR: /data
    volumes:
      - coachiq-data:/data
    devices:
      - /dev/can0:/dev/can0
```

### 4. Data Directory Structure

All CoachIQ data is stored under a single directory (default: `/var/lib/coachiq/`):

```
/var/lib/coachiq/
├── reference/          # Read-only reference data (managed by Nix)
│   ├── rvc.json       # RV-C protocol specification
│   ├── coach_mapping.default.yml
│   └── *.yml          # Coach-specific mappings
├── database/          # SQLite databases (user data)
├── backups/           # Automatic backups
├── config/            # User configuration overrides
├── themes/            # Custom UI themes
├── dashboards/        # Custom dashboards
└── logs/              # Application logs
```

**Directory Permissions:**
- `reference/` - Read-only, owned by root (managed by Nix tmpfiles)
- All other directories - Writable by coachiq user

**For Development:**
- Reference files are loaded from `./config/` in the project root
- Or from Python package via importlib.resources

**Environment Variables:**
- `COACHIQ_PERSISTENCE__DATA_DIR` - Change base directory (default: `/var/lib/coachiq`)
- `COACHIQ_RVC__CONFIG_DIR` - Override reference data location (rarely needed)

## Feature Management

Features can be enabled/disabled at multiple levels:

1. **feature_flags.yaml** - Define available features
2. **Environment/Nix** - Override enable/disable
3. **Runtime API** - Some features support runtime toggling

Example feature configuration:

```yaml
# backend/services/feature_flags.yaml
my_feature:
  enabled: false  # Default state
  core: false     # Is it required?
  depends_on:     # Dependencies
    - can_interface
    - rvc
  description: "My custom feature"
```

Override via environment:
```bash
export COACHIQ_FEATURES__ENABLE_MY_FEATURE=true
```

## Security Considerations

### Never Put Secrets in:
- Environment variables in scripts
- Nix configuration files
- Git repositories
- Docker images

### Instead Use:
- NixOS secrets management (agenix, sops-nix)
- Docker secrets
- Kubernetes secrets
- HashiCorp Vault
- Environment files with restricted permissions

### Example Secret Management:

```nix
# NixOS with agenix
coachiq.settings = {
  security.secretKeyFile = config.age.secrets.coachiq-jwt.path;
};
```

```bash
# Docker with secrets
docker secret create coachiq-jwt jwt.key
docker service create \
  --secret coachiq-jwt \
  --env COACHIQ_SECURITY__SECRET_KEY_FILE=/run/secrets/coachiq-jwt \
  coachiq:latest
```

## Validation and Debugging

### Check Current Configuration:
```bash
# Show effective configuration
poetry run python scripts/validate-config.py

# Test configuration without starting service
poetry run python -c "from backend.core.config import get_settings; print(get_settings())"
```

### Common Issues:

1. **Environment variable not taking effect**
   - Check spelling and case (use UPPER_SNAKE_CASE)
   - Ensure double underscore for nesting
   - Verify the variable is exported

2. **Type conversion errors**
   - Booleans: use "true"/"false" (lowercase)
   - Lists: use comma separation
   - Numbers: ensure no quotes in shell

3. **Nix module not applying**
   - Run `nixos-rebuild switch` not just `nixos-rebuild build`
   - Check systemd service: `systemctl status coachiq`
   - View logs: `journalctl -u coachiq -f`

## Migration Guide

See `scripts/migrate-to-nix.sh` for automated migration assistance.

## Reference

- Full environment variable list: `docs/environment-variables.md`
- Nix module options: `nix/example-config.nix`
- Backend defaults: `backend/core/config.py`
