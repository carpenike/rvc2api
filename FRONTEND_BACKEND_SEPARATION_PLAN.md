# Frontend-Backend Business Logic Separation Plan

## Executive Summary

This document outlines our plan to properly separate business logic between the frontend and backend according to industry best practices. Currently, we have identified several violations where business logic has crept into the frontend React/TypeScript application that should be handled by our FastAPI backend.

## Industry Best Practices Validation

Based on research from leading companies (Airbnb, Netflix) and industry standards:

### ✅ **What Should Stay in Frontend**
- **Presentation Logic**: UI rendering, form validation for UX, navigation
- **Basic Optimistic Updates**: Immediate UI feedback with rollback capability
- **UI State Management**: Component state, visual interactions
- **Simple Data Formatting**: Date formatting, currency display for presentation

### ❌ **What Must Move to Backend**
- **Business Rules**: Core domain logic, validation affecting data integrity
- **Data Aggregation**: Statistics, calculations, complex transformations
- **Security Logic**: Authentication, authorization, access control
- **State Transition Rules**: Entity state management with business constraints
- **Performance Calculations**: Health scoring, threshold determinations

## Current Violations Identified

### 🔴 **Critical Priority Issues**

#### 1. CAN Bus Statistics & Analytics (`can-sniffer.tsx:36-70`)
**Current State**: Frontend performs complex aggregations
```typescript
// ❌ Business logic in frontend
const stats = useMemo(() => {
  const byPGN = messages.reduce((acc, msg) => {
    acc[msg.pgn] = (acc[msg.pgn] || 0) + 1
    return acc
  }, {} as Record<string, number>)

  const errorMessages = messages.filter(msg => msg.error).length
  const lastMinute = messages.filter(msg =>
    Date.now() - new Date(msg.timestamp).getTime() < 60000
  ).length
  // ... more business logic
}, [messages])
```

**Target State**: Backend provides aggregated data
```typescript
// ✅ Simple data consumption
const { data: stats } = useQuery({
  queryKey: ['can-statistics'],
  queryFn: () => fetchCANStatistics()
})
```

**Backend Implementation**: `GET /api/can/statistics/aggregated`

#### 2. Data Transformation in API Layer (`endpoints.ts`)
**Current State**: Client-side data reshaping
```typescript
// ❌ Business logic transformation
const result: DTCCollection = {
  dtcs: rawResult,
  total_count: rawResult.length,
  active_count: rawResult.filter(dtc => !dtc.resolved).length,
  by_severity: rawResult.reduce((acc, dtc) => {
    acc[dtc.severity] = (acc[dtc.severity] || 0) + 1
    return acc
  }, {} as Record<string, number>)
}
```

**Target State**: Backend returns final format
```typescript
// ✅ Direct consumption
const { data: dtcs } = useQuery({
  queryKey: ['dtcs'],
  queryFn: () => fetchDTCs() // Returns DTCCollection directly
})
```

#### 3. Entity State Management Rules (`useEntities.ts:180-347`)
**Current State**: Complex business rules in optimistic updates
```typescript
// ❌ Business logic in frontend
if (command.command === 'brightness_up') {
  newState = light.state === 'off' ? 'on' : light.state;
  brightness = Math.min(light.brightness + 10, 100);
}
```

**Target State**: Simple optimistic updates following TanStack Query patterns
```typescript
// ✅ Simple optimistic update
useMutation({
  mutationFn: controlEntity,
  onMutate: async (newState) => {
    await queryClient.cancelQueries({ queryKey: ['entities', entityId] })
    const previousState = queryClient.getQueryData(['entities', entityId])
    // Simple state reflection, backend handles business rules
    queryClient.setQueryData(['entities', entityId], newState)
    return { previousState }
  },
  onError: (err, newState, context) => {
    queryClient.setQueryData(['entities', entityId], context.previousState)
  }
})
```

#### 4. Performance Health Scoring (`performance.tsx:38-77`)
**Current State**: Frontend threshold calculations
```typescript
// ❌ Business thresholds in frontend
const getScoreColor = (score: number) => {
  if (score >= 0.8) return 'text-green-600';
  if (score >= 0.6) return 'text-yellow-600';
  return 'text-red-600';
};
```

**Target State**: Backend provides categorized data
```typescript
// ✅ Simple display logic
const { data: health } = useQuery({
  queryKey: ['performance-health'],
  queryFn: () => fetchPerformanceHealth() // Returns { score, category, color }
})
```

### 🟡 **Medium Priority Issues**

#### 5. Diagnostic Business Rules (`diagnostics.tsx`)
- Severity badge mapping logic
- Health indicator calculations
- Status categorization rules

#### 6. Search/Filter Logic (`DTCManager.tsx`)
- Multi-field search implementations
- Custom sorting algorithms
- Filter combination logic

### 🟢 **Low Priority Issues**

#### 7. Protocol Display Rules
- Protocol color mappings
- Display formatting rules (could remain as simple UI logic)

## Implementation Plan

### Phase 1: Critical API Fixes (Week 1-2)

#### Backend Endpoints to Create/Enhance:
```bash
# CAN Statistics Service
GET  /api/can/statistics/aggregated
POST /api/can/statistics/reset

# Entity Control with Business Rules
POST /api/entities/{id}/control
GET  /api/entities/{id}  # Return final computed state

# Diagnostics with Aggregation
GET  /api/diagnostics/dtcs  # Return DTCCollection format

# Performance Health Service
GET  /api/performance/health  # Return categorized scores
GET  /api/performance/thresholds  # Return configurable thresholds
```

#### Frontend Refactoring:
- Remove aggregation logic from `can-sniffer.tsx`
- Eliminate data transformations in `endpoints.ts`
- Simplify entity optimistic updates following TanStack Query patterns
- Replace health scoring with backend consumption

### Phase 2: Business Logic Migration (Week 3-4)

#### Backend Services:
```python
# Entity State Management Service
class EntityStateService:
    def apply_brightness_rules(self, entity, command):
        """Handle brightness increment/decrement with state transitions"""

    def validate_state_transition(self, entity, new_state):
        """Validate state changes according to business rules"""

# Performance Health Service
class PerformanceHealthService:
    def calculate_health_score(self, metrics):
        """Apply configurable thresholds and return categorized health"""

    def get_performance_categories(self, scores):
        """Return color/variant mappings based on scores"""
```

#### Frontend Optimistic Updates:
Follow TanStack Query best practices:
- Simple state reflection, not business rule application
- Backend returns final state after applying rules
- Frontend reconciles with backend response

### Phase 3: Query Enhancement (Week 5-6)

#### Backend Query Parameters:
```python
# Enhanced API endpoints with server-side processing
GET /api/diagnostics/dtcs?search=engine&sort=severity&severity=critical
GET /api/entities?device_type=light&area=bedroom&search=courtesy
GET /api/can/messages?pgn=1FEDA&limit=100&since=timestamp
```

#### Frontend Simplification:
- Remove client-side search/filter/sort logic
- Use query parameters for data filtering
- Eliminate complex data transformations

## Architecture Principles

### Backend (FastAPI) Responsibilities:
- **All business rules and validation**
- **Data aggregation and calculations**
- **Security and access control**
- **State management with business constraints**
- **Performance optimizations**

### Frontend (React/TypeScript) Responsibilities:
- **UI rendering and interactions**
- **Basic optimistic updates (following TanStack Query patterns)**
- **Presentation formatting**
- **User experience enhancements**

## Implementation Guidelines

### TanStack Query Optimistic Update Pattern:
```typescript
// ✅ Correct pattern for entity control
const entityMutation = useMutation({
  mutationFn: ({ entityId, command }) => controlEntity(entityId, command),
  onMutate: async ({ entityId, command }) => {
    // Cancel outgoing refetches
    await queryClient.cancelQueries({ queryKey: ['entities', entityId] })

    // Snapshot previous value
    const previousEntity = queryClient.getQueryData(['entities', entityId])

    // Simple optimistic update (visual feedback only)
    queryClient.setQueryData(['entities', entityId], (old) => ({
      ...old,
      state: command.state, // Simple reflection, not business logic
      _optimistic: true
    }))

    return { previousEntity }
  },
  onError: (err, variables, context) => {
    // Rollback to previous state
    queryClient.setQueryData(
      ['entities', variables.entityId],
      context.previousEntity
    )
  },
  onSettled: (data, error, variables) => {
    // Backend response is source of truth
    queryClient.invalidateQueries({ queryKey: ['entities', variables.entityId] })
  }
})
```

### Backend Service Pattern:
```python
# ✅ Business logic in service layer
class EntityControlService:
    def control_entity(self, entity_id: str, command: ControlCommand) -> Entity:
        """Apply business rules and return final state"""
        entity = self.entity_manager.get_entity(entity_id)

        # Apply business rules
        if command.command == "brightness_up":
            new_brightness = min(entity.brightness + 10, 100)
            new_state = "on" if entity.state == "off" else entity.state

        # Validate state transition
        self.validate_state_transition(entity, new_state)

        # Send CAN command
        self.can_service.send_command(entity, command)

        # Return computed final state
        return entity.update_state({
            "state": new_state,
            "brightness": new_brightness,
            "timestamp": time.time()
        })
```

## Success Metrics

- **Performance**: Reduced frontend bundle size and CPU usage
- **Consistency**: Business rules enforced uniformly across all clients
- **Security**: No client-side bypass of business logic
- **Maintainability**: Single source of truth for business rules
- **Testing**: Business logic unit tested in isolation

## Progress Tracking

### Completed ✅
- [x] React key conflicts resolved in entity rendering
- [x] Entity deduplication moved to backend EntityManager
- [x] Unified entities API implemented

### In Progress 🔄
- [ ] CAN statistics aggregation migration
- [ ] Entity control business rules migration
- [ ] Performance health scoring migration
- [ ] Data transformation elimination

### Pending ⏳
- [ ] Diagnostic search/filter backend implementation
- [ ] Protocol-specific logic consolidation
- [ ] Performance optimization validation

## Next Steps

1. **Week 1**: Implement CAN statistics aggregation endpoint
2. **Week 1**: Refactor entity control to use simple optimistic updates
3. **Week 2**: Create performance health scoring service
4. **Week 2**: Eliminate API data transformations
5. **Week 3**: Enhance backend with query parameters
6. **Week 4**: Final validation and performance testing

## References

- [TanStack Query Optimistic Updates](https://tanstack.com/query/latest/docs/framework/react/guides/optimistic-updates)
- [FastAPI Best Architecture Patterns](https://github.com/fastapi-practices/fastapi_best_architecture)
- [Frontend/Backend Separation Best Practices](https://mobidev.biz/blog/web-application-architecture-types)

---

**Last Updated**: December 2024
**Status**: Planning Phase
**Next Review**: Weekly during implementation
