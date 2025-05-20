# DevContainer Environment

This directory contains the configuration for the VS Code DevContainer development environment for the rvc2api project.

## Important Update: Nix Installation Fix

A fix for Nix installation issues has been implemented. If you're experiencing problems with Nix in the container:

1. Run the migration script: `./.devcontainer/migrate-nix-fix.sh`
2. Rebuild the DevContainer using "Dev Containers: Rebuild Without Cache"
3. See `NIX-FIX-NOTES.md` for details about the changes

## Container Structure

The container environment uses a streamlined structure organized by lifecycle phase:

```plaintext
.devcontainer/
├── devcontainer.json           # Main configuration file
├── NIX-FIX-NOTES.md            # Documentation for Nix fixes
├── migrate-nix-fix.sh          # Script to apply Nix fixes
├── lifecycle/                  # Container lifecycle scripts
│   ├── initialize.sh           # Run before container creation (on host)
│   ├── on-create.sh            # Run when container is created
│   ├── post-create.sh          # Run after container creation
│   └── post-start.sh           # Run when container starts
├── scripts/                    # Utility scripts
│   ├── setup-nix.sh            # Set up Nix package manager
│   ├── setup-vcan.sh           # Set up virtual CAN interfaces
│   └── setup-dev-tools.sh      # Set up development tools
├── diagnostics/                # Diagnostic tools
│   ├── diagnose-nix.sh         # Diagnose Nix issues
│   └── diagnose-vcan.sh        # Diagnose vcan interface issues
├── config/                     # Configuration files
│   └── env.sh                  # Environment variables
├── nix-store/                  # Persistent Nix store directory
├── nix-profile/                # Persistent Nix profile directory
└── home-cache/                 # Home directory cache
```

## Getting Started

1. **Prerequisites**:

   - Visual Studio Code with Remote Development Extension Pack
   - Docker (Docker Desktop or Colima on macOS)
   - Git

2. **Initial Setup**:

   - For macOS users with Colima: Run `.devcontainer/setup-colima.sh` to configure Colima optimally
   - For Docker Desktop users: No additional setup needed

3. **Starting the DevContainer**:
   - Open VS Code in the project directory
   - Click on the Remote Development icon in the bottom left corner
   - Select "Reopen in Container"

## Troubleshooting

### Common Issues

#### Nix not available in container

If `nix` commands are not working in the container:

1. Apply the Nix fix: `./.devcontainer/migrate-nix-fix.sh`
2. Rebuild the container with "Dev Containers: Rebuild Without Cache"
3. Check logs at `/workspace/devcontainer_startup.log` and `/workspace/nix_setup.log`

For other issues, refer to the detailed guides in `TROUBLESHOOTING.md`.

## Container Setup

The container is automatically set up with:

1. **Nix package manager** with flakes enabled
2. **Virtual CAN interfaces** (when kernel module is available)
3. **Development tools** like Git, Node.js, and Python
4. **VS Code extensions** for improved development

## Verifying CAN Interface Availability

You can verify that virtual CAN interfaces are available and properly configured:

```bash
# Check for available CAN interfaces
ip link show | grep -i can

# Expected output should show at least vcan0
# Example output:
#   X: vcan0: <NOARP,UP,LOWER_UP> mtu 72 qdisc noqueue state UNKNOWN mode DEFAULT group default qlen 1000
```

If virtual CAN interfaces are not available, run the diagnostics script:

```bash
/workspace/.devcontainer/diagnostics/diagnose-vcan.sh
```
