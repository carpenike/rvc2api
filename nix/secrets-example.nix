# Example of secure secret management for CoachIQ
# DO NOT commit actual secrets to version control!

{ config, lib, pkgs, ... }:

{
  # Option 1: Using systemd credentials (recommended)
  systemd.services.coachiq = {
    serviceConfig = {
      LoadCredential = [
        "jwt-secret:/run/secrets/coachiq-jwt-secret"
        "smtp-password:/run/secrets/coachiq-smtp-password"
      ];
    };
    # Access in app via CREDENTIALS_DIRECTORY environment variable
  };

  # Option 2: Using agenix for secret management
  age.secrets = {
    coachiq-jwt-secret = {
      file = ./secrets/jwt-secret.age;
      owner = "coachiq";
      group = "coachiq";
    };
    coachiq-smtp-password = {
      file = ./secrets/smtp-password.age;
      owner = "coachiq";
      group = "coachiq";
    };
  };

  # Option 3: Using sops-nix
  sops.secrets = {
    "coachiq/jwt_secret" = {
      owner = "coachiq";
      group = "coachiq";
    };
    "coachiq/smtp_password" = {
      owner = "coachiq";
      group = "coachiq";
    };
  };

  # Configure CoachIQ to read secrets from files
  coachiq.settings = {
    # Instead of putting secrets directly in config:
    # security.secretKey = "NEVER DO THIS";

    # Use environment variables that point to secret files:
    security.secretKeyFile = config.age.secrets.coachiq-jwt-secret.path;

    notifications.smtp = {
      enabled = true;
      passwordFile = config.age.secrets.coachiq-smtp-password.path;
    };
  };

  # Option 4: For development/testing only - use hashedPassword
  # Generate with: mkpasswd -m sha-512
  coachiq.settings.security.secretKeyHash = "$6$rounds=10000$..."; # Example only
}
