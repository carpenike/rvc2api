# API Design Patterns

## Unified Entity API Design

### Core Principle
**All entity operations use the `/api/entities` endpoint pattern.** Never create separate endpoints like `/api/lights`, `/api/locks`, etc. This ensures a unified, type-safe, and extensible API surface.

### Entity Endpoint Structure
```
GET    /api/entities                    # List all entities
GET    /api/entities?device_type=light  # Filter by device type
GET    /api/entities/{id}               # Get specific entity
POST   /api/entities/{id}/control       # Control entity
PUT    /api/entities/{id}               # Update entity configuration
DELETE /api/entities/{id}               # Remove entity (admin only)
```

## Entity Control Commands

### Standardized Command Structure
All entity control operations use a consistent command format:

```typescript
interface EntityControlCommand {
  command: "set" | "toggle" | "brightness_up" | "brightness_down" | "custom";
  state?: "on" | "off";
  brightness?: number;      // 0-100
  duration?: number;        // Duration in seconds for timed operations
  custom_data?: Record<string, any>;  // Device-specific parameters
}
```

### Command Examples
```json
// Turn light on
{
  "command": "set",
  "state": "on"
}

// Set light to 75% brightness
{
  "command": "set",
  "state": "on",
  "brightness": 75
}

// Toggle current state
{
  "command": "toggle"
}

// Increase brightness by 10%
{
  "command": "brightness_up"
}

// Custom device command
{
  "command": "custom",
  "custom_data": {
    "awning_position": 50,
    "auto_retract": true
  }
}
```

### Command Response Format
```typescript
interface EntityControlResponse {
  status: "success" | "error" | "pending";  // Use status instead of success boolean
  entity_id: string;
  command: EntityControlCommand;
  result?: {
    previous_state?: string;
    new_state?: string;
    timestamp: string;
  };
  error?: {
    code: string;
    message: string;
    details?: Record<string, any>;
  };
}
```

## FastAPI Implementation Patterns

### Router Structure
```python
from fastapi import APIRouter, Depends, HTTPException
from backend.models.entity import EntityControlCommand, EntityControlResponse
from backend.services.entity_service import EntityService

router = APIRouter(prefix="/api/entities", tags=["entities"])

@router.post("/{entity_id}/control", response_model=EntityControlResponse)
async def control_entity(
    entity_id: str,
    command: EntityControlCommand,
    entity_service: EntityService = Depends(get_entity_service)
) -> EntityControlResponse:
    """
    Control an entity with the specified command.

    Supports all RV-C device types including lights, locks, awnings,
    slides, and custom device commands.

    Args:
        entity_id: Unique identifier for the entity
        command: Control command with action and parameters

    Returns:
        Result of the control operation

    Raises:
        404: Entity not found
        400: Invalid command for entity type
        503: CAN bus communication error
    """
    try:
        result = await entity_service.control_entity(entity_id, command)

        # CRITICAL: Use result.status, not result.success
        if result.status == "success":
            logger.info(f"Control command '{command.command}' executed successfully for entity '{entity_id}'")

        return result
    except EntityNotFoundError:
        raise HTTPException(status_code=404, detail=f"Entity {entity_id} not found")
    except InvalidCommandError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except CANBusError as e:
        raise HTTPException(status_code=503, detail=f"CAN bus error: {e}")
```

### Query Filtering
```python
@router.get("", response_model=EntityListResponse)
async def list_entities(
    device_type: Optional[str] = None,
    state: Optional[str] = None,
    location: Optional[str] = None,
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    entity_service: EntityService = Depends(get_entity_service)
) -> EntityListResponse:
    """
    List entities with optional filtering.

    Query Parameters:
        device_type: Filter by device type (light, lock, slide, etc.)
        state: Filter by current state (on, off, open, closed, etc.)
        location: Filter by physical location
        limit: Maximum number of entities to return
        offset: Number of entities to skip for pagination
    """
    filters = EntityFilters(
        device_type=device_type,
        state=state,
        location=location
    )

    entities = await entity_service.list_entities(
        filters=filters,
        limit=limit,
        offset=offset
    )

    return EntityListResponse(
        entities=entities,
        total=len(entities),
        limit=limit,
        offset=offset
    )
```

## WebSocket Real-time Updates

### Message Format
```typescript
interface WebSocketMessage {
  type: "entity_update" | "entity_added" | "entity_removed" | "system_status";
  timestamp: string;
  data: EntityUpdate | SystemStatus;
}

interface EntityUpdate {
  entity_id: string;
  changes: Partial<EntityState>;
  source: "user_command" | "can_bus" | "system" | "schedule";
}
```

### WebSocket Implementation
```python
from fastapi import WebSocket, WebSocketDisconnect
from backend.websocket.handlers import ConnectionManager

manager = ConnectionManager()

@app.websocket("/ws/entities")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time entity updates.

    Sends entity state changes, system status updates, and
    CAN bus activity to connected clients.
    """
    await manager.connect(websocket)
    try:
        while True:
            # Handle incoming messages (subscriptions, etc.)
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get("type") == "subscribe":
                await manager.subscribe_client(websocket, message.get("topics", []))

    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Broadcast entity updates
async def broadcast_entity_update(entity_id: str, changes: dict):
    """Broadcast entity state changes to subscribed clients."""
    message = {
        "type": "entity_update",
        "timestamp": datetime.now().isoformat(),
        "data": {
            "entity_id": entity_id,
            "changes": changes,
            "source": "can_bus"
        }
    }
    await manager.broadcast_to_topic("entities", json.dumps(message))
```

## Frontend Integration Patterns

### API Client Structure
```typescript
class EntityApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = "") {
    this.baseUrl = baseUrl;
  }

  async getEntities(filters?: EntityFilters): Promise<Entity[]> {
    const params = new URLSearchParams();
    if (filters?.deviceType) params.set("device_type", filters.deviceType);
    if (filters?.state) params.set("state", filters.state);

    const response = await fetch(`${this.baseUrl}/api/entities?${params}`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);

    const data = await response.json();
    return data.entities;
  }

  async controlEntity(
    entityId: string,
    command: EntityControlCommand
  ): Promise<EntityControlResponse> {
    const response = await fetch(`${this.baseUrl}/api/entities/${entityId}/control`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(command)
    });

    if (!response.ok) {
      const error = await response.json();
      throw new EntityControlError(error.detail || "Control failed");
    }

    return response.json();
  }
}
```

### React Query Integration
```typescript
export function useControlEntity() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ entityId, command }: {
      entityId: string;
      command: EntityControlCommand
    }) => apiClient.controlEntity(entityId, command),

    onMutate: async ({ entityId, command }) => {
      // Optimistic update
      await queryClient.cancelQueries({ queryKey: ["entities"] });

      const previousEntities = queryClient.getQueryData<Entity[]>(["entities"]);

      if (previousEntities) {
        const optimisticEntities = previousEntities.map(entity =>
          entity.id === entityId
            ? { ...entity, ...predictEntityState(entity, command) }
            : entity
        );

        queryClient.setQueryData(["entities"], optimisticEntities);
      }

      return { previousEntities };
    },

    onError: (err, variables, context) => {
      // Revert optimistic update on error
      if (context?.previousEntities) {
        queryClient.setQueryData(["entities"], context.previousEntities);
      }
    },

    onSettled: () => {
      // Refetch to ensure consistency
      queryClient.invalidateQueries({ queryKey: ["entities"] });
    }
  });
}
```

## OpenAPI Documentation Standards

### Comprehensive Endpoint Documentation
```python
@router.post(
    "/{entity_id}/control",
    response_model=EntityControlResponse,
    summary="Control Entity",
    description="Send control commands to RV-C entities",
    responses={
        200: {
            "description": "Command executed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "entity_id": "light_1",
                        "command": {"command": "set", "state": "on", "brightness": 75},
                        "result": {
                            "previous_state": "off",
                            "new_state": "on",
                            "timestamp": "2024-01-15T10:30:00Z"
                        }
                    }
                }
            }
        },
        404: {"description": "Entity not found"},
        400: {"description": "Invalid command"},
        503: {"description": "CAN bus communication error"}
    },
    tags=["Entity Control"]
)
```

### Model Documentation
```python
class EntityControlCommand(BaseModel):
    """
    Command structure for controlling RV-C entities.

    Supports standardized commands across all device types with
    device-specific parameters via custom_data field.
    """

    command: Literal["set", "toggle", "brightness_up", "brightness_down", "custom"] = Field(
        description="Command type to execute"
    )
    state: Optional[Literal["on", "off"]] = Field(
        None,
        description="Target state for set commands"
    )
    brightness: Optional[int] = Field(
        None,
        ge=0,
        le=100,
        description="Brightness level (0-100) for dimmable devices"
    )
    duration: Optional[int] = Field(
        None,
        gt=0,
        description="Duration in seconds for timed operations"
    )
    custom_data: Optional[Dict[str, Any]] = Field(
        None,
        description="Device-specific parameters for custom commands"
    )

    class Config:
        schema_extra = {
            "examples": [
                {
                    "command": "set",
                    "state": "on",
                    "brightness": 75
                },
                {
                    "command": "toggle"
                },
                {
                    "command": "custom",
                    "custom_data": {
                        "awning_position": 50,
                        "auto_retract": True
                    }
                }
            ]
        }
```

## Error Handling Patterns

### Standardized Error Responses
```python
class EntityError(Exception):
    """Base exception for entity operations."""
    pass

class EntityNotFoundError(EntityError):
    """Entity with specified ID not found."""
    pass

class InvalidCommandError(EntityError):
    """Command not valid for entity type."""
    pass

class CANBusError(EntityError):
    """CAN bus communication failure."""
    pass

# Global exception handler
@app.exception_handler(EntityError)
async def entity_error_handler(request: Request, exc: EntityError):
    status_code = 400
    if isinstance(exc, EntityNotFoundError):
        status_code = 404
    elif isinstance(exc, CANBusError):
        status_code = 503

    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "type": exc.__class__.__name__,
                "message": str(exc),
                "timestamp": datetime.now().isoformat()
            }
        }
    )
```

## Security Considerations

### Rate Limiting
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/{entity_id}/control")
@limiter.limit("10/minute")  # Prevent rapid command flooding
async def control_entity(request: Request, ...):
    # Implementation
```

### Input Validation
```python
@router.post("/{entity_id}/control")
async def control_entity(
    entity_id: str = Path(..., regex=r"^[a-zA-Z0-9_-]+$"),  # Validate entity ID format
    command: EntityControlCommand,  # Pydantic handles validation
    ...
):
    # Additional business logic validation
    if command.brightness is not None and not entity.supports_dimming:
        raise InvalidCommandError("Entity does not support brightness control")
```

## Health Endpoint Standards

### Health Check Pattern
Health endpoints should be at the root level, not under `/api/`:

```typescript
// CORRECT: Frontend health check
export async function fetchHealthStatus(): Promise<HealthStatus> {
  const url = '/healthz';  // Root level, not /api/healthz
  const response = await fetch(url);
  return response.json();
}

// WRONG: Do not use API prefix for health
const url = '/api/healthz';  // Incorrect pattern
```

### Health Implementation
```python
@app.get("/healthz", tags=["health"])
async def health_check():
    """System health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}
```

## Real-time Data Patterns

### WebSocket vs REST Polling
Use WebSocket for real-time data streams, REST for one-time queries:

```typescript
// CORRECT: WebSocket for real-time CAN data
const { isConnected, error } = useCANScanWebSocket({
  autoConnect: !isPaused,
  onMessage: (message: CANMessage) => {
    setMessages(prev => [...prev, message].slice(-maxMessages))
  }
})

// WRONG: Polling for real-time data
useEffect(() => {
  const interval = setInterval(async () => {
    const data = await fetchCANMessages(); // Creates unnecessary load
  }, 100);
}, []);
```

### WebSocket Fallback Strategy
Always implement graceful fallback from WebSocket to REST:

```typescript
const [connectionMethod, setConnectionMethod] = useState<'websocket' | 'polling'>('websocket');

// Fallback to polling if WebSocket fails
useEffect(() => {
  if (wsError && connectionMethod === 'websocket') {
    console.warn('WebSocket failed, falling back to polling');
    setConnectionMethod('polling');
  }
}, [wsError]);
```

## Critical Requirements

- **Unified Endpoints**: Use `/api/entities` pattern only, never separate device-type endpoints
- **Standardized Commands**: All entity control uses the same command structure
- **Health Endpoints**: Use `/healthz` at root level, not `/api/healthz`
- **Real-time Data**: Use WebSocket for streams, REST for queries, implement fallback
- **Response Format**: Use `status` field instead of boolean `success`
- **Comprehensive Documentation**: Include examples, error scenarios, and response schemas
- **Error Handling**: Structured error responses with proper HTTP status codes
- **Type Safety**: Full TypeScript types generated from OpenAPI schema
