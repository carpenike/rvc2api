# Using VSCode Devcontainer with vCAN

This guide explains how to use the devcontainer setup to develop and test the RVC2API project with virtual CAN bus support.

## Prerequisites

1. [VSCode](https://code.visualstudio.com/) installed
2. [Docker](https://www.docker.com/products/docker-desktop/) installed
3. [Colima](https://github.com/abiosoft/colima) installed (for macOS)
4. [Dev Containers Extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) installed in VSCode

## Starting Colima

Before opening the devcontainer, make sure Colima is running:

```bash
colima start --cpu 4 --memory 8 --disk 20 --vm-type qemu --mount-type 9p --arch x86_64
```

## Opening the Project in a Devcontainer

1. Open VSCode
2. Open the command palette (Cmd+Shift+P or Ctrl+Shift+P)
3. Run "Dev Containers: Open Folder in Container..."
4. Select your rvc2api project folder

VSCode will build and start the container, which may take a few minutes on first run.

## Verifying vCAN Setup

Once the devcontainer is running, you can verify the vCAN interfaces:

```bash
# Check if vcan interfaces are set up
ip link show vcan0
ip link show vcan1
```

## Testing vCAN Communication

You can use the `test_vcan.py` script in the `dev_tools` directory to test vCAN communication:

### Sending Test Messages

```bash
python dev_tools/test_vcan.py --action send --interface vcan0 --count 5 --interval 0.5
```

### Monitoring CAN Messages

```bash
python dev_tools/test_vcan.py --action monitor --interface vcan0 --duration 60
```

For more comprehensive testing, open two terminal windows in VSCode:

1. In one terminal, run the monitoring command
2. In another terminal, run the sending command

## Running the RVC2API Backend

```bash
# Make sure the current directory is the project root
cd /workspace

# Copy the devcontainer environment variables
cp .env.devcontainer .env

# Start the backend server
poetry run python src/core_daemon/main.py
```

## Running the Frontend

In another terminal:

```bash
cd /workspace/web_ui
npm run dev
```

## Troubleshooting

### vCAN Module Not Available

If you encounter issues with the vCAN module not being available, check if the kernel module is loaded:

```bash
lsmod | grep vcan
```

If it's not available, it could be due to limitations in the VM kernel used by Colima. In this case:

1. Exit the devcontainer
2. Stop Colima: `colima stop`
3. Try starting Colima with a different VM provider: `colima start --vm-type qemu`
4. Open the devcontainer again
