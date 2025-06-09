# React Deployment with Caddy

This document describes the deployment setup for the CoachIQ React frontend after the refactoring from a FastAPI-served template-based UI to a standalone React application.

For information on developing the frontend, see [Frontend Development Guide](frontend-development.md).

## Architecture

The architecture consists of:

1. **FastAPI Backend**: Provides API endpoints at `/api/*` and WebSocket connections at `/ws/*`
2. **React Frontend**: Standalone SPA served directly by Caddy
3. **Caddy**: HTTP server that:
   - Serves the React frontend static files
   - Reverse proxies API requests to the FastAPI backend
   - Handles TLS termination and certificate management

```
  +--------+                +-------+                +-----------+
  | Browser | <--HTTPS----> | Caddy | <--HTTP/WS---> | FastAPI   |
  +--------+                +-------+                +-----------+
                               |
                         +----------+
                         | React    |
                         | Frontend |
                         | (static) |
                         +----------+
```

## Caddy Configuration

The Caddy configuration is defined in the NixOS module at `modules/caddy.nix`. Key features:

- Serves the React frontend from `/var/lib/coachiq-web-ui/dist`
- Proxies all `/api/*` requests to the FastAPI backend
- Proxies all `/ws/*` WebSocket connections to the backend
- Uses Cloudflare DNS verification for HTTPS certificates
- Falls back to serving `index.html` for any non-file paths (for SPA routing)

## Deployment Process

1. Build the React frontend:

   ```
   cd frontend
   npm install
   npm run build
   ```

2. Copy the built files to the server:

   ```
   rsync -avz dist/ nixpi:/var/lib/coachiq-web-ui/dist/
   ```

## Static Files for API Documentation

The FastAPI backend still serves static files for API documentation at the `/static` route. These files are no longer related to the web UI, which is now a standalone React application. The static files are:

1. Located in the `src/core_daemon/static/` directory
2. Automatically created if the directory doesn't exist
3. Used only for API documentation and Swagger UI customization
4. Not related to the React frontend

When deploying updates:

1. API documentation static files are included in the Python package
2. No manual action is needed for these files during deployment
3. The React frontend is built and deployed separately as described above

## Code Changes from Refactoring

1. Modified `config.py` to only handle static files for API documentation
2. Removed web UI template-related code from the FastAPI application
3. Updated `main.py` to mount only the API documentation static files
4. Created a dedicated `static` directory in `src/core_daemon/` separate from web UI
5. Removed frontend router imports from the FastAPI application

6. Ensure the Caddy service is running:

   ```
   systemctl status caddy
   ```

## Development Workflow

During development:

1. Run the FastAPI backend:

   ```
   poetry run python run_server.py
   ```

2. Run the React dev server:

   ```
   cd frontend
   npm run dev
   ```

The Vite dev server is configured to proxy API requests to the FastAPI backend.
