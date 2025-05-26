#!/usr/bin/env bash
set -euo pipefail
echo "🚀 Activating Nix development environment…"
cd /workspace
exec nix develop
