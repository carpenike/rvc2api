# Using VSCode Devcontainer with vCAN

## Testing vCAN Communication

### Quick Setup Verification

You can verify your vCAN setup quickly using the `test_vcan_setup.py` script:

```bash
# Bash
python dev_tools/test_vcan_setup.py

# Fish
python dev_tools/test_vcan_setup.py
```

This script:

1. Opens a connection to the vcan0 interface
2. Sends a test message
3. Listens for the message
4. Confirms successful communication

### Manual Testing

For more detailed testing, you can use the `test_vcan.py` script in the `dev_tools` directory:

#### Sending Test Messages

```bash
python dev_tools/test_vcan.py --action send --interface vcan0 --count 5 --interval 0.5
```

#### Monitoring CAN Messages

```bash
python dev_tools/test_vcan.py --action monitor --interface vcan0 --duration 60
```

For more comprehensive testing, open two terminal windows in VS Code:

1. In one terminal, run the monitoring command
2. In another terminal, run the sending commando use the devcontainer setup to develop and test the RVC2API project with virtual CAN bus support.

## Prerequisites

1. [VSCode](https://code.visualstudio.com/) installed
2. [Docker](https://www.docker.com/products/docker-desktop/) installed
3. [Colima](https://github.com/abiosoft/colima) installed (for macOS)
4. [Dev Containers Extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) installed in VSCode

## Setting Up Colima with vCAN

We've streamlined the setup process by integrating vCAN setup into the Colima setup script:

```bash
.devcontainer/setup-colima.sh
```

This script will:

1. Install or configure Colima with proper resources
2. Set up Docker context
3. Install and configure vCAN interfaces in the VM
4. Create systemd services to ensure vCAN interfaces persist on VM restart

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
poetry run python run_server.py
```

## Running the Frontend

In another terminal:

```bash
cd /workspace/web_ui
npm run dev
```

## Automated Setup with Scripts

The project includes scripts to automate the setup of vcan interfaces:

### Host Machine Setup (macOS with Colima)

Run the provided setup script:

```bash
./scripts/setup_colima_vcan.sh
```

This script will:

- SSH into your Colima VM
- Install necessary Linux headers
- Load the vcan kernel module
- Create vcan0 and vcan1 interfaces
- Configure systemd service for automatic vcan setup on VM restart

### Devcontainer Setup

Inside the devcontainer, you can verify and create vcan interfaces with:

```bash
./scripts/ensure_vcan_interfaces.sh
```

This script will:

- Check if vcan module is loaded
- Create vcan0 and vcan1 interfaces if missing
- Ensure interfaces are up and running
- Install can-utils tools if missing

### Using VS Code Tasks

The following VS Code tasks are available for vcan setup and testing:

1. **System: Setup Colima vcan** - Run from host machine to set up Colima VM
2. **System: Ensure vcan Interfaces** - Run inside devcontainer to verify/create interfaces
3. **System: Test vCAN Setup** - Test the vcan interfaces by sending and receiving a message

To run these tasks:

1. Press `Cmd+Shift+P` (macOS) or `Ctrl+Shift+P` (Windows/Linux)
2. Type "Tasks: Run Task" and select it
3. Choose one of the vCAN-related tasks from the list

## Troubleshooting

### Diagnosing vCAN Issues

Run the diagnostic script to check for common vCAN issues:

```bash
./.devcontainer/diagnose-vcan.sh
```

### vCAN Module Not Available

If you encounter issues with the vCAN module not being available, check if the kernel module is loaded:

```bash
lsmod | grep vcan
```

If it's not available, it could be due to limitations in the VM kernel used by Colima. In this case:

1. Exit the devcontainer
2. Stop Colima: `colima stop`
3. Try starting Colima with a different VM provider: `colima start --vm-type qemu`
4. Run the setup script: `./scripts/setup_colima_vcan.sh`
5. Open the devcontainer again
