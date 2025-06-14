# Getting Started with CoachIQ on NixOS

This guide will help you deploy CoachIQ using the NixOS module with minimal configuration.

## Quick Start

### Bare Minimum Configuration

The absolute minimum configuration needed to run CoachIQ:

```nix
# /etc/nixos/configuration.nix
{ config, pkgs, ... }:

{
  imports = [
    # Your other imports...
    "${fetchTarball "https://github.com/yourusername/coachiq/archive/main.tar.gz"}/flake.nix"
  ];

  # Enable CoachIQ service
  coachiq.enable = true;
}
```

This bare minimum configuration will:
- Install and start the CoachIQ service
- Use all backend defaults (no environment variables set)
- Bind to `0.0.0.0:8000` (backend default)
- Create a systemd service with proper security hardening
- Set up a `coachiq` user and group
- Create directory structure under `/var/lib/coachiq`:
  - `/var/lib/coachiq/reference/` - Read-only RV-C specs (managed by Nix)
  - `/var/lib/coachiq/database/` - SQLite databases
  - `/var/lib/coachiq/config/` - User configuration
  - And other user data directories

### Basic Production Configuration

For a typical production deployment:

```nix
{ config, pkgs, ... }:

{
  coachiq = {
    enable = true;

    settings = {
      # Bind to localhost only (reverse proxy recommended)
      server.host = "127.0.0.1";

      # Enable persistence for production
      persistence.enabled = true;

      # Configure CAN interfaces
      canbus.channels = [ "can0" "can1" ];
    };
  };

  # If using hardware CAN interfaces
  boot.kernelModules = [ "can" "can_raw" "can_dev" ];

  # If using USB CAN adapters
  services.udev.packages = [ pkgs.can-utils ];
}
```

### Configuration with Custom Features

Enable specific features and protocols:

```nix
{ config, pkgs, ... }:

{
  coachiq = {
    enable = true;

    settings = {
      # Custom app branding
      appName = "My RV Control System";

      # Server configuration
      server = {
        host = "0.0.0.0";
        port = 8080;
      };

      # Enable specific features
      features = {
        enableJ1939 = true;
        enableFirefly = true;
        enableAdvancedDiagnostics = true;
      };

      # Protocol-specific settings
      j1939 = {
        sourceAddress = 128;
        preferredBaudRate = 250000;
      };
    };
  };
}
```

## Understanding Environment Variables

When you set a Nix option, it becomes an environment variable only if it differs from the backend default:

### Example 1: Using Backend Defaults
```nix
coachiq.settings = {
  # No server configuration provided
};
```

Results in NO environment variables being set. The backend will use its defaults:
- Host: `0.0.0.0`
- Port: `8000`
- Workers: `1`

### Example 2: Overriding Specific Values
```nix
coachiq.settings = {
  server.port = 8080;  # Different from default
};
```

Results in only one environment variable:
```bash
COACHIQ_SERVER__PORT=8080
```

The backend will still use its defaults for `host` and `workers`.

### Example 3: Complete Override
```nix
coachiq.settings = {
  server = {
    host = "192.168.1.100";
    port = 9000;
    workers = 4;
  };
};
```

Results in:
```bash
COACHIQ_SERVER__HOST=192.168.1.100
COACHIQ_SERVER__PORT=9000
COACHIQ_SERVER__WORKERS=4
```

## Viewing Configuration Options

### 1. Check Available Options
```bash
# List all CoachIQ module options
nixos-option coachiq

# Check specific option
nixos-option coachiq.settings.server.port
```

### 2. View Module Documentation
```bash
# Generate HTML documentation
nix-build '<nixpkgs/nixos/release.nix>' -A options

# Or use man pages (if available)
man configuration.nix
```

### 3. Use the Example Configuration
See `nix/example-config.nix` for all available options with descriptions.

## Debugging Configuration

### Check What Environment Variables Are Set
```bash
# View the actual systemd service
systemctl cat coachiq

# See only environment variables
systemctl show coachiq | grep -E '^Environment='
```

### View Effective Configuration
```bash
# Connect to the running service
curl http://localhost:8000/api/admin/config

# Or use the validation script
/run/current-system/sw/bin/coachiq-validate-config
```

### Common Patterns

#### Pattern 1: Minimal Override
Only set what you need to change:
```nix
coachiq.settings = {
  # Only override specific values
  server.port = 8080;
  features.enableJ1939 = true;
};
```

#### Pattern 2: Security-First
For exposed services:
```nix
coachiq.settings = {
  server.host = "127.0.0.1";  # Localhost only
  security.secretKeyFile = "/run/secrets/coachiq-jwt";
  cors.allowedOrigins = [ "https://my-domain.com" ];
};
```

#### Pattern 3: Development Mode
For development environments:
```nix
coachiq.settings = {
  server = {
    reload = true;
    debug = true;
  };
  logging.level = "DEBUG";
  canbus = {
    bustype = "virtual";
    channels = [ "vcan0" ];
  };
};
```

## Backend Defaults Reference

The backend defines these defaults (in `backend/core/config.py`):

| Setting | Backend Default | Environment Variable |
|---------|----------------|---------------------|
| server.host | "0.0.0.0" | COACHIQ_SERVER__HOST |
| server.port | 8000 | COACHIQ_SERVER__PORT |
| server.workers | 1 | COACHIQ_SERVER__WORKERS |
| server.reload | false | COACHIQ_SERVER__RELOAD |
| logging.level | "INFO" | COACHIQ_LOGGING__LEVEL |
| persistence.enabled | false | COACHIQ_PERSISTENCE__ENABLED |
| persistence.dataDir | "/var/lib/coachiq" | COACHIQ_PERSISTENCE__DATA_DIR |
| features.enableVectorSearch | true | COACHIQ_FEATURES__ENABLE_VECTOR_SEARCH |
| features.enableApiDocs | true | COACHIQ_FEATURES__ENABLE_API_DOCS |

## Migration from Docker/Systemd

If migrating from an existing deployment:

1. **Extract current configuration:**
   ```bash
   ./scripts/migrate-to-nix.sh
   ```

2. **Review generated `coachiq-config.nix`**

3. **Test in development:**
   ```bash
   nixos-rebuild build-vm
   ./result/bin/run-nixos-vm
   ```

4. **Deploy to production:**
   ```bash
   nixos-rebuild switch
   ```

## Next Steps

- See [Configuration Guide](configuration-guide.md) for complete options
- Check [nix/example-config.nix](../nix/example-config.nix) for advanced examples
- Use `coachiq-validate-config` to verify your setup
- Monitor with `systemctl status coachiq` and `journalctl -u coachiq -f`

## Key Principles

1. **Null means "use backend default"** - Don't set options unless you need to override
2. **Environment variables override everything** - They have highest precedence
3. **Type safety at build time** - Nix validates configuration before deployment
4. **Security by default** - Service runs with minimal privileges
5. **No duplicate defaults** - Backend is the single source of truth for defaults
