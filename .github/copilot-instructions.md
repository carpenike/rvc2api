# GitHub Copilot Instructions for rvc2api

This document provides key information for GitHub Copilot to understand the `rvc2api` project architecture and coding patterns. Detailed domain-specific instructions are organized in `.github/instructions/*.instructions.md` files.

## Project Summary

`rvc2api` is a Python-based API and WebSocket service for RV-C (Recreational Vehicle Controller Area Network) systems:

- **FastAPI backend daemon** with WebSocket support
- **React frontend** with TypeScript and Vite
- **RV-C decoder** for CANbus messages
- **Modular architecture** with clear separation of concerns
- **Typed code** with Pydantic models and full type hints

## Linting & Code Quality Requirements

### Python

- **Version**: 3.12+
- **Formatting**: black (line length: 100)
- **Linting**: ruff (configured in pyproject.toml)
- **Type Checking**: pyright (basic mode, configured in pyrightconfig.json)
- **Import Order**: Group as stdlib → third-party → local
- **Custom Type Stubs**: Created in typings/ directory for external libraries
- **Line Endings**: LF (Unix style)
- **Code Validation**: All code must pass both linting AND type checking

### TypeScript/React

- **ESLint**: Using flat config in eslint.config.js and eslint.config.mjs
- **TypeScript**: Strict mode enabled with project references
- **Formatting**: Follow ESLint configuration rules
- **Line Endings**: LF (Unix style)
- **Indentation**: 2 spaces
- **TypeScript Interfaces**: Ensure all standalone interface files have imports to avoid parsing errors
- **Trailing Commas**: Not allowed (configured in ESLint)

## Core Architecture

- `src/common/`: Shared models and utilities
- `src/core_daemon/`: FastAPI app, WebSockets, state management
- `src/rvc_decoder/`: DGN decoding, mappings, instance management
- `web_ui/`: React frontend with TypeScript, Vite, and Tailwind CSS
- `backend/`: (Future) Restructured backend components

## Deployment Architecture

- **Backend**: FastAPI application served on configured port
- **Frontend**: React SPA built with Vite and served by Caddy
- **Reverse Proxy**: Caddy serves frontend static files and proxies API/WebSocket requests

## Code Patterns

- **FastAPI routes**: Organized by domain in `api_routers/` using APIRouter
- **WebSockets**: Used for real-time updates in `websocket.py`
- **State management**: Centralized in `app_state.py`
- **Configuration**: Environment variables with Pydantic Settings
- **Error handling**: Structured exceptions with proper logging
- **Testing**: pytest with mocked CANbus interfaces
- **React Components**: Organized by feature in the `web_ui/src/` directory
- **API Integration**: REST and WebSocket connections between frontend and backend
- **Type Stubs**: Custom type stubs in `typings/` for third-party libraries
  - Use Protocol-based implementations for complex interfaces
  - Only include required parts of the API that are actually used

## Development Tools

- **Model Context Protocol**: Use MCP tools to better understand the codebase
  - `@context7`: Project-specific code lookup (e.g., `@context7 WebSocket connection handling`)
  - `@perplexity`: External research for protocols and libraries
  - `@github`: Repository and issue queries
- **Detailed patterns**: See domain-specific instruction files for example queries
- **Testing**: Use `poetry run pytest` for backend tests and `cd web_ui && npm test` for frontend
