---
mode: "agent"
description: "Plan and execute a code refactoring task"
tools: ["context7"]
---

# Code Refactoring Guide

This guide helps plan and execute refactoring tasks in the CoachIQ codebase. Use this to organize structural changes, improve architecture, or implement best practices while maintaining functionality. When completed, the refactoring plan will be saved to `/docs/specs/refactor-<topic>.md` for review and implementation.

---

## 1. Refactoring Objective

### 1.1. Purpose

- What is the goal of this refactoring?
- What problems will it solve?
- What benefits will it provide?

### 1.2. Scope

- Which components are affected?
- What remains unchanged?
- What are the boundaries of this refactoring?
- Use `@context7` to analyze the files and modules that will be affected

---

## 2. Current State Analysis

### 2.1. Code Structure

- What is the current architecture?
- What are the key components and their relationships?
- What are the pain points or issues?
- Use `@context7` to analyze current patterns and implementation details

### 2.2. Code Quality Concerns

- What technical debt exists?
- What patterns need improvement?
- What inconsistencies should be addressed?

### 2.3. Test Coverage

- What is the current test coverage?
- Are there areas with insufficient testing?
- How will existing tests be affected?

---

## 3. Refactoring Plan

### 3.1. Architectural Changes

- What architectural patterns will be applied?
- How will components be reorganized?
- How will dependencies change?

### 3.2. Code Structure Changes

- What files will be created, modified, or deleted?
- How will modules be reorganized?
- What naming conventions will change?

### 3.3. Interface Changes

- Will public APIs change?
- How will backward compatibility be maintained?
- What deprecation strategy will be used?

### 3.4. Testing Strategy

- How will existing tests be updated?
- What new tests will be needed?
- How will refactoring success be verified?

---

## 4. Implementation Strategy

### 4.1. Phased Approach

- What are the logical phases for this refactoring?
- What are the dependencies between phases?
- What is the recommended sequence?
- Validate approach by using `@context7` to check similar patterns or precedents

### 4.2. Risk Mitigation

- What are the potential risks?
- How will they be mitigated?
- What fallback plans exist?

### 4.3. Validation Checkpoints

- How will we verify each phase?
- What metrics will indicate success?
- What testing will occur at each checkpoint?

---

## 5. Code Migration Guide

### 5.1. Old vs. New Patterns

- Compare old patterns with new patterns
- Provide examples of before and after code
- Explain the rationale for changes

```python
# BEFORE:
# Tightly coupled, global state
app_state = AppState()

async def get_device_status(device_id: str):
    return app_state.devices.get(device_id)

# AFTER:
# Dependency injection, service pattern
class DeviceService:
    def __init__(self, state_manager: StateManager):
        self.state_manager = state_manager

    async def get_device_status(self, device_id: str):
        return await self.state_manager.get_device(device_id)

# Usage in FastAPI
@router.get("/api/devices/{device_id}")
async def get_device(
    device_id: str,
    device_service: DeviceService = Depends(get_device_service)
):
    return await device_service.get_device_status(device_id)
```

### 5.2. Deprecation Path

- How will deprecated code be marked?
- What timeline will be used for removal?
- How will users be guided to new patterns?

---

## 6. Documentation Updates

### 6.1. Code Documentation

- What docstrings need to be updated?
- What examples need to be revised?
- What architectural documentation needs to be created?

### 6.2. User Documentation

- What user-facing documentation needs to be updated?
- How will API changes be communicated?
- What migration guides should be provided?

---

## 7. Execution Checklist

### 7.1. Preparation

- [ ] Analyze current code structure
- [ ] Create test cases for critical functionality
- [ ] Document current behavior
- [ ] Create backup branch

### 7.2. Implementation

- [ ] Create new structure
- [ ] Implement core changes
- [ ] Update tests
- [ ] Update documentation
- [ ] Create deprecation notices

### 7.3. Validation

- [ ] Run all tests
- [ ] Verify performance
- [ ] Validate backward compatibility
- [ ] Review code quality

### 7.4. Deployment

- [ ] Create release plan
- [ ] Update changelog
- [ ] Communicate changes to users
- [ ] Monitor for issues

---

## 8. References

### 8.1. Design Patterns

- List relevant design patterns
- Provide resources for further reading
- Reference similar refactorings

### 8.2. Best Practices

- List Python best practices being applied
- Reference style guides or coding standards
- Link to community resources

---

## Output

Once this refactoring plan is complete, save it to `/docs/specs/refactor-<topic>.md` where `<topic>` is a kebab-case name descriptive of the refactoring (e.g., `refactor-websocket-handlers.md` or `refactor-state-management.md`). This document will serve as the blueprint for implementation and can be shared with the development team.

---

This guide serves as a template for planning and executing code refactoring. Adjust sections as needed based on the specific requirements of your refactoring task.
