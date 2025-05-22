---
mode: 'agent'
description: 'Plan a new feature by breaking it down into components'
tools: ['context7']
---

# Feature Planning Guide

- **Feature Name:** [Concise name]
- **Status:** [Proposed | In Planning | Approved]
- **Date:** [YYYY-MM-DD]
- **Author(s):** [Name(s)]
- **Related ADR:** [Link, if applicable]

**Summary:**
[Briefly describe the feature and its purpose.]

---

## 1. Feature Overview

### 1.1. Core Purpose
- What is the primary goal of this feature?
- What problem does it solve for users?

### 1.2. User Perspective
- How will users interact with this feature?
- What is the expected user experience?

### 1.3. System Integration
- How does this feature integrate with the existing rvc2api components?
- What existing components will be affected?
- Use `@context7` to identify existing patterns and components to leverage

---

## 2. Technical Breakdown

### 2.1. Data Layer
- What data structures are needed?
- How will data flow through the system?
- What Pydantic models need to be created or modified?
- Use `@context7` to analyze existing model patterns

### 2.2. Backend Components
- What new Python modules/classes/functions are needed?
- What existing components need modification?
- How will the feature interact with the CAN bus (if applicable)?
- What FastAPI endpoints are required?
- Use `@context7` to analyze similar endpoint implementations and patterns

### 2.3. Frontend Components
- What UI components are needed?
- How will data be displayed or collected?
- What JavaScript functionality is required?
- How will WebSocket communication be used (if applicable)?

### 2.4. Configuration Requirements
- What configuration options should be exposed?
- How will these be stored and accessed?

---

## 3. Implementation Plan

### 3.1. Phase 1: Core Structure
- [ ] Define data models and structures
- [ ] Implement basic service functionality
- [ ] Create API endpoints

### 3.2. Phase 2: UI and Integration
- [ ] Build UI components
- [ ] Implement WebSocket communication (if applicable)
- [ ] Connect UI to backend services

### 3.3. Phase 3: Testing and Refinement
- [ ] Write unit tests
- [ ] Write integration tests
- [ ] Refine based on testing results

---

## 4. Testing Strategy

### 4.1. Unit Testing
- What units of code need tests?
- What mocking will be required?

### 4.2. Integration Testing
- How will the complete feature be tested?
- What edge cases need to be considered?

### 4.3. Manual Testing
- What manual test procedures are needed?
- What environments should be tested?

---

## 5. Considerations and Constraints

### 5.1. Performance Considerations
- Are there any potential performance bottlenecks?
- How will this feature perform under load?

### 5.2. Security Considerations
- Are there any security implications to consider?
- How will user input be validated?

### 5.3. Backward Compatibility
- Will this feature affect existing functionality?
- How will migrations or transitions be handled?

---

## 6. Documentation Needs

### 6.1. Code Documentation
- What documentation is needed for developers?
- What docstrings need to be written?

### 6.2. User Documentation
- What documentation is needed for users?
- Are there usage examples to include?

---

## 7. Timeline and Milestones

### 7.1. Development Phases
- What are the key development milestones?
- What is the estimated timeline for each phase?

### 7.2. Dependencies
- Are there any dependencies on other features or components?
- Are there any external dependencies or constraints?

---

## 8. Future Considerations

### 8.1. Potential Enhancements
- What future enhancements might be considered?
- What features are being deferred to later iterations?

### 8.2. Maintenance Implications
- What ongoing maintenance will this feature require?
- Are there any potential technical debt concerns?

---

## Output

Once this plan is complete, save it to `/docs/specs/<feature-name>.md` where `<feature-name>` is a kebab-case name descriptive of the feature (e.g., `tank-monitoring-service.md` or `websocket-reconnection-handler.md`). This document will serve as the blueprint for implementation and can be shared with the development team.
