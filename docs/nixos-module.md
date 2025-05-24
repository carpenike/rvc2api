# NixOS Module Configuration for rvc2api

This document provides detailed configuration options for the `rvc2api` NixOS module, which allows you to manage the rvc2api service as part of your NixOS system configuration.

## Basic Usage

To use the `rvc2api` module in your NixOS configuration:

```nix
# In your configuration.nix or flake.nix
{
  imports = [
    # Other imports...
    inputs.rvc2api.nixosModules.rvc2api
  ];

  # Enable the service
  rvc2api = {
    enable = true;
    settings = {
      # Configuration options here
    };
  };
}
```

## Configuration Options

### Main Options

| Option    | Type    | Default                          | Description                |
| --------- | ------- | -------------------------------- | -------------------------- |
| `enable`  | boolean | `false`                          | Enable the rvc2api service |
| `package` | package | `self.packages.<system>.rvc2api` | The rvc2api package to use |

### Server Configuration

These settings control the API server.

| Option              | Type   | Default     | Description                                           |
| ------------------- | ------ | ----------- | ----------------------------------------------------- |
| `settings.host`     | string | `"0.0.0.0"` | Host IP to bind the API server to                     |
| `settings.port`     | int    | `8000`      | Port to run the API server on                         |
| `settings.logLevel` | string | `"INFO"`    | Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) |

### Controller Configuration

| Option                          | Type   | Default  | Description                      |
| ------------------------------- | ------ | -------- | -------------------------------- |
| `settings.controllerSourceAddr` | string | `"0xF9"` | Controller source address in hex |

### Pushover Integration

Pushover is used for sending notifications from the service.

| Option                       | Type           | Default | Description                        |
| ---------------------------- | -------------- | ------- | ---------------------------------- |
| `settings.pushover.enable`   | boolean        | `false` | Enable Pushover integration        |
| `settings.pushover.apiToken` | string         | `""`    | Pushover API token                 |
| `settings.pushover.userKey`  | string         | `""`    | Pushover user key                  |
| `settings.pushover.device`   | null or string | `null`  | Optional Pushover device name      |
| `settings.pushover.priority` | null or int    | `null`  | Optional Pushover message priority |

### UptimeRobot Integration

UptimeRobot is used for monitoring service health.

| Option                        | Type    | Default | Description                    |
| ----------------------------- | ------- | ------- | ------------------------------ |
| `settings.uptimerobot.enable` | boolean | `false` | Enable UptimeRobot integration |
| `settings.uptimerobot.apiKey` | string  | `""`    | UptimeRobot API key            |

### CAN Bus Configuration

These settings control how the service interacts with the RV's CAN bus.

| Option                     | Type            | Default       | Description                       |
| -------------------------- | --------------- | ------------- | --------------------------------- |
| `settings.canbus.channels` | list of strings | `[ "can0" ]`  | SocketCAN interfaces to listen on |
| `settings.canbus.bustype`  | string          | `"socketcan"` | Python-CAN bus type               |
| `settings.canbus.bitrate`  | int             | `500000`      | CAN bus bitrate                   |

### RV-C Spec and Device Mapping

These settings allow customizing the RV-C specification and device mapping files.

| Option                       | Type           | Default | Description                                 |
| ---------------------------- | -------------- | ------- | ------------------------------------------- |
| `settings.rvcSpecPath`       | null or string | `null`  | Override path to `rvc.json` (RVC spec file) |
| `settings.deviceMappingPath` | null or string | `null`  | Override path to device mapping file        |
| `settings.modelSelector`     | null or string | `null`  | Model selector for device mapping file      |
| `settings.userCoachInfoPath` | null or string | `null`  | Path to user coach info YAML file           |

### GitHub Integration

| Option                      | Type           | Default | Description                                                 |
| --------------------------- | -------------- | ------- | ----------------------------------------------------------- |
| `settings.githubUpdateRepo` | null or string | `null`  | GitHub repository to check for updates (format: owner/repo) |

## Example Configurations

### Basic Configuration

```nix
rvc2api = {
  enable = true;
  settings.canbus.channels = [ "can0" "can1" ];
};
```

### Complete Configuration

```nix
rvc2api = {
  enable = true;

  # Use a specific package version
  package = pkgs.rvc2api;

  settings = {
    # Server configuration
    host = "0.0.0.0";
    port = 8000;
    logLevel = "INFO";  # Or "DEBUG" for more verbose output

    # Controller configuration
    controllerSourceAddr = "0xF9";

    # Pushover notifications
    pushover = {
      enable = true;
      apiToken = "your-api-token";
      userKey = "your-user-key";
      device = "mydevice";
      priority = 1;
    };

    # UptimeRobot monitoring
    uptimerobot = {
      enable = true;
      apiKey = "your-api-key";
    };

    # CAN bus settings
    canbus = {
      channels = [ "can0" "vcan0" ];
      bustype = "socketcan";
      bitrate = 500000;
    };

    # Use a specific RV model's mapping file
    modelSelector = "2021_Entegra_Aspire_44R";

    # Or specify custom mapping paths
    # rvcSpecPath = "/path/to/custom/rvc.json";
    # deviceMappingPath = "/path/to/custom/coach_mapping.default.yml";

    # User coach information
    userCoachInfoPath = "/path/to/coach_info.yml";

    # GitHub update checker
    githubUpdateRepo = "carpenike/rvc2api";
  };
};
```

## Environment Variables

The NixOS module automatically sets up these environment variables for the systemd service:

| Environment Variable           | Derived From                                                   |
| ------------------------------ | -------------------------------------------------------------- |
| `ENABLE_PUSHOVER`              | `settings.pushover.enable`                                     |
| `PUSHOVER_API_TOKEN`           | `settings.pushover.apiToken`                                   |
| `PUSHOVER_USER_KEY`            | `settings.pushover.userKey`                                    |
| `PUSHOVER_DEVICE`              | `settings.pushover.device`                                     |
| `PUSHOVER_PRIORITY`            | `settings.pushover.priority`                                   |
| `ENABLE_UPTIMEROBOT`           | `settings.uptimerobot.enable`                                  |
| `UPTIMEROBOT_API_KEY`          | `settings.uptimerobot.apiKey`                                  |
| `CAN_CHANNELS`                 | `settings.canbus.channels` (comma-separated)                   |
| `CAN_BUSTYPE`                  | `settings.canbus.bustype`                                      |
| `CAN_BITRATE`                  | `settings.canbus.bitrate`                                      |
| `RVC2API_HOST`                 | `settings.host`                                                |
| `RVC2API_PORT`                 | `settings.port`                                                |
| `LOG_LEVEL`                    | `settings.logLevel`                                            |
| `CONTROLLER_SOURCE_ADDR`       | `settings.controllerSourceAddr`                                |
| `GITHUB_UPDATE_REPO`           | `settings.githubUpdateRepo`                                    |
| `CAN_MODEL_SELECTOR`           | `settings.modelSelector`                                       |
| `CAN_SPEC_PATH`                | `settings.rvcSpecPath`                                         |
| `CAN_MAP_PATH`                 | Complex logic based on `deviceMappingPath` and `modelSelector` |
| `RVC2API_USER_COACH_INFO_PATH` | `settings.userCoachInfoPath`                                   |

## Advanced Configuration

For advanced use cases, you might want to override the package to use a custom version:

```nix
rvc2api = {
  enable = true;
  package = pkgs.callPackage ./path/to/custom-rvc2api.nix {};
  # ...other settings
};
```

Or use inputs from a flake for package references:

```nix
rvc2api = {
  enable = true;
  package = inputs.rvc2api.packages.${pkgs.system}.rvc2api;
  # ...other settings
};
```
