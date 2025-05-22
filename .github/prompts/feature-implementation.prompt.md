---
mode: 'agent'
description: 'Implement a new feature for the rvc2api project'
tools: ['context7']
---

# Feature Implementation Guide

- **Feature Name:** [Concise name]
- **Status:** [Proposed | In Progress | Completed]
- **Date:** [YYYY-MM-DD]
- **Author(s):** [Name(s)]
- **Related Spec:** [Link to `/docs/specs/feature-xyz.md`]
- **Related ADR:** [Link, if applicable]

**Summary:**  
[Briefly describe the feature and its purpose.]

---

## Feature Implementation Process

### 1. Review Service Specification
- [ ] Review the service specification document from `/docs/specs/`
- [ ] Clarify any ambiguities or missing details
- [ ] Understand how this feature integrates with the existing codebase
- [ ] Use `@context7` to analyze related components in the codebase

### 2. Core Implementation

#### 2.1. Data Models
- [ ] Define needed Pydantic models in appropriate location
  - For shared models: `src/common/models.py`
  - For service-specific models: `src/core_daemon/models.py` or new module
- [ ] Include full type hints and field validations
- [ ] Add appropriate docstrings to each model

#### 2.2. Backend Service Logic
- [ ] Implement core business logic
  - For RV-C specific logic: Add to `src/rvc_decoder/`
  - For API-related logic: Create or update modules in `src/core_daemon/`
- [ ] Follow error handling guidelines
  - Use specific exception types
  - Log exceptions with appropriate severity
  - Provide user-friendly error messages
- [ ] Add appropriate logging

#### 2.3. API Integration
- [ ] Add API endpoints to appropriate router in `src/core_daemon/api_routers/`
- [ ] Define route parameters, response models, and error handling
- [ ] Update OpenAPI documentation with detailed descriptions
- [ ] For real-time updates, integrate with WebSocket in `src/core_daemon/websocket.py`

#### 2.4. Web UI Components (Current HTML/JS)
- [ ] Add HTML templates to `src/core_daemon/web_ui/templates/`
- [ ] Add static assets to `src/core_daemon/web_ui/static/`
- [ ] Add JavaScript for client-side logic
- [ ] Ensure responsive design for various screen sizes

### 3. Testing

#### 3.1. Unit Tests
- [ ] Write unit tests for new core functions
- [ ] Test both success and error cases
- [ ] Mock external dependencies (CAN bus, filesystem, etc.)
- [ ] Place tests in corresponding path in `tests/` directory

#### 3.2. Integration Tests
- [ ] Add integration tests that validate full workflow
- [ ] Test API endpoints directly
- [ ] Test WebSocket communication if applicable

### 4. Documentation

#### 4.1. Code Documentation
- [ ] Add module-level docstrings
- [ ] Document all public functions, classes, and methods
- [ ] Include examples in docstrings when helpful

#### 4.2. User-Facing Documentation
- [ ] Update README.md if needed
- [ ] Add any configuration or setup instructions

### 5. Final Review
- [ ] Review for coding style (black, ruff/flake8)
- [ ] Check for type hint completeness
- [ ] Verify error handling coverage
- [ ] Ensure all tests pass

---

## Best Practices for rvc2api

### Python Coding Standards
- Follow PEP 8 and use black for formatting (line length: 100)
- Use full type hints and Pydantic for data validation
- Group imports: standard library → third-party → local
- Include module-level docstrings summarizing file purpose
- Use Google-style or PEP 257 docstrings for functions and classes

### Error Handling
- Catch and log expected exceptions with appropriate context
- Use custom error classes where appropriate
- Avoid bare `except:` without re-raising or limiting scope

### Testing
- Test both success and error paths
- Mock external dependencies (CAN bus, file system)
- Use descriptive test names that explain what's being tested

### Performance Considerations
- Be mindful of real-time requirements for CAN bus communication
- Consider the impact of long-running operations on WebSocket connections
- Use asynchronous patterns appropriately

---

## Implementation Examples

### Example: Adding a New API Endpoint

```python
# In src/core_daemon/api_routers/my_router.py

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/my-feature", tags=["my-feature"])

class MyRequestModel(BaseModel):
    """
    Model for the request body of the my-feature endpoint.

    Attributes:
        parameter_1: Description of parameter 1
        parameter_2: Description of parameter 2
    """
    parameter_1: str
    parameter_2: int

class MyResponseModel(BaseModel):
    """
    Model for the response from the my-feature endpoint.

    Attributes:
        result: Description of the result
        status: Status of the operation
    """
    result: str
    status: str

@router.post("/action", response_model=MyResponseModel)
async def perform_action(request: MyRequestModel):
    """
    Perform an action based on the provided parameters.

    Args:
        request: The request body containing parameters

    Returns:
        A response object with the result and status

    Raises:
        HTTPException: If the action cannot be performed
    """
    try:
        # Implement action logic
        result = f"Processed {request.parameter_1}"
        return MyResponseModel(result=result, status="success")
    except Exception as e:
        logger.exception(f"Error performing action: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

### Example: Adding WebSocket Support

```python
# In src/core_daemon/websocket.py

async def handle_my_feature_updates(websocket: WebSocket, app_state: dict):
    """
    Handle WebSocket connections for my-feature updates.

    Sends real-time updates about feature state changes.

    Args:
        websocket: The WebSocket connection
        app_state: The shared application state
    """
    # Setup code

    try:
        while True:
            # Listen for changes and send updates
            if change_detected:
                await websocket.send_json({
                    "type": "my_feature_update",
                    "data": updated_data
                })
            await asyncio.sleep(0.1)
    except WebSocketDisconnect:
        # Cleanup code
```
