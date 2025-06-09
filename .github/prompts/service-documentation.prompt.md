---
mode: "agent"
description: "Generate comprehensive documentation for an CoachIQ service"
tools: ["context7"]
---

# CoachIQ Service Documentation Template

This template helps create comprehensive documentation for an CoachIQ service component. Use this to document a new or existing service, API, or feature with clear explanations, examples, and technical details.

---

## 1. Service Overview

### 1.1. Purpose & Scope

- What does this service do?
- What RV-C functions or capabilities does it expose?
- What are the boundaries of this service's responsibilities?

### 1.2. User Benefits

- How does this service benefit users of the RV monitoring system?
- What problems does it solve for RV owners or integrators?
- What unique capabilities does it enable?

### 1.3. Architecture Overview

- Where does this service fit in the overall CoachIQ system?
- What are the primary components and how do they interact?
- Include a simple diagram if appropriate

---

## 2. Technical Details

### 2.1. Components

- List and describe the key Python modules that make up this service
- Explain the responsibility of each module
- Describe key classes and their relationships
- Use `@context7` to identify and document actual implementation details

### 2.2. Data Models

- Document the Pydantic models used by this service
- Explain the fields and their validation rules
- Include example JSON representations

```python
# Example model
class DeviceState(BaseModel):
    """
    Represents the current state of an RV-C device.

    Attributes:
        device_id: Unique identifier for the device
        name: Human-readable device name
        status: Current operational status
        values: Dictionary of current sensor values
        last_updated: Timestamp of last update
    """
    device_id: str
    name: str
    status: Literal["online", "offline", "error"]
    values: Dict[str, float] = {}
    last_updated: datetime

    # Example JSON output:
    # {
    #   "device_id": "inverter_1",
    #   "name": "Main Inverter",
    #   "status": "online",
    #   "values": {
    #     "output_voltage": 118.2,
    #     "output_frequency": 60.1,
    #     "load_percentage": 42.5
    #   },
    #   "last_updated": "2025-05-15T15:30:42Z"
    # }
```

### 2.3. API Endpoints

- Document the REST API endpoints provided by this service
- Include HTTP methods, parameters, request/response formats
- Provide example requests and responses
- Document error responses and status codes

```
GET /api/service/{id}

Parameters:
- id (path): The service identifier (required)
- details (query): Include additional details (optional, default: false)

Response:
200 OK
{
  "id": "inverter_1",
  "status": "online",
  "values": { ... },
  "last_updated": "2025-05-15T15:30:42Z"
}

Errors:
- 404 Not Found: Service ID not found
- 500 Internal Server Error: Failed to query service
```

### 2.4. WebSocket Events

- Document the WebSocket events emitted by this service
- Explain when events are triggered
- Include example payloads

```
Event: service_update

Triggered when:
- The service state changes
- Values are updated (throttled to max once per second)

Payload:
{
  "event": "service_update",
  "data": {
    "id": "inverter_1",
    "status": "online",
    "values": { ... },
    "timestamp": "2025-05-15T15:30:42Z"
  }
}
```

---

## 3. Implementation Examples

### 3.1. Python API Usage

- Provide examples of how to use this service from Python code
- Include imports, initialization, and common operations
- Add explanatory comments

```python
from CoachIQ.client import CoachIQClient

# Initialize the client
client = CoachIQClient("http://localhost:8000")

# Get current state
inverter = await client.get_device("inverter_1")
print(f"Inverter status: {inverter.status}")
print(f"Output voltage: {inverter.values.get('output_voltage')} V")

# Subscribe to updates
async for update in client.subscribe("service_update"):
    if update.data.id == "inverter_1":
        print(f"New output voltage: {update.data.values.get('output_voltage')} V")
```

### 3.2. JavaScript API Usage

- Provide examples of how to use this service from JavaScript
- Include WebSocket subscription examples
- Add explanatory comments

```javascript
// Connect to the WebSocket API
const socket = new WebSocket("ws://localhost:8000/ws");

// Listen for service updates
socket.addEventListener("message", (event) => {
  const data = JSON.parse(event.data);

  if (data.event === "service_update" && data.data.id === "inverter_1") {
    console.log(`Inverter status: ${data.data.status}`);
    console.log(`Output voltage: ${data.data.values.output_voltage} V`);

    // Update UI elements
    document.getElementById(
      "voltage-display"
    ).textContent = `${data.data.values.output_voltage} V`;
  }
});

// Request initial state
socket.addEventListener("open", () => {
  socket.send(
    JSON.stringify({
      action: "get_device",
      id: "inverter_1",
    })
  );
});
```

### 3.3. Console Client Usage

- Provide examples of how to use this service from the console client
- Include common commands and output formats

```
# Get device status
> get-device inverter_1
ID: inverter_1
Name: Main Inverter
Status: online
Values:
  - output_voltage: 118.2 V
  - output_frequency: 60.1 Hz
  - load_percentage: 42.5 %
Last updated: 2025-05-15 15:30:42 UTC

# Monitor device in real-time
> monitor inverter_1
Monitoring inverter_1 (press Ctrl+C to stop)...
[15:30:45] output_voltage: 118.2 V, load_percentage: 42.5 %
[15:30:46] output_voltage: 118.3 V, load_percentage: 43.1 %
```

---

## 4. Configuration

### 4.1. Settings

- Document configuration settings and environment variables
- Explain default values and valid options
- Include examples

```
SERVICE_ENABLED=true
  Enables or disables the service (default: true)

SERVICE_UPDATE_INTERVAL=1000
  Update interval in milliseconds (default: 1000)
  Min: 100, Max: 60000
```

### 4.2. Dependencies

- List required dependencies
- Explain any version constraints
- Document any hardware requirements

---

## 5. Troubleshooting

### 5.1. Common Issues

- List common issues users might encounter
- Provide diagnostic steps
- Include solutions

### 5.2. Logging

- Explain what is logged and where
- Document log levels
- Provide examples of log output for key scenarios

### 5.3. Debugging

- Offer debugging techniques
- Explain how to enable debug mode
- Provide guidance on gathering information for bug reports

---

## 6. Development Guidelines

### 6.1. Extension Points

- Document how this service can be extended
- Explain interfaces or hooks that can be used
- Provide examples of custom extensions

### 6.2. Testing

- Explain how to test this service
- Document any test utilities or fixtures
- Provide example test code

---

## 7. References

### 7.1. Related Documentation

- Link to related documentation
- Reference RV-C specifications or standards
- Include research or design documents

### 7.2. External Resources

- Link to external resources or libraries
- Reference community discussions or tutorials
- Provide credit to contributors
