---
mode: 'agent'
description: 'Define a new service or feature for the rvc2api project'
tools: ['context7']
---

# New Service Specification Template

- **Service Name:** [Concise name]
- **Status:** [Proposed | In Review | Approved]
- **Date:** [YYYY-MM-DD]
- **Author(s):** [Name(s)]
- **Related ADR:** [Link, if applicable]

**Summary:**
[Briefly describe what this service does and why it is needed.]

This template helps you define a new service or feature for the rvc2api project. Use this as a starting point to clearly articulate what you want to build before implementation begins. When completed, the specification will be saved to `/docs/specs/<service-name>.md` for review and implementation.

---

## 1. Service Overview

### 1.1. Purpose
- What problem does this service solve?
- How does it fit into the broader rvc2api ecosystem?

### 1.2. Core Functionality
- What are the primary capabilities this service will provide?
- Who is the intended user of this service?

### 1.3. Integration Points
- How does this service interact with the RV-C bus?
- How will it connect with other components of rvc2api?

---

## 2. Technical Requirements

### 2.1. Data Requirements
- What data does this service need to access or store?
- What is the data flow (input → processing → output)?
- Are there any special considerations for data formatting or validation?

### 2.2. API Requirements
- What API endpoints are needed?
- For each endpoint, define:
  - HTTP method
  - Path
  - Required parameters
  - Response format
  - Error handling

### 2.3. WebSocket Requirements (if applicable)
- What real-time updates will this service provide?
- What is the WebSocket message format?
- What events trigger messages?

### 2.4. Web UI Requirements (if applicable)
- What UI components are needed?
- How will users interact with this service?
- What state needs to be maintained in the UI?

---

## 3. Implementation Considerations

### 3.1. Python Components
- What new modules/classes/functions are needed?
- Where will they be placed in the codebase?
- Any external dependencies required?

### 3.2. RV-C Interaction
- What RV-C DGNs (Data Group Numbers) are involved?
- Reading or writing to the CAN bus?
- Any custom device mapping requirements?

### 3.3. Testing Strategy
- How will the service be tested?
- What test cases are needed?
- Any special mocking requirements for CAN bus?

---

## 4. Implementation Plan

### 4.1. Phase 1: Core Components
- List the initial components that need to be implemented

### 4.2. Phase 2: Integration
- Describe how to integrate with existing services

### 4.3. Phase 3: UI and Testing
- List UI components and test coverage needed

---

## 5. Acceptance Criteria

- What defines a successful implementation?
- List specific criteria that must be met for this service to be considered complete
- Include performance considerations if applicable

---

## Notes and Considerations

- Any additional notes, research, or context relevant to this service
- Known limitations or edge cases to be aware of
- Future enhancement possibilities

---

## Output

Once this specification is complete, save it to `/docs/specs/<service-name>.md` where `<service-name>` is a kebab-case name descriptive of the service (e.g., `tank-monitor-service.md` or `weather-integration.md`). This document will serve as the blueprint for implementation and can be shared with the development team.
