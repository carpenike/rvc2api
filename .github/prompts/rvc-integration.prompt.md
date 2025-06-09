---
mode: "agent"
description: "Add support for new RV-C DGNs and functionality"
tools: ["context7", "perplexity_ask"]
---

# RV-C Integration Guide

This guide provides a structured approach to adding support for new RV-C DGNs (Data Group Numbers) and functionality to the CoachIQ project. When completed, the integration plan will be saved to `/docs/specs/rvc-dgn-<dgn_number>.md` for review and implementation.

---

## 1. RV-C Protocol Understanding

### 1.1. DGN Identification

- What DGN(s) are you working with?
- What is the purpose of this DGN in the RV-C protocol?
- Is this a standard or proprietary DGN?

### 1.2. Message Structure

- What is the byte structure of this DGN?
- What SPNs (Suspect Parameter Numbers) are included?
- What are the data types, ranges, and units for each SPN?

### 1.3. Protocol Behavior

- How frequently is this DGN typically sent?
- Is it sent periodically or in response to events?
- Are there any special considerations for this DGN?
- Use `@perplexity_ask` to research protocol standards and behaviors

---

## 2. Implementation Planning

### 2.1. Decoder Updates

- How will the DGN be decoded in `src/rvc_decoder/decode.py`?
- What changes are needed to the RV-C specification file (`rvc.json`)?
- Are any custom parsing functions needed?
- Use `@context7` to analyze existing decoder patterns and implementation

### 2.2. Device Mapping

- How should this DGN be mapped to user-friendly names?
- What changes are needed to `coach_mapping.default.yml`?
- Are there instance-specific or coach-specific mappings needed?

### 2.3. Entity Representation

- How should this DGN be represented in the API?
- What entity model is needed?
- How will state be tracked and updated?
- Use `@context7` to analyze similar entity models in the codebase

---

## 3. Implementation Steps

### 3.1. RV-C Specification Updates

- [ ] Update `src/rvc_decoder/config/rvc.json` with DGN/SPN definitions
- [ ] Add any needed enumerations or scaling factors
- [ ] Document the DGN format in comments

### 3.2. Device Mapping Updates

- [ ] Update `src/rvc_decoder/config/coach_mapping.default.yml` with friendly names
- [ ] Add any category groupings
- [ ] Define any custom display formats

### 3.3. Decoder Implementation

- [ ] Implement or update decoding logic in `src/rvc_decoder/decode.py`
- [ ] Add any special case handling
- [ ] Ensure proper error handling

### 3.4. Entity Integration

- [ ] Create or update entity models
- [ ] Implement state tracking
- [ ] Add WebSocket event handling for real-time updates

### 3.5. API Endpoint Updates

- [ ] Add or update API endpoints
- [ ] Define request/response models
- [ ] Implement any command functionality (for writable DGNs)

### 3.6. Web UI Integration

- [ ] Add UI components for displaying/controlling the entity
- [ ] Implement any special formatting or visualization
- [ ] Add any needed JavaScript for interactivity

---

## 4. Testing Strategy

### 4.1. Decoder Testing

- [ ] Create unit tests for decoding logic
- [ ] Test with sample CAN frames
- [ ] Verify correct parsing of all SPNs

### 4.2. Integration Testing

- [ ] Test full data flow from CAN message to API/WebSocket
- [ ] Test any command functionality
- [ ] Verify correct UI updates

### 4.3. Real-world Testing

- [ ] Test with actual RV-C hardware if available
- [ ] Verify behavior matches protocol specifications
- [ ] Check for any unexpected edge cases

---

## 5. Documentation

### 5.1. Code Documentation

- [ ] Add docstrings explaining DGN purpose and structure
- [ ] Document any special handling or edge cases
- [ ] Update comments in configuration files

### 5.2. User Documentation

- [ ] Update README or user guides as needed
- [ ] Document any new API endpoints or WebSocket events
- [ ] Provide usage examples if applicable

---

## 6. RV-C Reference Information

### Common RV-C Data Types

- **UINT8**: 8-bit unsigned integer (0-255)
- **UINT16**: 16-bit unsigned integer (0-65535)
- **UINT32**: 32-bit unsigned integer (0-4294967295)
- **INT8**: 8-bit signed integer (-128 to 127)
- **INT16**: 16-bit signed integer (-32768 to 32767)
- **INT32**: 32-bit signed integer (-2147483648 to 2147483647)
- **Bit fields**: Individual bits within a byte
- **Enumeration**: Integer value mapped to predefined options

### Common RV-C Units

- Temperature: Celsius (°C)
- Voltage: Volts (V)
- Current: Amperes (A)
- Power: Watts (W)
- Pressure: Kilopascals (kPa)
- Time: Seconds (s)
- Percentage: % (0-100 or 0.00-1.00)

### Data Group Categories

- **0x0xxxx**: Manufacturer-specific
- **0x1xxxx**: Standard RV-C
- **0x2xxxx**: Reserved

### Example Implementation

```python
# Example entry in rvc.json
{
  "pgn": 20480,  # 0x5000
  "label": "AC Power Status",
  "description": "Reports the status of an AC power source",
  "transmissionRepetition": "1000ms",
  "length": 8,
  "signals": [
    {
      "name": "instance",
      "description": "Instance of the AC power source",
      "startBit": 0,
      "length": 8,
      "type": "UINT8"
    },
    {
      "name": "voltage",
      "description": "AC voltage",
      "startBit": 8,
      "length": 16,
      "type": "UINT16",
      "scale": 0.1,
      "unit": "V"
    },
    {
      "name": "current",
      "description": "AC current",
      "startBit": 24,
      "length": 16,
      "type": "UINT16",
      "scale": 0.1,
      "unit": "A"
    },
    {
      "name": "frequency",
      "description": "AC frequency",
      "startBit": 40,
      "length": 8,
      "type": "UINT8",
      "scale": 0.1,
      "unit": "Hz"
    },
    {
      "name": "status",
      "description": "Power source status",
      "startBit": 48,
      "length": 8,
      "type": "ENUM",
      "enum": {
        "0": "Disconnected",
        "1": "Connected - Inactive",
        "2": "Connected - Active",
        "3": "Connected - Fault"
      }
    }
  ]
}
```

---

## Output

Once this integration plan is complete, save it to `/docs/specs/rvc-dgn-<dgn_number>.md` where `<dgn_number>` is the hexadecimal representation of the DGN number (e.g., `rvc-dgn-0x1FEDA.md` or `rvc-dgn-0x1FF9C.md`). This document will serve as the blueprint for implementation and can be shared with the development team.
