# Claude Configuration

This directory contains modular Claude configuration files for the CoachIQ project. Each file provides targeted guidance for specific development workflows and contexts.

## Directory Structure

```
.claude/
├── commands/           # Custom slash commands for common workflows
├── instructions/       # Modular instruction files by domain
└── README.md          # This file
```

## Available Commands

| Command | Description |
|---------|-------------|
| `/fix-type-errors` | Run type checking and fix common issues |
| `/run-full-dev` | Start complete development environment |
| `/code-quality-check` | Run all linting, formatting, and type checks |
| `/build-and-test` | Full build and test cycle |

## Available Instructions

| File | Domain | Description |
|------|--------|-------------|
| `backend.md` | Python Backend | FastAPI patterns, service architecture |
| `frontend.md` | React Frontend | TypeScript, React patterns, UI components |
| `testing.md` | Testing | pytest, Vitest, testing patterns |
| `code-quality.md` | Code Quality | Linting, formatting, type checking |
| `api-patterns.md` | API Design | Entity control, WebSocket, REST patterns |

## Usage

These files are automatically loaded by Claude Code and provide context-aware guidance when working with the codebase. Custom commands can be invoked using `/command-name` syntax.

## Team Collaboration

All configuration files are version-controlled to ensure consistent AI assistance across the development team. When adding new commands or instructions, follow the existing patterns and update this README.
