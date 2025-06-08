# Testing Instructions

## Testing Philosophy

- **Test Coverage**: Aim for >80% coverage on business logic
- **Test Types**: Unit tests for logic, integration tests for API endpoints, E2E for critical workflows
- **Mocking Strategy**: Mock external dependencies (CAN interfaces, file system) but test real business logic
- **Fast Feedback**: Tests should run quickly to enable TDD workflows

## Backend Testing (pytest)

### Configuration
```toml
# pyproject.toml
[tool.pytest.ini_options]
pythonpath = ["backend", "src"]
addopts = ["--import-mode=importlib"]
testpaths = ["tests"]

# Additional markers can be added for test categorization
markers = [
    "integration: Integration tests requiring external services",
    "performance: Performance benchmarking tests"
]
```

### Test Structure
```python
# tests/conftest.py
import pytest
from unittest.mock import AsyncMock
from backend.core.config import get_settings
from backend.core.state import AppState

@pytest.fixture
async def app_state():
    """Provide clean app state for testing."""
    state = AppState()
    yield state
    await state.cleanup()

@pytest.fixture
def mock_can_interface():
    """Mock CAN interface for testing."""
    mock = AsyncMock()
    mock.send.return_value = True
    mock.receive.return_value = {"id": 0x123, "data": b"\x01\x02"}
    return mock

@pytest.fixture
def test_settings():
    """Test-specific configuration."""
    return get_settings(
        server={"host": "localhost", "port": 8000},
        can={"interfaces": ["vcan0"]},
        features={"enable_persistence": False}
    )
```

### Testing Patterns

#### Service Testing
```python
# tests/services/test_entity_service.py
import pytest
from backend.services.entity_service import EntityService
from backend.models.entity import EntityControlCommand

@pytest.mark.asyncio
async def test_entity_control_command(mock_can_interface, app_state):
    """Test entity control with mocked CAN interface."""
    service = EntityService(can_interface=mock_can_interface, state=app_state)

    command = EntityControlCommand(command="set", state="on", brightness=75)
    result = await service.control_entity("light_1", command)

    assert result.success is True
    mock_can_interface.send.assert_called_once()

    # Verify CAN message format
    call_args = mock_can_interface.send.call_args[0][0]
    assert call_args["id"] == 0x1FEDC123  # Expected RV-C PGN
```

#### API Router Testing
```python
# tests/api/test_entities.py
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_get_entities():
    """Test entity listing endpoint."""
    response = client.get("/api/entities")
    assert response.status_code == 200

    data = response.json()
    assert "entities" in data
    assert isinstance(data["entities"], list)

@pytest.mark.asyncio
async def test_control_entity(mock_entity_service):
    """Test entity control endpoint."""
    command = {"command": "set", "state": "on", "brightness": 75}

    response = client.post("/api/entities/light_1/control", json=command)
    assert response.status_code == 200

    result = response.json()
    assert result["success"] is True
```

#### WebSocket Testing
```python
# tests/websocket/test_handlers.py
import pytest
import json
from fastapi.testclient import TestClient
from backend.main import app

def test_websocket_connection():
    """Test WebSocket connection and message handling."""
    client = TestClient(app)

    with client.websocket_connect("/ws/entities") as websocket:
        # Test connection
        websocket.send_text('{"type": "subscribe", "topic": "entities"}')

        # Simulate entity update
        data = websocket.receive_text()
        message = json.loads(data)

        assert message["type"] == "entity_update"
        assert "entity" in message
```

#### Integration Testing
```python
# tests/integration/test_can_integration.py
import pytest
from backend.integrations.can.manager import CANManager
from backend.integrations.rvc.decode import RVCDecoder

@pytest.mark.integration
async def test_rvc_message_flow():
    """Test complete RV-C message processing flow."""
    can_manager = CANManager(interfaces=["vcan0"])
    decoder = RVCDecoder()

    # Send test message
    test_message = {
        "id": 0x1FEDC001,
        "data": b"\x01\x64\x00\x00\x00\x00\x00\x00"
    }

    await can_manager.send_message(test_message)

    # Verify processing
    received = await can_manager.receive_message(timeout=1.0)
    decoded = decoder.decode_message(received)

    assert decoded["dgn"] == "DC_DIMMER_COMMAND_2"
    assert decoded["instance"] == 1
    assert decoded["brightness"] == 100
```

### Test Factories
```python
# tests/factories.py
from backend.models.entity import Entity, EntityState
from datetime import datetime

class EntityFactory:
    @staticmethod
    def create_light(
        entity_id: str = "light_1",
        name: str = "Test Light",
        state: str = "off",
        brightness: int = 0
    ) -> Entity:
        return Entity(
            id=entity_id,
            name=name,
            device_type="light",
            state=EntityState(
                state=state,
                brightness=brightness,
                last_updated=datetime.now()
            )
        )

    @staticmethod
    def create_can_message(pgn: int = 0x1FEDC, data: bytes = b"\x00" * 8):
        return {
            "id": pgn,
            "data": data,
            "timestamp": datetime.now()
        }
```

## Frontend Testing (Vitest)

### Configuration
```typescript
// vitest.config.ts
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
    globals: true
  },
  resolve: {
    alias: {
      "@": "/src"
    }
  }
});
```

### Test Setup
```typescript
// src/test/setup.ts
import { afterEach } from "vitest";
import { cleanup } from "@testing-library/react";
import "@testing-library/jest-dom";

// Cleanup after each test
afterEach(() => {
  cleanup();
});

// Mock WebSocket globally
global.WebSocket = vi.fn(() => ({
  send: vi.fn(),
  close: vi.fn(),
  addEventListener: vi.fn(),
  removeEventListener: vi.fn()
}));
```

### Component Testing
```typescript
// src/components/__tests__/entity-card.test.tsx
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { EntityCard } from "@/components/entity-card";

const TestWrapper = ({ children }: { children: React.ReactNode }) => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } }
  });

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
};

describe("EntityCard", () => {
  it("renders entity information correctly", () => {
    const entity = {
      id: "light_1",
      name: "Living Room Light",
      state: "on",
      brightness: 75
    };

    render(<EntityCard entity={entity} />, { wrapper: TestWrapper });

    expect(screen.getByText("Living Room Light")).toBeInTheDocument();
    expect(screen.getByRole("switch")).toBeChecked();
  });

  it("calls control API on toggle", async () => {
    const mockControlEntity = vi.fn();
    vi.mock("@/hooks/useEntities", () => ({
      useControlEntity: () => ({ mutate: mockControlEntity })
    }));

    const entity = { id: "light_1", name: "Test Light", state: "off" };

    render(<EntityCard entity={entity} />, { wrapper: TestWrapper });

    const toggle = screen.getByRole("switch");
    fireEvent.click(toggle);

    expect(mockControlEntity).toHaveBeenCalledWith({
      entityId: "light_1",
      command: { command: "toggle" }
    });
  });
});
```

### Hook Testing
```typescript
// src/hooks/__tests__/useWebSocket.test.tsx
import { describe, it, expect, vi } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useWebSocket } from "@/hooks/useWebSocket";

describe("useWebSocket", () => {
  it("establishes WebSocket connection", () => {
    const { result } = renderHook(() => useWebSocket("ws://localhost:8000/ws"));

    expect(result.current.isConnected).toBe(false);

    // Simulate connection
    act(() => {
      result.current.socket?.onopen?.(new Event("open"));
    });

    expect(result.current.isConnected).toBe(true);
  });

  it("handles reconnection on disconnect", () => {
    vi.useFakeTimers();

    const { result } = renderHook(() => useWebSocket("ws://localhost:8000/ws"));

    // Simulate disconnect
    act(() => {
      result.current.socket?.onclose?.(new CloseEvent("close"));
    });

    expect(result.current.isConnected).toBe(false);

    // Fast-forward reconnection timer
    act(() => {
      vi.advanceTimersByTime(3000);
    });

    // Should attempt reconnection
    expect(global.WebSocket).toHaveBeenCalledTimes(2);

    vi.useRealTimers();
  });
});
```

## Test Commands

### Backend Testing
```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=backend --cov-report=term --cov-report=html

# Run specific test files
poetry run pytest tests/services/test_entity_service.py

# Run integration tests only
poetry run pytest -m integration

# Performance tests
poetry run pytest -m performance --benchmark-only
```

### Frontend Testing
```bash
cd frontend

# Run all tests
npm test

# Run with coverage
npm run test:coverage

# Run in watch mode
npm run test:watch

# Run specific test files
npm test entity-card
```

## Testing Best Practices

### General Principles
- **Arrange-Act-Assert**: Structure tests clearly with setup, execution, and verification
- **Single Responsibility**: Each test should verify one specific behavior
- **Descriptive Names**: Test names should clearly describe what is being tested
- **Independent Tests**: Tests should not depend on each other's state

### Mocking Guidelines
- **Mock External Dependencies**: Always mock CAN interfaces, file system, external APIs
- **Real Business Logic**: Don't mock your own services unless testing integration points
- **Mock Data**: Use factories for consistent test data creation
- **Async Mocking**: Use `AsyncMock` for async dependencies

### Coverage Targets
- **Services**: >90% coverage for business logic
- **API Routes**: 100% coverage for happy path and error scenarios
- **Components**: >80% coverage focusing on user interactions
- **Integration**: Critical user flows end-to-end

### Performance Testing
```python
# Backend performance testing
@pytest.mark.performance
def test_entity_query_performance(benchmark):
    """Benchmark entity query performance."""
    result = benchmark(entity_service.get_all_entities)
    assert len(result) > 0
    assert benchmark.stats["mean"] < 0.1  # 100ms max
```

## CI/CD Integration

All tests must pass in CI before code can be merged:
1. **Backend**: `poetry run pytest --cov=backend --cov-report=xml`
2. **Frontend**: `cd frontend && npm test && npm run test:coverage`
3. **Integration**: Selected integration tests on staging environment
4. **Performance**: Regression testing on performance benchmarks
