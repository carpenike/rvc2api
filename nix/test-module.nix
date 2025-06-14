# Test the CoachIQ NixOS module configuration
# Run with: nix-build test-module.nix

{ nixpkgs ? <nixpkgs>, system ? builtins.currentSystem }:

let
  pkgs = import nixpkgs { inherit system; };

  # Import the flake's NixOS module
  coachiqModule = (import ../flake.nix).nixosModules.default;

  # Test configuration
  testConfig = {
    imports = [ coachiqModule ];

    coachiq.enable = true;
    coachiq.settings = {
      server.port = 8080;
      security.secretKey = "test-secret";
      features.enableJ1939 = true;
    };
  };

  # Evaluate the configuration
  evaluatedConfig = pkgs.lib.nixosSystem {
    inherit system;
    modules = [ testConfig ];
  };

in {
  # Show what environment variables would be set
  envVars = evaluatedConfig.config.systemd.services.coachiq.environment;

  # Validate that only configured values are set
  validation = {
    # Port should be set because user configured it
    portIsSet = evaluatedConfig.config.systemd.services.coachiq.environment ? COACHIQ_SERVER__PORT;

    # Host should NOT be set because user didn't configure it
    hostIsNotSet = !(evaluatedConfig.config.systemd.services.coachiq.environment ? COACHIQ_SERVER__HOST);
  };
}
