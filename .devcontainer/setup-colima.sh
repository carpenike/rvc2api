#!/usr/bin/env bash
# setup-colima.sh
# Improved Colima setup script for rvc2api devcontainer

# --- OS CHECK ---
if [[ "$(uname)" != "Darwin" ]]; then
  echo "❌ This Colima setup script is intended for macOS only."
  exit 1
fi

# --- SHELL CHECK ---
if [ -n "$BASH_VERSION" ]; then
  : # running in bash, continue
else
  echo "❌ This script must be run with bash, not fish or another shell."
  echo "   Please run: bash $0"
  exit 1
fi

set -euo pipefail

# ===== CONFIGURATION =====
DESIRED_CPUS=2
DESIRED_MEMORY=6 # in GB (integer, no suffix)
DESIRED_MEMORY_STR="${DESIRED_MEMORY}g" # for display only
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# ===== FUNCTIONS =====
function colima_status_json() {
  colima status --json 2>/dev/null || echo '{}'
}

function get_colima_field() {
  local field="$1"
  colima_status_json | grep -o '"'"$field"'": *[0-9]*' | grep -o '[0-9]\+' || echo 0
}

function get_colima_memory() {
  colima_status_json | grep -o '"memory": *[0-9]*' | grep -o '[0-9]\+' || echo 0
}

function is_colima_running() {
  colima status 2>/dev/null | grep -q 'Running'
}

function is_colima_installed() {
  command -v colima >/dev/null 2>&1
}

function ensure_colima_stopped() {
  if is_colima_running; then
    echo "🛑 Stopping Colima..."
    colima stop || true
  fi
}

function start_colima_with_resources() {
  echo "🚀 Starting Colima with ${DESIRED_CPUS} CPUs and ${DESIRED_MEMORY_STR} RAM and virtiofs mount (vm-type=vz)..."
  colima start --cpu $DESIRED_CPUS --memory $DESIRED_MEMORY --vm-type=vz --mount-type=virtiofs
}

function check_colima_resources() {
  local cpus=$(get_colima_field cpu)
  local mem=$(get_colima_memory)
  if [[ $cpus -lt $DESIRED_CPUS || $mem -lt $DESIRED_MEMORY ]]; then
    echo "⚠️  Colima is running with insufficient resources: CPUs=$cpus, Memory=${mem}GB"
    echo "   Required: CPUs=$DESIRED_CPUS, Memory=${DESIRED_MEMORY}GB"
    echo "   You should stop Colima and restart with:"
    echo "     colima stop && colima start --cpu $DESIRED_CPUS --memory $DESIRED_MEMORY --vm-type=vz --mount-type=virtiofs"
    echo "   (Always use --vm-type=vz --mount-type=virtiofs for best file performance on Apple Silicon)"
    return 1
  fi
  return 0
}

# ===== MAIN LOGIC =====

if ! is_colima_installed; then
  echo "❌ Colima is not installed. Please install Colima and try again."
  exit 1
fi

if is_colima_running; then
  echo "✅ Colima is running. Checking resources..."
  if ! check_colima_resources; then
    echo "⚠️  Please restart Colima with the correct resources."
  else
    echo "✅ Colima resources are sufficient."
  fi
else
  echo "ℹ️  Colima is not running. Starting with desired resources..."
  start_colima_with_resources
fi

# Set Docker context to Colima
if docker context ls | grep -q '^colima'; then
  echo "🔄 Setting Docker context to 'colima'..."
  docker context use colima
else
  echo "⚠️  Docker context 'colima' not found. Please check your Docker/Colima installation."
fi

# Check Docker connection
if ! docker info >/dev/null 2>&1; then
  echo "❌ Docker is not running or not connected to Colima."
  exit 1
else
  echo "✅ Successfully connected to Docker."
fi

# Only attempt Docker operations if Docker is running
if docker info >/dev/null 2>&1; then
    echo "🔍 Checking that base image contains required commands..."
    docker pull mcr.microsoft.com/devcontainers/base:debian >/dev/null 2>&1 || {
        echo "⚠️ Could not pull base image. Internet connection issues?"
    }
    CONTAINER_NAME="rvc2api-verify-$(date +%s)"
    if docker run --name "$CONTAINER_NAME" --rm -d mcr.microsoft.com/devcontainers/base:debian sleep 10 >/dev/null 2>&1; then
        MISSING=""
        for cmd in id sleep bash find; do
            if ! docker exec "$CONTAINER_NAME" which $cmd >/dev/null 2>&1; then
                MISSING="$MISSING $cmd"
            fi
        done
        docker stop "$CONTAINER_NAME" >/dev/null 2>&1 || true
        if [ -n "$MISSING" ]; then
            echo "⚠️ WARNING: Base container is missing critical commands:$MISSING"
            echo "   This will cause the devcontainer to fail. Updating the devcontainer.json..."
            if grep -q "multiUser.*true" "$PROJECT_DIR/.devcontainer/devcontainer.json" || ! grep -q "multiUser.*false" "$PROJECT_DIR/.devcontainer/devcontainer.json"; then
                echo "🔧 Setting Nix multiUser=false in devcontainer.json..."
                sed -i.bak 's/"installNixFlakes": true,/"installNixFlakes": true,\n      "multiUser": false,/' "$PROJECT_DIR/.devcontainer/devcontainer.json"
                rm -f "$PROJECT_DIR/.devcontainer/devcontainer.json.bak"
            fi
        else
            echo "✅ Base container contains all required commands."
        fi
    else
        echo "⚠️ Could not create test container. Skipping command checks."
        if grep -q "multiUser.*true" "$PROJECT_DIR/.devcontainer/devcontainer.json" || ! grep -q "multiUser.*false" "$PROJECT_DIR/.devcontainer/devcontainer.json"; then
            echo "🔧 Setting Nix multiUser=false in devcontainer.json as a precaution..."
            sed -i.bak 's/"installNixFlakes": true,/"installNixFlakes": true,\n      "multiUser": false,/' "$PROJECT_DIR/.devcontainer/devcontainer.json"
            rm -f "$PROJECT_DIR/.devcontainer/devcontainer.json.bak"
        fi
    fi
fi

echo ""
echo "🚗 Setting up vCAN interfaces in Colima VM..."
# Create a temporary script to run inside the VM for vCAN setup
VCAN_SCRIPT=$(mktemp)
cat > "$VCAN_SCRIPT" << 'EOF'
#!/bin/bash
set -e

echo "📦 Installing Linux headers..."
sudo apt-get update
sudo apt-get install -y linux-headers-$(uname -r) build-essential

echo "🔄 Setting up vcan kernel module..."
# Check if vcan module is already loaded
if lsmod | grep -q "^vcan "; then
    echo "✅ vcan module is already loaded."
else
    echo "🔧 Loading vcan module..."
    sudo modprobe vcan
    echo "✅ vcan module loaded."
fi

# Check if vcan is already in /etc/modules
if grep -q "^vcan" /etc/modules 2>/dev/null; then
    echo "✅ vcan is already configured to load at startup."
else
    echo "🔧 Configuring vcan to load at startup..."
    echo "vcan" | sudo tee -a /etc/modules > /dev/null
    echo "✅ vcan configured to load at startup."
fi

# Setup vcan interfaces
echo "🔧 Setting up vcan interfaces..."
# Check if vcan0 exists
if ip link show vcan0 &> /dev/null; then
    echo "✅ vcan0 interface already exists."
else
    sudo ip link add dev vcan0 type vcan
    sudo ip link set up vcan0
    echo "✅ Created vcan0 interface."
fi

# Check if vcan1 exists
if ip link show vcan1 &> /dev/null; then
    echo "✅ vcan1 interface already exists."
else
    sudo ip link add dev vcan1 type vcan
    sudo ip link set up vcan1
    echo "✅ Created vcan1 interface."
fi

# Create a systemd service to ensure vcan interfaces are created at boot
if [ -f /etc/systemd/system/vcan-setup.service ]; then
    echo "✅ vcan-setup.service already exists."
else
    echo "🔧 Creating systemd service for vcan interfaces..."
    cat << 'SYSTEMD' | sudo tee /etc/systemd/system/vcan-setup.service > /dev/null
[Unit]
Description=Setup vcan interfaces
After=network.target

[Service]
Type=oneshot
ExecStart=/bin/bash -c "ip link add dev vcan0 type vcan || true; ip link set up vcan0; ip link add dev vcan1 type vcan || true; ip link set up vcan1"
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
SYSTEMD

    sudo systemctl daemon-reload
    sudo systemctl enable vcan-setup.service
    sudo systemctl start vcan-setup.service
    echo "✅ Created and enabled vcan-setup.service."
fi

# Display the status of the interfaces
echo "📊 vcan interfaces status:"
ip -details link show vcan0
ip -details link show vcan1

# Test can-utils if available
if command -v cansend &> /dev/null; then
    echo "🧪 Testing vcan with can-utils..."
    # Send a test frame to vcan0
    cansend vcan0 123#DEADBEEF
    echo "✅ Test message sent to vcan0."
else
    echo "⚠️ can-utils not installed. Installing now..."
    sudo apt-get install -y can-utils
    if [ $? -eq 0 ]; then
        echo "✅ can-utils installed. Testing vcan with can-utils..."
        cansend vcan0 123#DEADBEEF
        echo "✅ Test message sent to vcan0."
    else
        echo "❌ Failed to install can-utils. You might need to install it manually."
    fi
fi

echo "🏁 vcan setup completed successfully!"
EOF

# Make the script executable
chmod +x "$VCAN_SCRIPT"

# Copy the script to Colima VM
echo "📄 Copying setup script to Colima VM..."
colima ssh -- mkdir -p /tmp/vcan_setup
colima ssh cp "$VCAN_SCRIPT" --to-host /tmp/vcan_setup/setup.sh

# Execute the script in Colima VM
echo "🚀 Running vcan setup script in Colima VM..."
colima ssh -- sudo bash /tmp/vcan_setup/setup.sh || {
    echo "⚠️ vcan setup encountered some issues. You may need to run scripts/setup_colima_vcan.sh directly."
}

# Clean up the temporary script
rm "$VCAN_SCRIPT"

echo ""
echo "🏁 Colima setup completed."
echo ""
echo "📋 Next steps:"
echo "1. Open this project in VS Code"
echo "2. Run the 'Dev Containers: Reopen in Container' command"
echo "3. If container fails to start, try the following:"
echo "   - Check that Docker context is set to colima: docker context use colima"
echo "   - Make sure devcontainer.json has 'multiUser: false' for Nix feature"
echo "   - If using Colima, ensure it's running: colima status"
echo "   - Run VS Code command: 'Dev Containers: Rebuild Without Cache'"
echo "4. For specific Nix errors about 'command not found', rebuild with Nix multiUser mode disabled"
echo "5. For other issues, see .devcontainer/TROUBLESHOOTING.md"
echo ""
echo "🔍 Recommended VS Code extensions for debugging container issues:"
echo "- Dev Containers"
echo "- Docker"

# Always make sure rvc2api/.devcontainer/devcontainer.json has multiUser=false
if [ -f "$PROJECT_DIR/.devcontainer/devcontainer.json" ]; then
    if grep -q "multiUser.*true" "$PROJECT_DIR/.devcontainer/devcontainer.json" || ! grep -q "multiUser.*false" "$PROJECT_DIR/.devcontainer/devcontainer.json"; then
        echo ""
        echo "🔧 Setting Nix multiUser=false in devcontainer.json to fix common startup issues..."
        sed -i.bak 's/"installNixFlakes": true,/"installNixFlakes": true,\n      "multiUser": false,/' "$PROJECT_DIR/.devcontainer/devcontainer.json"
        rm -f "$PROJECT_DIR/.devcontainer/devcontainer.json.bak"
        echo "✅ Updated devcontainer.json"
    fi
fi

exit 0
