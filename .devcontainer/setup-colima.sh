#!/usr/bin/env bash
# setup-colima.sh
# Improved Colima setup script for rvc2api devcontainer (with Colima SSH config + SCP)

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
DESIRED_MEMORY=6  # in GB (integer, no suffix)
DESIRED_MEMORY_STR="${DESIRED_MEMORY}g"  # for display only
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# ===== FUNCTIONS =====
colima_status_json() { colima status --json 2>/dev/null || echo '{}'; }
get_colima_field() {
  colima_status_json | grep -o "\"$1\": *[0-9]*" | grep -o '[0-9]\+' || echo 0
}
get_colima_memory() { get_colima_field memory; }
is_colima_running() { colima status 2>/dev/null | grep -q Running; }
is_colima_installed() { command -v colima >/dev/null; }
ensure_colima_stopped() { is_colima_running && colima stop || true; }
start_colima_with_resources() {
  colima start \
    --cpu "$DESIRED_CPUS" \
    --memory "$DESIRED_MEMORY" \
    --vm-type vz \
    --mount-type virtiofs
}
check_colima_resources() {
  local cpus mem
  cpus=$(get_colima_field cpu)
  mem=$(get_colima_field memory)
  if (( cpus < DESIRED_CPUS || mem < DESIRED_MEMORY )); then
    echo "⚠️  Insufficient: CPUs=$cpus (need $DESIRED_CPUS), Memory=${mem}GB (need ${DESIRED_MEMORY}GB)"
    return 1
  fi
  return 0
}

# ===== PRE-REQUISITES =====
if ! is_colima_installed; then
  echo "❌ Please install Colima first."
  exit 1
fi

if ! command -v limactl >/dev/null; then
  echo "❌ limactl not found. Install Lima (e.g. brew install lima) and try again."
  exit 1
fi

# ===== COLIMA LIFECYCLE =====
if is_colima_running; then
  echo "✅ Colima is running."
  check_colima_resources || echo "⚠️  Restart Colima with correct resources if needed."
else
  echo "ℹ️  Starting Colima..."
  start_colima_with_resources
fi

# Docker context
docker context use colima 2>/dev/null && echo "🔄 Docker context set to colima."

# Quick docker sanity
docker info >/dev/null && echo "✅ Docker is up."

# ===== BUILD vCAN SCRIPT =====
VCAN_SCRIPT=$(mktemp)
trap 'rm -f "$VCAN_SCRIPT"' EXIT

cat >"$VCAN_SCRIPT" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

echo "📦 Installing headers & build-essential..."
sudo apt-get update
sudo apt-get install -y linux-headers-$(uname -r) build-essential linux-modules-extra-$(uname -r)

echo "🔄 vcan and can_dev modules will be loaded on next boot (added to /etc/modules-load.d/vcan.conf)"
echo -e "vcan\ncan_dev" | sudo tee /etc/modules-load.d/vcan.conf >/dev/null

echo "🔧 Creating vcan0 systemd service..."
sudo tee /etc/systemd/system/vcan0.service >/dev/null <<'SERVICE'
[Unit]
Description=Create and bring up vcan0
After=network.target

[Service]
Type=oneshot
ExecStart=/usr/sbin/ip link add dev vcan0 type vcan
ExecStart=/usr/sbin/ip link set up vcan0
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
SERVICE
sudo systemctl daemon-reload
sudo systemctl enable vcan0.service

echo "🔧 Creating vcan1 systemd service..."
sudo tee /etc/systemd/system/vcan1.service >/dev/null <<'SERVICE'
[Unit]
Description=Create and bring up vcan1
After=network.target

[Service]
Type=oneshot
ExecStart=/usr/sbin/ip link add dev vcan1 type vcan
ExecStart=/usr/sbin/ip link set up vcan1
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
SERVICE
sudo systemctl daemon-reload
sudo systemctl enable vcan1.service

echo "✅ Enabled vcan0.service and vcan1.service"

echo "🏁 vcan setup complete."
echo

echo "⚠️  Please run: colima restart"
echo "   This will reboot the Colima VM and enable vcan interfaces."
EOF

chmod +x "$VCAN_SCRIPT"

# ===== COPY + RUN via SSH/SCP (portable Colima method) =====
SSH_CONFIG=$(mktemp)
colima ssh-config > "$SSH_CONFIG"

echo "📄 Copying vcan script into Colima VM..."
scp -F "$SSH_CONFIG" "$VCAN_SCRIPT" colima:/tmp/vcan_setup.sh

echo "🚀 Executing vcan script inside VM..."
colima ssh -- sudo bash /tmp/vcan_setup.sh

rm -f "$SSH_CONFIG"

echo "🏁 All done!"
