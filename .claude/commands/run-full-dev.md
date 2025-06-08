# Start Full Development Environment

Launch the complete CoachIQ development environment with all services.

## Workflow

1. **Enter Nix Development Shell** (if available)
   ```bash
   nix develop
   ```

2. **Start Backend Server**
   ```bash
   poetry run python run_server.py --reload --debug
   ```
   - Available at: http://localhost:8000
   - API docs: http://localhost:8000/docs
   - WebSocket: ws://localhost:8000/ws

3. **Start Frontend Development Server**
   ```bash
   cd frontend && npm run dev
   ```
   - Available at: http://localhost:5173
   - Hot reload enabled

4. **Start Documentation Server**
   ```bash
   poetry run mkdocs serve
   ```
   - Available at: http://localhost:8001

## VS Code Integration

Use the integrated VS Code task for streamlined setup:
- Open Command Palette (`Cmd+Shift+P`)
- Run: `Tasks: Run Task`
- Select: `Server: Start Full Dev Environment`

## Development URLs

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:5173 | React development server |
| Backend API | http://localhost:8000 | FastAPI with hot reload |
| API Docs | http://localhost:8000/docs | Swagger UI |
| ReDoc | http://localhost:8000/redoc | Alternative API docs |
| Documentation | http://localhost:8001 | MkDocs site |

## Environment Requirements

- **Python**: Managed via Poetry virtual environment
- **Node.js**: For frontend development (npm/pnpm)
- **Nix** (optional): For reproducible development environment
- **CAN Interface**: Virtual CAN (vcan) for testing

## Arguments

$ARGUMENTS can specify:
- `backend-only` - Start only the Python backend
- `frontend-only` - Start only the React frontend
- `docs-only` - Start only the documentation server
- `no-nix` - Skip Nix development shell activation
