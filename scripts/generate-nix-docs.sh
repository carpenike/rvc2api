#!/usr/bin/env bash
# Generate NixOS module documentation from the flake

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "Generating NixOS module documentation..."

# Use nix-doc or similar tool to generate docs
# For now, we'll create a simple extraction

cat > "$PROJECT_ROOT/docs/nix-module-options.md" << 'EOF'
# CoachIQ NixOS Module Options

This document lists all available configuration options for the CoachIQ NixOS module.

## Basic Usage

```nix
{
  coachiq.enable = true;
  coachiq.settings = {
    server.port = 8080;
    security.secretKey = "your-secret-key";
  };
}
```

## Complete Options Reference

Run `nix-instantiate --eval --strict -E '(import ./flake.nix).nixosModules.default.options' --json | jq` to see all options.

EOF

# If nix is available, generate actual options
if command -v nix &> /dev/null; then
  echo "Extracting option definitions from flake..."
  # This would require more complex parsing, but the idea is to extract from the flake
fi

echo "Documentation generated at docs/nix-module-options.md"
