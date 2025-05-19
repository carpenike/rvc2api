# DevContainer Performance Optimization Guide

This guide provides tips for optimizing your DevContainer experience with this project.

## Docker Environment Configuration

### For Colima on macOS (Recommended)

For optimal performance with Colima on macOS, see the [Colima-specific optimization guide](./COLIMA.md). Key recommendations:

```bash
colima start --cpu 4 --memory 8 --disk 60 --vm-type=vz --mount-type=virtiofs
```

- Use Apple's Virtualization Framework (vz) for better performance
- Use VirtioFS mount type for faster filesystem operations
- For M-series Macs, add `--arch aarch64` for native ARM performance

### For Docker Desktop

If using Docker Desktop, adjust these settings:

1. **Resources > Advanced**:

   - CPUs: 4 or more (if available)
   - Memory: 8GB or more
   - Swap: 1GB or more
   - Disk image size: 60GB or more

2. **File Sharing**:

   - Only share the directories you need
   - Consider using Docker volumes for dependencies

3. **WSL Integration** (Windows only):
   - Use WSL 2 backend for better performance
   - Consider moving your workspace into the WSL 2 filesystem

## Alternative: Use Volume-Based Development

For significantly better performance, especially on macOS and Windows:

1. Use VS Code's "Clone Repository in Container Volume..." command:

   - Open the Command Palette (`Ctrl+Shift+P` or `Cmd+Shift+P`)
   - Search for "Dev Containers: Clone Repository in Container Volume..."
   - Enter this repository's URL

2. Benefits:
   - All file operations happen inside the container
   - No slow bind mounts between host and container
   - Much faster file I/O for build tools

## DevContainer Optimizations

The current configuration includes several optimizations:

1. **Filesystem Performance**:

   - Using `consistency=cached` for bind mounts
   - Persistent Nix store mount to prevent rebuilding

2. **VS Code Performance**:

   - File watcher exclusions for large directories
   - Extensions optimized for the project

3. **Network Configuration**:
   - Using `--network=host` for CAN interface access
   - Properly scoped container capabilities

## Troubleshooting

### Container Crashes

- Check Docker logs: `docker logs <container-id>` or `colima logs`
- Look for out-of-memory issues
- Increase memory allocation in settings
- For Colima: Try adding `--layer=false` to prevent memory pressure

### Slow Performance

- Check if disk I/O is the bottleneck (common with bind mounts)
- For Colima: Ensure you're using `--mount-type=virtiofs`
- Consider using a Docker volume workflow
- Use the built-in Nix cache and avoid rebuilding dependencies

### Network Issues

- The container uses `--network=host` for CAN interface access
- For Colima: Verify interfaces are available with `colima ssh -- ip link show`

## Pre-build Dependencies (Advanced)

For faster startup times:

1. Use a pre-built Nix profile:

   ```bash
   nix develop --profile .devcontainer/profile
   ```

2. Use this profile in your container:
   ```
   "mounts": [
     "source=${localWorkspaceFolder}/.devcontainer/profile,target=/nix/var/nix/profiles/per-user/vscode/profile,type=bind"
   ]
   ```

## Feedback

If you encounter performance issues, please open an issue with:

1. Your host OS and Docker environment (Colima/Docker Desktop)
2. Steps to reproduce
3. Any error messages or symptoms
