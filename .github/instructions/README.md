# GitHub Copilot Instructions

This directory contains modular GitHub Copilot instructions for the `rvc2api` project. Each file includes YAML frontmatter with an `applyTo` pattern indicating which files the instructions apply to.

## Available Instructions

### Core Architecture

| File                                                                 | Applies To     | Description                                       |
| -------------------------------------------------------------------- | -------------- | ------------------------------------------------- |
| [project-overview.instructions.md](project-overview.instructions.md) | All files      | Project architecture and structure                |
| [python-backend.instructions.md](python-backend.instructions.md)     | Backend code   | Python backend architecture and patterns          |
| [react-frontend.instructions.md](react-frontend.instructions.md)     | React UI files | React, TypeScript, and Vite frontend architecture |

### Code Style and Quality

| File                                                                                 | Applies To   | Description                                    |
| ------------------------------------------------------------------------------------ | ------------ | ---------------------------------------------- |
| [python-code-style.instructions.md](python-code-style.instructions.md)               | Python files | Python coding standards and style guide        |
| [typescript-code-style.instructions.md](typescript-code-style.instructions.md)       | TS/JS files  | TypeScript/React coding standards and patterns |
| [eslint-typescript-config.instructions.md](eslint-typescript-config.instructions.md) | TS/JS files  | ESLint setup and TypeScript config details     |
| [code-style.instructions.md](code-style.instructions.md)                             | Python files | General coding standards (legacy)              |

### Development Workflow

| File                                                               | Applies To | Description                        |
| ------------------------------------------------------------------ | ---------- | ---------------------------------- |
| [dev-environment.instructions.md](dev-environment.instructions.md) | All files  | Setting up and using dev tools     |
| [vscode-tasks.instructions.md](vscode-tasks.instructions.md)       | All files  | VS Code task definitions and usage |
| [testing.instructions.md](testing.instructions.md)                 | Test files | Test patterns and requirements     |
| [pull-requests.instructions.md](pull-requests.instructions.md)     | All files  | PR guidelines and expectations     |

### Tools and Configuration

| File                                                   | Applies To   | Description                                |
| ------------------------------------------------------ | ------------ | ------------------------------------------ |
| [mcp-tools.instructions.md](mcp-tools.instructions.md) | All files    | Using Copilot Chat tools (@context7, etc.) |
| [env-vars.instructions.md](env-vars.instructions.md)   | Python files | Configuration and environment setup        |

### Legacy Documentation

| File                                           | Applies To    | Description                           |
| ---------------------------------------------- | ------------- | ------------------------------------- |
| [webui.instructions.md](webui.instructions.md) | Legacy Web UI | Legacy HTML template and JS standards |

## Using These Instructions

These files are designed to work with GitHub Copilot in VS Code. When editing a file, GitHub Copilot will automatically apply the relevant instructions based on the file type.

You can also use the prompt templates in the [../prompts](../prompts) directory for more specific guidance on common development tasks.

## MCP Tools Integration

The project uses Model Context Protocol (MCP) tools for AI-assisted development:

- **@context7**: Always use first for library/framework questions - provides accurate, up-to-date API information
- **@perplexity**: For general research on technical topics not found in the codebase
- **@github**: For repository exploration and finding related issues/PRs

See [mcp-tools.instructions.md](mcp-tools.instructions.md) for detailed usage examples.

## VS Code Tasks Integration

Extensive VS Code tasks are available to streamline development. These tasks cover:

- Starting servers (backend, frontend, documentation)
- Code quality checks (linting, formatting, type checking)
- Testing (with and without coverage reports)
- Building (frontend, documentation)
- Development environment management

See [vscode-tasks.instructions.md](vscode-tasks.instructions.md) for the complete list of available tasks and how to use them.
