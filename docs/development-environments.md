# Development Environment Setup for rvc2api

This document outlines multiple approaches for setting up development environments for the rvc2api project.

## Option 1: Using Nix Development Shell (Recommended)

The project includes a Nix flake that provides a fully configured development environment with all dependencies.

### Prerequisites

- [Nix package manager](https://nixos.org/download.html) with flakes enabled

### Setup

1. Enter the development shell:

   ```bash
   nix develop
   ```

2. This provides:

   - Python with all project dependencies
   - Node.js for the frontend
   - Poetry for Python package management
   - All necessary development tools

3. Start developing:
   - Backend: `poetry run python run_server.py`
   - Frontend: `cd web_ui && npm run dev`

### Benefits

- Reproducible environment across all developers
- Exact versions of all dependencies are locked
- Works on any system where Nix is installed
- No global pollution of your system

## Option 2: Using poetry2nix

The project includes experimental support for [poetry2nix](https://github.com/nix-community/poetry2nix), which offers more integrated management of Python dependencies within the Nix ecosystem.

See [Poetry2Nix Integration](poetry2nix-integration.md) for setup instructions.

## Option 3: Using Poetry Directly

If you don't want to use Nix, you can use Poetry directly to manage the Python environment.

### Prerequisites

- [Python](https://www.python.org/downloads/) 3.12 or later
- [Poetry](https://python-poetry.org/docs/#installation)
- [Node.js](https://nodejs.org/) (for frontend development)

### Setup

1. Install Python dependencies:

   ```bash
   poetry install
   ```

2. Install frontend dependencies:

   ```bash
   cd web_ui && npm install
   ```

3. Start the backend server:

   ```bash
   poetry run python run_server.py
   ```

4. Start the frontend development server:

   ```bash
   cd web_ui && npm run dev
   ```

## VS Code Integration

The repository includes VS Code configuration files to make development easier:

- Tasks for common operations
- Launch configurations for debugging
- Recommended extensions

To use these features:

1. Open the project in VS Code
2. Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on macOS) and search for "Tasks: Run Task"
3. Choose from available tasks like:
   - Start Backend Server
   - Start Frontend Dev Server
   - Run Tests
   - Format Code (Ruff)
   - Lint (Ruff)

## Environment Variables

The application uses the following environment variables which you may need to set for development:

### Basic Configuration

- `LOG_LEVEL`: Logging level (default: "INFO")
- `RVC2API_TITLE`: API title (default: "rvc2api")
- `RVC2API_SERVER_DESCRIPTION`: API description (default: "RV-C to API Bridge")
- `RVC2API_ROOT_PATH`: Root path for API URLs (default: "")

### CAN Bus Configuration

- `CAN_CHANNELS`: Comma-separated list of CAN interfaces (default: "can0,can1")
- `CAN_BUSTYPE`: CAN bus type (default: "socketcan")
- `CAN_BITRATE`: CAN bus bitrate (default: "500000")

### Integrations

- `ENABLE_PUSHOVER`: Enable Pushover notifications (default: "0")
- `PUSHOVER_API_TOKEN`: Pushover API token
- `PUSHOVER_USER_KEY`: Pushover user key
- `PUSHOVER_DEVICE`: Pushover device name (optional)
- `PUSHOVER_PRIORITY`: Pushover message priority (optional)
- `ENABLE_UPTIMEROBOT`: Enable UptimeRobot integration (default: "0")
- `UPTIMEROBOT_API_KEY`: UptimeRobot API key

### File Paths

- `CAN_SPEC_PATH`: Override path to RV-C specification file
- `CAN_MAP_PATH`: Override path to device mapping file
- `RVC2API_USER_COACH_INFO_PATH`: Path to user coach info YAML file

## Model Context Protocol Tools

For enhanced code exploration and understanding, the project is configured to work with Model Context Protocol (MCP) tools:

- See [MCP Tools Setup](mcp-tools-setup.md) for more information.
