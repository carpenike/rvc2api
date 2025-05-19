# Colima Optimization Guide for rvc2api

This document provides specific guidance for optimizing Colima for use with the rvc2api project DevContainer on macOS.

## Recommended Colima Configuration

### For New Colima Installations

If you haven't initialized Colima yet, use these settings for optimal performance:

```bash
colima start --cpu 4 --memory 8 --disk 60 --vm-type=vz --mount-type=virtiofs
```

These settings use:

- 4 CPU cores and 8GB RAM (adjust based on your Mac's specifications)
- 60GB disk space
- Apple's Virtualization Framework (vz) - much faster than QEMU
- VirtioFS for faster filesystem performance (requires macOS Ventura or newer)

### For Existing Colima Installations

> **Important Note**: The `vm-type` and `mount-type` parameters **cannot** be changed after the initial Colima setup.

If you've already initialized Colima, you can still adjust CPU, memory, and disk size:

```bash
colima stop
colima start --cpu 4 --memory 8 --disk 60
```

To check your current configuration:

```bash
colima list
```

If you need the performance benefits of the virtualization framework (vz) and virtiofs, you'll need to delete and recreate your Colima instance:

```bash
colima delete
colima start --cpu 4 --memory 8 --disk 60 --vm-type=vz --mount-type=virtiofs
```

> **Caution**: Deleting your Colima instance will remove all containers, images and volumes unless they're stored externally.

## For M-series Mac Users

If you're using an M-series Mac (Apple Silicon), ensure you're using ARM64 compatible images for best performance:

```bash
# For new installations:
colima start --cpu 4 --memory 8 --disk 60 --vm-type=vz --mount-type=virtiofs --arch aarch64

# For existing installations (aarch64 can be changed later):
colima stop
colima start --cpu 4 --memory 8 --arch aarch64
```

## Making Configuration Persistent

To make these settings persistent, edit your Colima configuration file:

```bash
colima stop
vim ~/.colima/default/colima.yaml
```

Add or modify these settings:

```yaml
cpu: 4
memory: 8
disk: 60
```

For new installations only (these cannot be changed after initial setup):

```yaml
vmType: vz
mountType: virtiofs
arch: aarch64 # Only for M-series Macs
```

> **Note**: Remember that `vmType` and `mountType` can only be set during the initial Colima setup. If you need to change them, you must delete and recreate your Colima instance.

## Setting Up vcan Interfaces on Colima VM

As mentioned in the README.md, you've already set up the vcan interfaces using systemd on the Colima host. If you need to recreate this setup:

1. SSH into the Colima VM:

   ```bash
   colima ssh
   ```

2. Set up the vcan module:

   ```bash
   sudo modprobe vcan
   ```

3. Create the vcan interfaces:

   ```bash
   sudo ip link add dev vcan0 type vcan
   sudo ip link set up vcan0
   sudo ip link add dev vcan1 type vcan
   sudo ip link set up vcan1
   ```

4. To make this persistent across Colima restarts, create the systemd service:

   ```bash
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

   sudo systemctl enable vcan0.service
   ```

## Troubleshooting Colima + DevContainer Issues

### Slow File Operations

If file operations are slow despite the optimizations:

1. Check if you're using virtiofs mount type:

   ```bash
   colima list
   ```

2. Try restarting Colima with explicit mount options:

   ```bash
   colima stop
   colima start --cpu 4 --memory 8 --vm-type=vz --mount-type=virtiofs --mount $HOME:$HOME
   ```

### Container Crashes

If the container still crashes occasionally:

1. Check Colima logs:

   ```bash
   colima status
   colima logs
   ```

2. Increase stability by avoiding memory pressure:

   ```bash
   colima stop
   colima start --cpu 4 --memory 8 --vm-type=vz --mount-type=virtiofs --layer=false
   ```

### Unable to Access vcan Interfaces

If the container can't see the vcan interfaces despite using host networking:

1. Verify the interfaces exist in the Colima VM:

   ```bash
   colima ssh -- ls -la /sys/class/net/ | grep vcan
   ```

2. Check permissions:

   ```bash
   colima ssh -- ls -la /dev/vcan*
   ```

3. Ensure the container has the necessary capabilities:

   ```bash
   docker run --rm --cap-add=NET_ADMIN --network=host busybox ip link
   ```

## Performance Monitoring

To monitor performance of your setup:

```bash
# Inside Colima VM
colima ssh -- htop

# Check disk space
colima ssh -- df -h

# Monitor Docker
docker stats
```

## Final Notes

- The DevContainer now uses the host network to ensure access to vcan interfaces
- Memory and CPU limits are set to manage resource usage
- File watcher exclusions are configured to reduce CPU usage
- Consider using Docker volumes for node_modules and other dependency directories
