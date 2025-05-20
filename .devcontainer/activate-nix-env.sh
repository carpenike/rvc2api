#!/usr/bin/env bash
set -euo pipefail

# 1) Source Nix profile (so `nix` is on your PATH)
if [[ -f "$HOME/.nix-profile/etc/profile.d/nix.sh" ]]; then
  # shellcheck source=/dev/null
  . "$HOME/.nix-profile/etc/profile.d/nix.sh"
fi

# 2) Jump to your project and hand off to nix
echo "🚀 Activating Nix development environment…"
cd /workspace
exec nix develop
