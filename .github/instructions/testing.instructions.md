---
applyTo: "tests/**/*.py"
---

# Testing Guidelines

- Use `pytest` and `pytest-asyncio` for async test coverage
- Tests should mirror source file paths:
  - `tests/backend/test_config.py` → `backend/core/config.py`
- Mock CANbus, Modbus, or filesystem access in unit tests
- Add a brief docstring explaining each test's intent
- Ensure test code passes linting and type checking requirements
- Create proper type stubs for mocked components when needed

## MCP Tools for Testing

### @context7 Use Cases

- Find existing test patterns: `@context7 test_can_processing implementation`
- Look up mock usage: `@context7 MockCANBus usage`
- Find test fixtures: `@context7 pytest fixtures for websockets`
- Check test coverage: `@context7 tests for api_router_entities`

### @perplexity Use Cases

- Research testing techniques: `@perplexity testing async FastAPI endpoints`
- Find test isolation patterns: `@perplexity mocking WebSocket connections in pytest`
- Learn about test frameworks: `@perplexity pytest-asyncio vs asynctest`

## Example Test

```python
def test_canbus_command_send():
    """Test that CANbus commands are properly formatted and transmitted."""
    # Setup test fixtures
    mock_can_bus = MockCANBus()
    interface = CANInterface(bus=mock_can_bus)

    # Execute the function under test
    result = interface.send_command("1FEBD,1,255,0,0,0,0,0,0")

    # Verify the results
    assert result is True
    assert mock_can_bus.last_message.arbitration_id == 0x1FEBD
    assert mock_can_bus.last_message.data == bytes([1, 255, 0, 0, 0, 0, 0, 0])
```
