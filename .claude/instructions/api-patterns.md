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

### Cross-Protocol Entity Control (NEW)
Enhanced command structure for multi-protocol environments:

```typescript
interface CrossProtocolEntityControlCommand extends EntityControlCommand {
  target_protocol?: "rvc" | "j1939" | "firefly" | "spartan_k2";
  bridge_protocols?: boolean;  // Enable automatic protocol bridging
  safety_validation?: boolean; // Enable safety interlock validation
  network_segment?: string;    // Target specific network segment
  chassis_safety_override?: boolean; // Allow authorized chassis safety override
  firefly_multiplexed?: boolean; // Handle Firefly multiplexed operations
}
```

### Safety Interlock Commands (NEW)
For chassis and safety-critical operations:

```typescript
interface SafetyInterlockCommand {
  system_type: "slides" | "awnings" | "leveling_jacks" | "chassis" | "brakes" | "suspension";
  operation: "extend" | "retract" | "position" | "emergency_stop";
  safety_conditions: {
    park_brake_engaged?: boolean;
    engine_off?: boolean;
    wind_speed_below?: number;  // mph
    level_within_tolerance?: boolean;
  };
  validation_level: "strict" | "warn" | "bypass";
  override_code?: string;  // For authorized overrides
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

// Cross-protocol chassis control with safety validation
{
  "command": "set",
  "target_protocol": "spartan_k2",
  "safety_validation": true,
  "custom_data": {
    "brake_pressure_target": 85.0,
    "system_check_required": true
  }
}

// Firefly multiplexed operation
{
  "command": "custom",
  "target_protocol": "firefly",
  "firefly_multiplexed": true,
  "custom_data": {
    "zone_lighting": {
      "living_room": {"brightness": 75, "scene": "evening"},
      "bedroom": {"brightness": 50, "scene": "nighttime"}
    }
  }
}

// Safety interlock operation
{
  "command": "custom",
  "system_type": "slides",
  "operation": "extend",
  "safety_conditions": {
    "park_brake_engaged": true,
    "engine_off": true,
    "level_within_tolerance": true
  },
  "validation_level": "strict"
}
```

### Command Response Format
```typescript
interface EntityControlResponse {
  status: "success" | "error" | "pending" | "safety_blocked";  // Use status instead of success boolean
  entity_id: string;
  command: EntityControlCommand | CrossProtocolEntityControlCommand;
  result?: {
    previous_state?: string;
    new_state?: string;
    timestamp: string;
    protocol_used?: string;  // Which protocol executed the command
    safety_validation?: SafetyValidationResult;
    network_segment?: string;
  };
  error?: {
    code: string;
    message: string;
    details?: Record<string, any>;
    safety_violations?: string[];  // Safety interlock violations
  };
}

interface SafetyValidationResult {
  is_safe: boolean;
  violations: string[];
  system_status: {
    brake_pressure?: number;
    suspension_level_differential?: number;
    steering_pressure?: number;
    park_brake_engaged?: boolean;
    engine_status?: string;
  };
  override_available?: boolean;
}
```

## FastAPI Implementation Patterns

### Router Structure
```python
from fastapi import APIRouter, Depends, HTTPException
from backend.models.entity import EntityControlCommand, EntityControlResponse
from backend.services.entity_service import EntityService
from backend.core.dependencies import get_entity_service

router = APIRouter(prefix="/api/entities", tags=["entities"])

@router.post("/{entity_id}/control", response_model=EntityControlResponse)
async def control_entity(
    entity_id: str,
    command: CrossProtocolEntityControlCommand,
    entity_service: EntityService = Depends(get_entity_service),
    diagnostics: DiagnosticsHandler = Depends(get_diagnostics_handler),
    spartan_k2: SpartanK2Service = Depends(get_spartan_k2_service)
) -> EntityControlResponse:
    """
    Control an entity with cross-protocol support and safety validation.

    Supports all RV-C, J1939, Firefly, and Spartan K2 device types including
    lights, locks, awnings, slides, chassis systems, and custom device commands.

    Args:
        entity_id: Unique identifier for the entity
        command: Cross-protocol control command with safety validation

    Returns:
        Result of the control operation with safety status

    Raises:
        404: Entity not found
        400: Invalid command for entity type or safety interlock failure
        503: CAN bus communication error
    """
    try:
        # Validate safety interlocks for chassis/safety-critical commands
        if command.safety_validation and command.target_protocol == "spartan_k2":
            safety_result = await spartan_k2.validate_safety_interlocks()
            if not safety_result.is_safe:
                return EntityControlResponse(
                    status="safety_blocked",
                    entity_id=entity_id,
                    command=command,
                    error={
                        "code": "SAFETY_INTERLOCK_VIOLATION",
                        "message": "Safety interlock validation failed",
                        "safety_violations": safety_result.violations
                    }
                )

        # Execute cross-protocol control with automatic protocol bridging
        result = await entity_service.control_entity_cross_protocol(entity_id, command)

        # CRITICAL: Use result.status, not result.success
        if result.status == "success":
            logger.info(f"Cross-protocol command '{command.command}' executed successfully for entity '{entity_id}' via {result.result.protocol_used}")

        return result
    except EntityNotFoundError:
        raise HTTPException(status_code=404, detail=f"Entity {entity_id} not found")
    except InvalidCommandError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except CANBusError as e:
        raise HTTPException(status_code=503, detail=f"CAN bus error: {e}")
    except SafetyInterlockError as e:
        raise HTTPException(status_code=400, detail=f"Safety interlock failed: {e}")
```

### Query Filtering
```python
@router.get("", response_model=EntityListResponse)
async def list_entities(
    device_type: Optional[str] = None,
    state: Optional[str] = None,
    location: Optional[str] = None,
    protocol: Optional[str] = Query(None, regex="^(rvc|j1939|firefly|spartan_k2)$"),
    network_segment: Optional[str] = None,
    health_status: Optional[str] = Query(None, regex="^(healthy|warning|critical|unknown)$"),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    entity_service: EntityService = Depends(get_entity_service),
    diagnostics: DiagnosticsHandler = Depends(get_diagnostics_handler)
) -> EntityListResponse:
    """
    List entities with optional cross-protocol filtering and health status.

    Query Parameters:
        device_type: Filter by device type (light, lock, slide, chassis, etc.)
        state: Filter by current state (on, off, open, closed, etc.)
        location: Filter by physical location
        protocol: Filter by protocol (rvc, j1939, firefly, spartan_k2)
        network_segment: Filter by network segment (house, chassis, etc.)
        health_status: Filter by diagnostic health status
        limit: Maximum number of entities to return
        offset: Number of entities to skip for pagination
    """
    filters = CrossProtocolEntityFilters(
        device_type=device_type,
        state=state,
        location=location,
        protocol=protocol,
        network_segment=network_segment,
        health_status=health_status
    )

    # Get entities with cross-protocol health status
    entities = await entity_service.list_entities_cross_protocol(
        filters=filters,
        limit=limit,
        offset=offset
    )

    # Enhance with diagnostic health information
    if health_status:
        health_data = await diagnostics.get_entities_health_status(
            entity_ids=[e.id for e in entities]
        )
        for entity in entities:
            entity.health_status = health_data.get(entity.id, "unknown")

    return EntityListResponse(
        entities=entities,
        total=len(entities),
        limit=limit,
        offset=offset,
        protocols_included=list(set(e.protocol for e in entities if hasattr(e, 'protocol')))
    )
```

## WebSocket Real-time Updates

### Message Format
```typescript
interface WebSocketMessage {
  type: "entity_update" | "entity_added" | "entity_removed" | "system_status" |
        "cross_protocol_event" | "safety_alert" | "diagnostic_event";
  timestamp: string;
  data: EntityUpdate | SystemStatus | CrossProtocolEvent | SafetyAlert | DiagnosticEvent;
}

interface EntityUpdate {
  entity_id: string;
  changes: Partial<EntityState>;
  source: "user_command" | "can_bus" | "system" | "schedule" | "safety_interlock";
  protocol: "rvc" | "j1939" | "firefly" | "spartan_k2";
  network_segment?: string;
}

interface CrossProtocolEvent {
  event_type: "protocol_bridge" | "network_switch" | "fault_correlation";
  source_protocol: string;
  target_protocol: string;
  entities_affected: string[];
  correlation_id?: string;
}

interface SafetyAlert {
  alert_type: "interlock_violation" | "system_fault" | "emergency_stop";
  system: "brakes" | "suspension" | "steering" | "slides" | "awnings";
  severity: "warning" | "critical" | "emergency";
  violations: string[];
  override_available: boolean;
}

interface DiagnosticEvent {
  event_type: "fault_detected" | "fault_cleared" | "prediction_updated";
  protocol: string;
  system_type: string;
  fault_codes: string[];
  prediction_confidence?: number;
  maintenance_urgency?: "immediate" | "urgent" | "soon" | "scheduled";
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

### Core API Patterns (MANDATORY)
- **Unified Endpoints**: Use `/api/entities` pattern only, never separate device-type endpoints
- **Cross-Protocol Commands**: All entity control supports multi-protocol operations with safety validation
- **Health Endpoints**: Use `/healthz` at root level, not `/api/healthz`
- **Real-time Data**: Use WebSocket for streams, REST for queries, implement fallback
- **Response Format**: Use `status` field instead of boolean `success`
- **Comprehensive Documentation**: Include examples, error scenarios, and response schemas
- **Error Handling**: Structured error responses with proper HTTP status codes
- **Type Safety**: Full TypeScript types generated from OpenAPI schema

### Multi-Protocol Requirements (NEW)
- **Protocol Support**: All endpoints must handle RV-C, J1939, Firefly, and Spartan K2 protocols
- **Safety Validation**: Chassis and safety-critical operations require interlock validation
- **Cross-Protocol Bridging**: Enable automatic protocol translation when beneficial
- **Network Awareness**: Support multi-network environments with fault isolation
- **Diagnostic Integration**: Include health status and fault correlation in entity operations
- **Performance Monitoring**: Integrate with performance analytics for optimization recommendations

### Safety Compliance (CRITICAL)
- **Interlock Validation**: All chassis operations must validate safety interlocks
- **Emergency Stop**: Support immediate emergency stop across all protocols
- **Authorization**: Safety overrides require proper authorization codes
- **Audit Logging**: All safety-related operations must be logged for compliance
- **Real-time Alerts**: Safety violations must trigger immediate WebSocket alerts
- **Graceful Degradation**: System must continue operating safely when components fail
