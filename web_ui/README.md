# rvc2api React Frontend

This directory contains the React-based frontend for the rvc2api project. It provides a modern, responsive UI for interacting with the RV-C API backend. It's built with:

- **React 19** for UI components
- **Vite** for build tooling and development server
- **TailwindCSS** for styling
- **TypeScript** for type safety
- **React Router** for navigation
- **ESLint** with flat configuration for code quality
- **Jest** for testing

## Features

- Modern React-based UI with real-time data via WebSocket connection
- Dashboard view with system status
- Device management interface
- Light control interface
- CAN message analyzer
- Network topology visualization

## Development

### Prerequisites

- Node.js 20+ and npm 10+
  - When using Nix, these are automatically provided by the development shell

### Setup

#### Using Nix (Recommended)

```bash
# Enter the development environment
nix develop

# Navigate to web_ui directory
cd web_ui

# Install dependencies
npm install

# Start the development server
npm run dev
```

#### Manual Setup (Without Nix)

```bash
# Navigate to web_ui directory
cd web_ui

# Install dependencies
npm install

# Start the development server
npm run dev
```

The development server will start at `http://localhost:5173` and will proxy API requests to the FastAPI backend running on port 8000.

### Environment Variables

You can customize the development environment using a `.env.local` file:

```bash
# API URL for development (default: http://localhost:8000/api)
VITE_API_URL=http://localhost:8000/api

# WebSocket URL for development (default: ws://localhost:8000/api/ws)
VITE_WS_URL=ws://localhost:8000/api/ws

# App version override
VITE_APP_VERSION=0.1.0-dev
```

### Available Scripts

- `npm run dev` - Start the development server
- `npm run build` - Build for production
- `npm run lint` - Run ESLint
- `npm run preview` - Preview the production build locally
- `npm run typecheck` - Run TypeScript type checking
- `npm run test` - Run Jest tests
- `npm run test:watch` - Run tests in watch mode
- `npm run test:coverage` - Run tests with coverage report

## API Integration

The frontend communicates with the backend through:

1. HTTP REST API - For data fetching and commands
2. WebSocket - For real-time updates

All API requests are automatically proxied to the backend during development.

## Building for Production

### Using Nix (Recommended)

```bash
# Build using the Nix-managed script
nix run .#build-frontend
```

### Manual Build

```bash
# Navigate to web_ui directory
cd web_ui

# Build the production bundle
npm run build
```

Either method will create optimized files in the `dist/` directory, which can be served directly by the FastAPI backend or through Caddy as configured in the rv-nixpi repository.

## Project Structure

- `src/` - React source code
  - `components/` - Reusable React components
  - `pages/` - Top-level page components
  - `hooks/` - Custom React hooks
  - `api/` - Backend API integration
  - `context/` - React context providers
  - `types/` - TypeScript type definitions
  - `utils/` - Utility functions
- `public/` - Static assets that don't need processing
- `index.html` - HTML entry point
- `vite.config.ts` - Vite configuration
- `tsconfig.json` - TypeScript configuration

## ESLint and TypeScript Configuration

### ESLint Setup

This project uses ESLint v9+ with the new flat configuration format:

- `eslint.config.js` - Main configuration file using the flat config format
- `eslint.config.mjs` - Alternative format for module support

Key configuration settings:

- No trailing commas (`comma-dangle: ["error", "never"]`)
- Double quotes (`quotes: ["error", "double"]`)
- Always use semicolons (`semi: ["error", "always"]`)
- Unix line endings (LF)
- 2 spaces indentation

### TypeScript Configuration

TypeScript uses project references to separate concerns:

- `tsconfig.json` - Root configuration with references
- `tsconfig.app.json` - Application-specific configuration
- `tsconfig.node.json` - Node-specific configuration
- `tsconfig.test.json` - Test-specific configuration

### Helper Scripts

Several scripts are available to help maintain code quality:

```bash
# Run ESLint
npm run lint

# Fix ESLint issues
npm run lint:fix

# Fix common styling issues (trailing commas, etc.)
npm run fix:style

# Fix TypeScript interface parsing errors
npm run fix:interfaces

# Run TypeScript type checking
npm run typecheck
```

### Known Issues

- TypeScript files with standalone interfaces must have at least one import
- Pre-commit hook will run ESLint with the fix option automatically
- See GitHub issue #30 for information about remaining ESLint/TypeScript issues

## Adding New Components

1. Create a new component in `src/components/`
2. Export it from `src/components/index.ts`
3. Use it in your pages

## Additional Environment Configuration

The following additional environment variables can be set:

- `VITE_API_BASE_URL` - Base URL for API requests (defaults to `/api` in production)

## Design Principles

- Modern UI with curved lines and contemporary themes
- Responsive design that works on all device sizes
- Consistent color scheme and typography
- Accessible interface following WAI-ARIA guidelines
