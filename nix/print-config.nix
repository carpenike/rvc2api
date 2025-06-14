# Helper to print current CoachIQ configuration
# Usage: nix eval -f print-config.nix --json | jq

{ pkgs ? import <nixpkgs> {}, config }:

let
  # Extract just the coachiq settings
  coachiqConfig = config.coachiq.settings or {};

  # Helper to show which values are set vs defaults
  showConfigWithDefaults = settings:
    builtins.mapAttrs (name: value:
      if value == null
      then "← uses backend default"
      else value
    ) settings;

in {
  # Show current configuration
  current = showConfigWithDefaults coachiqConfig;

  # Show which environment variables would be set
  environmentVariables = builtins.attrNames (
    builtins.filterAttrs (n: v: v != null) {
      COACHIQ_SERVER__HOST = coachiqConfig.server.host or null;
      COACHIQ_SERVER__PORT = if (coachiqConfig.server.port or null) != null then toString coachiqConfig.server.port else null;
      # ... etc
    }
  );

  # Show backend defaults for reference
  backendDefaults = {
    server = {
      host = "0.0.0.0";
      port = 8000;
      workers = 1;
    };
    logging = {
      level = "INFO";
    };
    # ... etc
  };
}
