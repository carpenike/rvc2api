# DevContainer Environment Setup

This directory contains the configuration for the VS Code DevContainer development environment.

## Optimized Development Experience

The DevContainer configuration has been optimized for both performance and stability. Key improvements include:

- **Cached filesystem operations** for better performance
- **Resource limits** to prevent container crashes
- **Nix optimizations** for faster builds
- **VS Code settings** to improve editor performance
- **Persistent Nix store** to prevent unnecessary rebuilds

For detailed performance optimization tips, see [PERFORMANCE.md](./PERFORMANCE.md).

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
#   X: vcan1: <NOARP,UP,LOWER_UP> mtu 72 qdisc noqueue state UNKNOWN mode DEFAULT group default qlen 1000
```

If you're using Colima with systemd-configured interfaces on the host VM, the interfaces should be automatically accessible in your DevContainer due to the `--network=host` configuration.

## Manual Setup Process (For host systems)

If you prefer to set up your environment manually or are using a non-DevContainer setup:

### Colima Environment (macOS with Docker)

1. Follow the install process for colima and start the VM:

   ```bash
   # Install colima (if not already installed)
   brew install colima docker docker-credential-helper

   # Start colima with recommended settings
   colima start --cpu 4 --memory 8 --disk 40 --mount-type sshfs

   # Verify Docker is working with Colima
   docker info | grep -i runtime
   ```

2. SSH into the Colima VM to configure vcan:

   ```bash
   colima ssh
   ```

3. Ensure the Linux headers are installed so the vcan module can be loaded:

   ```bash
   sudo apt update
   sudo apt install -y build-essential linux-headers-$(uname -r) linux-modules-extra-$(uname -r)
   ```

4. Ensure the vcan module is loaded and the interface starts at boot:

   ```bash
   # Load vcan module
   sudo modprobe vcan

   # Create systemd service for vcan0
   sudo tee /etc/systemd/system/vcan0.service <<'EOF'
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
   EOF

   # Create systemd service for vcan1 (if needed)
   sudo tee /etc/systemd/system/vcan1.service <<'EOF'
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
   EOF

   # Enable and start the services
   sudo systemctl enable vcan0.service
   sudo systemctl start vcan0.service
   sudo systemctl enable vcan1.service
   sudo systemctl start vcan1.service

   # Verify the interfaces are up
   ip link show | grep -i vcan
   ```

## Troubleshooting

If you encounter issues with the DevContainer:

1. For Colima users, see [COLIMA.md](./COLIMA.md) for specific optimization tips
2. For general performance tips, see [PERFORMANCE.md](./PERFORMANCE.md)
3. Ensure your Docker environment has sufficient resources allocated
4. Consider using the "Clone Repository in Container Volume..." approach for better performance

### CAN Interface Issues

If virtual CAN interfaces are not available in your DevContainer:

1. **Verify interfaces in host environment**:

   ```bash
   # On macOS with Colima
   colima ssh
   ip link show | grep -i vcan
   ```

2. **Check container networking**:

   ```bash
   # Inside DevContainer
   ifconfig -a | grep -i vcan    # or
   ip link show | grep -i vcan
   ```

3. **Ensure the container has proper network access**:

   - Verify that `--network=host` is in the `runArgs` section of `devcontainer.json`
   - For Colima users, make sure both the host VM and container networking is properly configured

4. **Manually create interfaces** if necessary:
   ```bash
   # Inside DevContainer (requires NET_ADMIN capability)
   sudo ip link add dev vcan0 type vcan
   sudo ip link set up vcan0
   ```
