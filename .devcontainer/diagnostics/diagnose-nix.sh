#!/bin/bash
# diagnose-nix.sh - Improved diagnostics for Nix installation issues

# Don't exit on errors
set +e

echo "🔍 Running comprehensive Nix diagnostics..."

# Check if nix command exists in PATH
echo "🔍 Checking for nix command..."
if command -v nix >/dev/null; then
  echo "✅ nix command found: $(which nix)"
  echo "   Version: $(nix --version)"
else
  echo "❌ nix command not found in PATH"
  echo "   Current PATH: $PATH"
fi

# Check Nix store directory
echo "🔍 Checking Nix store directory..."
if [ -d "/nix" ]; then
  echo "✅ /nix directory exists"
  ls -la /nix

  echo "   Number of items in /nix/store: $(ls -1 /nix/store 2>/dev/null | wc -l || echo 'Cannot access')"
else
  echo "❌ /nix directory does not exist"
fi

# Check Nix configuration files
echo "🔍 Checking Nix configuration files..."
for conf_file in "/etc/nix/nix.conf" "$HOME/.config/nix/nix.conf"; do
  if [ -f "$conf_file" ]; then
    echo "✅ $conf_file exists:"
    cat "$conf_file"
  else
    echo "❌ $conf_file does not exist"
  fi
done

# Check Nix profile setup
echo "🔍 Checking Nix profiles..."
if [ -e "/nix/var/nix/profiles/default" ]; then
  echo "✅ Default Nix profile exists"
else
  echo "❌ Default Nix profile does not exist"
fi

if [ -e "$HOME/.nix-profile" ]; then
  echo "✅ User Nix profile exists: $(readlink -f $HOME/.nix-profile)"
  ls -la $HOME/.nix-profile
else
  echo "❌ User Nix profile does not exist"
fi

# Check Nix daemon status
echo "🔍 Checking Nix daemon status..."
if pgrep -f nix-daemon >/dev/null; then
  echo "✅ nix-daemon is running: $(pgrep -fa nix-daemon | head -n 1)"
else
  echo "❌ nix-daemon is not running"

  # Check if we're using a single-user install
  if [ -e "$HOME/.nix-profile/etc/profile.d/nix.sh" ]; then
    echo "   (This may be normal for a single-user installation)"
  fi
fi

# Check shell integration
echo "🔍 Checking shell integration..."
if grep -q "nix-daemon.sh\|nix.sh" "$HOME/.bashrc"; then
  echo "✅ Nix integration found in .bashrc"
  grep -n "nix-daemon.sh\|nix.sh" "$HOME/.bashrc"
else
  echo "❌ No Nix integration found in .bashrc"
fi

if grep -q "nix-daemon.sh\|nix.sh" "$HOME/.profile"; then
  echo "✅ Nix integration found in .profile"
  grep -n "nix-daemon.sh\|nix.sh" "$HOME/.profile"
else
  echo "❌ No Nix integration found in .profile"
fi

# Try to locate any nix binaries on the system
echo "🔍 Looking for Nix binaries..."
NIX_BINARIES=$(find /nix -name nix -type f -executable 2>/dev/null)
if [ -n "$NIX_BINARIES" ]; then
  echo "✅ Found Nix binaries:"
  echo "$NIX_BINARIES"
else
  echo "❌ No Nix binaries found"
fi

# Check for common nix commands
echo "🔍 Testing core Nix functionality..."
for cmd in nix nix-env nix-channel nix-store; do
  if command -v $cmd >/dev/null; then
    echo "✅ $cmd is available: $(which $cmd)"
  else
    echo "❌ $cmd is not available"
  fi
done

# Check for flakes support
if command -v nix >/dev/null; then
  echo "🔍 Testing Nix flakes support..."
  if nix --version | grep -q "nix.*2."; then
    echo "✅ Nix version supports flakes"

    TEST_DIR=$(mktemp -d)
    cd $TEST_DIR
    echo "{ description = \"test\"; outputs = { self }: { }; }" > flake.nix

    if nix flake check 2>/dev/null; then
      echo "✅ Flakes functionality is working"
    else
      echo "❌ Flakes functionality is not working"
    fi

    rm -rf $TEST_DIR
  else
    echo "❌ Nix version might not support flakes"
  fi
fi

# Provide recommendations
echo ""
echo "🔧 Recommendations:"
if ! command -v nix >/dev/null; then
  if [ -n "$NIX_BINARIES" ]; then
    NIX_DIR=$(dirname "$(echo "$NIX_BINARIES" | head -n 1)")
    echo "1. Add Nix to your PATH: export PATH=\"$NIX_DIR:\$PATH\""
    echo "2. Add this line to ~/.bashrc and ~/.profile"
    echo "3. Restart your shell or run 'source ~/.bashrc'"
  else
    echo "1. Run the fixed Nix installation script: /workspace/.devcontainer/scripts/setup-nix.sh.new"
    echo "2. Restart your shell or container after installation"
  fi
elif ! nix flake check 2>/dev/null; then
  echo "1. Enable flakes in Nix configuration:"
  echo "   echo 'experimental-features = nix-command flakes' >> ~/.config/nix/nix.conf"
fi

echo ""
echo "🔍 Nix diagnostics completed"
