# rvc2api Documentation

Welcome to the rvc2api documentation. This site provides comprehensive information about the rvc2api project, a Python-based API and WebSocket service for RV-C (Recreational Vehicle Controller Area Network) systems.

!!! info "Documentation Versions"
You're viewing the documentation for the version displayed in the top navigation bar.

    - **latest**: Most recent stable release
    - **dev**: Latest development version (main branch)
    - **x.y.z**: Specific released versions

    To switch versions, use the version dropdown in the navigation.

## What is rvc2api?

rvc2api is a modern API for RV-C CANbus systems, allowing you to:

- Monitor and control your RV's devices (lights, tanks, thermostats, etc.)
- Get real-time updates via WebSockets
- Access a clean and consistent API
- Use a modern React frontend

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/carpenike/rvc2api.git && cd rvc2api

# Install dependencies
poetry install
cd web_ui && npm install
```

### Running the Application

Start the backend:

```bash
poetry run python src/core_daemon/main.py
```

Start the frontend (in a separate terminal):

```bash
cd web_ui && npm run dev
```

## Key Features

- **FastAPI backend**: Modern, async API with automatic OpenAPI documentation
- **React frontend**: Clean, responsive UI built with TypeScript and Vite
- **WebSocket support**: Real-time updates for state changes
- **RV-C decoding**: Interpreting and generating CAN bus messages
- **Entity-based API**: Unified API surface for all device types

## Documentation Structure

This documentation is organized into several sections:

- [**Getting Started**](development-environments.md): Environment setup and development basics
- [**API Reference**](api/index.md): Comprehensive API documentation
  - [API Overview](api/overview.md): Structure and organization of the API
  - [Entity API](api/entities.md): Endpoints for entity management and control
  - [WebSocket API](api/websocket.md): Real-time communication
  - [OpenAPI Specification](api/openapi.md): Auto-generated API documentation
- [**Architecture**](architecture/overview.md): System design and component organization
  - [Backend Architecture](architecture/backend.md): Python API components
  - [Frontend Architecture](architecture/frontend.md): React UI components
- [**Development Guides**](frontend-development.md): In-depth development instructions

## Contributing

We welcome contributions to rvc2api! Please see the [GitHub repository](https://github.com/carpenike/rvc2api) and read [CONTRIBUTING.md](https://github.com/carpenike/rvc2api/blob/main/CONTRIBUTING.md) for guidelines on how to contribute.
