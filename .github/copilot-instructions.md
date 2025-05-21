# GitHub Copilot Instructions for rvc2api

- All build, cache, and output files (e.g., dist, dist-ssr, .vite, .vite-temp, node_modules, *.tsbuildinfo, .cache, *.log) are excluded from linting and type checking in both root and frontend ESLint configs.
- All API calls are made via /api/entities endpoints, not /api/lights, /api/locks, etc. to ensure a unified and extensible API design.
- All API endpoints require comprehensive documentation with examples, descriptions, and response schemas to maintain the OpenAPI specification.

This document provides key information for GitHub Copilot to understand the `rvc2api` project architecture and coding patterns.

## Modular Copilot Instructions

This project uses modular Copilot instruction files stored in `.github/instructions/`.
Each `.instructions.md` file contains targeted guidance for specific languages, frameworks, or workflows.

**Key instruction files:**

- [`project-overview.instructions.md`](.github/instructions/project-overview.instructions.md): Project architecture and structure
- [`python-code-style.instructions.md`](.github/instructions/python-code-style.instructions.md): Python coding standards
- [`typescript-code-style.instructions.md`](.github/instructions/typescript-code-style.instructions.md): TypeScript/React coding standards
- [`eslint-typescript-config.instructions.md`](.github/instructions/eslint-typescript-config.instructions.md): ESLint and TypeScript config details
- [`dev-environment.instructions.md`](.github/instructions/dev-environment.instructions.md): Development environment setup and tooling
- [`testing.instructions.md`](.github/instructions/testing.instructions.md): Test patterns and requirements
- [`pull-requests.instructions.md`](.github/instructions/pull-requests.instructions.md): PR guidelines and expectations
- [`documentation.instructions.md`](.github/instructions/documentation.instructions.md): API documentation and MkDocs configuration
- [`mcp-tools.instructions.md`](.github/instructions/mcp-tools.instructions.md): Using Copilot Chat tools and context commands
- [`env-vars.instructions.md`](.github/instructions/env-vars.instructions.md): Configuration and environment setup

> **For any code generation or chat involving these topics, refer to the relevant `.instructions.md` file in `.github/instructions/` for detailed guidance.**


## Project Summary

`rvc2api` is a Python-based API and WebSocket service for RV-C (Recreational Vehicle Controller Area Network) systems:

- **FastAPI backend daemon** with WebSocket support
- **React frontend** with TypeScript and Vite
- **RV-C decoder** for CANbus messages
- **Modular architecture** with clear separation of concerns
- **Typed code** with Pydantic models and full type hints
- **API Documentation** with MkDocs, Material theme, and OpenAPI integration

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

## Monorepo ESLint & TypeScript Configuration (Frontend)

- **Monorepo Flat Config**: ESLint is configured at the repo root (`eslint.config.js`) and imports the frontend config (`web_ui/eslint.config.js`) for monorepo compatibility. Always run ESLint and pre-commit from the repo root.
- **TypeScript Project References**: The frontend uses strict TypeScript project references (`tsconfig.json`, `tsconfig.app.json`, `tsconfig.test.json`, etc.) for modularity and performance. ESLint is pointed to the correct `tsconfig.eslint.json` using absolute paths.
- **Legacy Code Exclusion**: All legacy and legacy-adjacent files (e.g., `src/core_daemon/web_ui/`) are excluded from linting and type checking using robust absolute ignore patterns in ESLint config and pre-commit hooks. This ensures only modern, maintained code is checked.
- **Pre-commit Integration**: The `.pre-commit-config.yaml` runs ESLint from the repo root, using the root config and correct args. It is set up to ignore legacy files and only check relevant frontend code.
- **Troubleshooting**:
  - If ESLint or pre-commit reports config or parsing errors, check that you are running from the repo root and that ignore patterns are absolute.
  - For TypeScript interface parsing errors, ensure all interface files have at least one import (see `npm run fix:interfaces`).
  - For persistent config issues, see `.github/instructions/eslint-typescript-config.instructions.md` and use MCP tools for targeted queries (e.g., `@context7 ESLint ignore patterns`, `@context7 legacy exclusion`).

See `.github/instructions/eslint-typescript-config.instructions.md` for detailed config, ignore, and troubleshooting patterns.

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
- **Documentation**: MkDocs-based documentation with OpenAPI schema integration
  - API endpoints documented with FastAPI's metadata and docstring features
  - OpenAPI schema exported automatically via `scripts/export_openapi.py`
  - Frontend TypeScript types generated from OpenAPI schema
  - Documentation built with MkDocs Material theme
- **Type Stubs**: Custom type stubs in `typings/` for third-party libraries
  - Use Protocol-based implementations for complex interfaces
  - Only include required parts of the API that are actually used

## Development Tools

- **VS Code Tasks**: Extensive task configuration for streamlined development:
  - **Server Tasks**: Start backend, frontend, documentation server
  - **Code Quality**: Linting, type checking, formatting for both backend and frontend
  - **Testing**: Run tests with coverage for backend, run frontend tests
  - **Build Tasks**: Build frontend and documentation
  - **Development**: Nix shell, pre-commit checks, dependency management
  - See `.github/instructions/vscode-tasks.instructions.md` for details
- **Model Context Protocol**: MCP tools provide critical context-aware assistance
  - `@context7`: **IMPORTANT** - Always use for up-to-date library documentation and code examples
    - Provides current API specifications and examples that avoid hallucinated APIs
    - Essential for any React, FastAPI, Next.js, or third-party library questions
    - Examples: `@context7 React useState TypeScript`, `@context7 FastAPI WebSocket auth`
  - `@perplexity`: External research for protocols and general concepts
  - `@github`: Repository and issue queries
- **MCP Best Practice**: Always default to `@context7` for library and framework questions before using general LLM knowledge
- **Testing**: Use `poetry run pytest` for backend tests and `cd web_ui && npm test` for frontend
