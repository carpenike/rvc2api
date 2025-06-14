#!/usr/bin/env bash
# Helper script to migrate existing CoachIQ deployment to NixOS module

set -euo pipefail

echo "CoachIQ NixOS Migration Helper"
echo "=============================="
echo

# Function to extract current configuration
extract_current_config() {
    echo "Extracting current configuration..."

    # Check for .env file
    if [ -f .env ]; then
        echo "Found .env file"
        echo
        echo "Current environment variables:"
        grep "^COACHIQ_" .env | sort || true
    fi

    # Check for docker-compose.yml
    if [ -f docker-compose.yml ]; then
        echo
        echo "Found docker-compose.yml"
        # Extract environment section
        grep -A20 "environment:" docker-compose.yml | grep "COACHIQ_" || true
    fi

    # Check for systemd service
    if systemctl is-active coachiq >/dev/null 2>&1; then
        echo
        echo "Found running systemd service"
        systemctl show coachiq | grep "^Environment=" || true
    fi
}

# Generate Nix configuration from current setup
generate_nix_config() {
    echo
    echo "Generating Nix configuration..."

    cat > coachiq-config.nix << 'EOF'
# Generated CoachIQ NixOS configuration
# Review and adjust as needed

{ config, lib, pkgs, ... }:

{
  # Enable CoachIQ service
  coachiq.enable = true;

  coachiq.settings = {
    # TODO: Review and set these based on your current configuration

    server = {
      # host = "0.0.0.0";
      # port = 8000;
    };

    security = {
      # IMPORTANT: Use proper secret management!
      # secretKeyFile = "/run/secrets/coachiq-jwt";
    };

    persistence = {
      enabled = true;
      # dataDir = "/var/lib/coachiq";
    };

    # Add other settings based on your current configuration
  };
}
EOF

    echo "Generated coachiq-config.nix"
}

# Backup current data
backup_data() {
    echo
    echo "Backing up current data..."

    BACKUP_DIR="coachiq-backup-$(date +%Y%m%d-%H%M%S)"
    mkdir -p "$BACKUP_DIR"

    # Backup SQLite database if exists
    if [ -f /var/lib/coachiq/database/coachiq.db ]; then
        echo "Backing up SQLite database..."
        cp -p /var/lib/coachiq/database/coachiq.db "$BACKUP_DIR/"
    fi

    # Backup configuration files
    for file in .env docker-compose.yml config/coach_mapping.yml; do
        if [ -f "$file" ]; then
            echo "Backing up $file..."
            cp -p "$file" "$BACKUP_DIR/"
        fi
    done

    echo "Backup completed in $BACKUP_DIR"
}

# Main migration flow
main() {
    echo "This script will help you migrate to NixOS module configuration."
    echo
    read -p "Continue? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 1
    fi

    extract_current_config
    generate_nix_config
    backup_data

    echo
    echo "Migration preparation complete!"
    echo
    echo "Next steps:"
    echo "1. Review the generated coachiq-config.nix file"
    echo "2. Add proper secret management for sensitive values"
    echo "3. Test the configuration in a development environment"
    echo "4. Import the configuration in your NixOS configuration"
    echo "5. Run 'nixos-rebuild switch' to deploy"
    echo
    echo "For more information, see nix/example-config.nix"
}

main "$@"
