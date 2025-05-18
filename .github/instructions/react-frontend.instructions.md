---
applyTo: "**/web_ui/**"
---

# React Frontend Architecture

## Technology Stack

- React 18+ with TypeScript
- Vite for development and building
- Tailwind CSS for styling
- WebSocket for real-time data
- Fetch API for HTTP requests

## Linting & Code Quality

- TypeScript: Strict mode enabled with project references (tsconfig.json → tsconfig.app.json)
- ESLint: Using flat config system with both eslint.config.js and eslint.config.mjs
- Plugins: react-hooks, react-refresh, jsdoc
- Type Checking: Run with `npm run typecheck` (required for all PRs)
- Format: Follow ESLint configuration rules
- Formatting Rules:
  - No trailing commas (comma-dangle: ["error", "never"])
  - Double quotes (quotes: ["error", "double"])
  - Always use semicolons (semi: ["error", "always"])
- Line Endings: LF (Unix style)
- Indentation: 2 spaces
- TypeScript Interfaces: Must have at least one import statement to avoid parsing errors
- Verification: All code must pass linting, type checking, and formatting checks
- Fix Scripts: Use `npm run fix:style` to fix common ESLint issues

## Directory Structure

- `web_ui/src/components/`: Reusable UI components
- `web_ui/src/pages/`: Top-level page components
- `web_ui/src/hooks/`: Custom React hooks
- `web_ui/src/utils/`: Utility functions and helpers
- `web_ui/src/api.ts`: Backend API interaction

## Features

- Modern React-based UI with real-time data via WebSocket connection
- Dashboard view with system status
- Device management interface
- Light control interface
- CAN message analyzer
- Network topology visualization

## Design Principles

- Modern UI with curved lines and contemporary themes
- Responsive design that works on all device sizes
- Consistent color scheme and typography
- Accessible interface following WAI-ARIA guidelines

## MCP Tools for React Development

### @context7 Use Cases

- Get WebSocket message formats: `@context7 WebSocket message format entities`
- Find API endpoint schemas: `@context7 /api/entities schema`
- Review component implementations: `@context7 Lights.tsx component`
- Find backend state models: `@context7 entity state model`

### @perplexity Use Cases

- Research React best practices: `@perplexity React useEffect cleanup patterns`
- Investigate WebSocket reconnection: `@perplexity WebSocket reconnection in React`
- Explore UI component libraries: `@perplexity React component libraries for dashboard interfaces`

## API Integration

### REST API Example

```typescript
// Fetch entities from the API
const fetchEntities = async () => {
  try {
    const response = await fetch("/api/entities");
    if (!response.ok) throw new Error("Network response was not ok");
    const data = await response.json();
    return data;
  } catch (error) {
    console.error("Error fetching entities:", error);
    throw error;
  }
};
```

### WebSocket Example

```typescript
// Connect to entities WebSocket
const connectWebSocket = () => {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const wsUrl = `${protocol}//${window.location.host}/ws/entities`;

  const socket = new WebSocket(wsUrl);

  socket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    // Handle incoming data
  };

  socket.onclose = () => {
    // Implement reconnection logic
    setTimeout(() => connectWebSocket(), 3000);
  };

  return socket;
};
```

## Development Process

1. Run backend: `poetry run python src/core_daemon/main.py`
2. Run frontend: `cd web_ui && npm run dev`
3. Access development server at http://localhost:5173

## Building for Production

```bash
cd web_ui
npm run build
# Output in web_ui/dist/
```

## Deployment

The built files from `web_ui/dist/` should be deployed to `/var/lib/rvc2api-web-ui/dist/`
on the target system where Caddy is configured to serve them.
