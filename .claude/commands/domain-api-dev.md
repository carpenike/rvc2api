# Domain API Development Command

**Command**: `/domain-api-dev`
**Purpose**: Develop Domain API v2 endpoints with bulk operations, caching, and monitoring

## Usage

When the user mentions domain API development, API endpoints, bulk operations, or entity management, use this workflow:

## Workflow Steps

### 1. Understand Requirements
- Identify the domain (entities, diagnostics, analytics, etc.)
- Determine if it's a new domain or extending existing
- Check if bulk operations are needed
- Assess performance requirements (caching, rate limiting)

### 2. Backend Implementation
- **Schema First**: Create Pydantic schemas with `to_zod_schema()` method
- **Domain Service**: Implement business logic extending `DomainServiceBase`
- **Domain Router**: Create router with standard patterns (list, get, create, bulk operations)
- **Dependencies**: Add to `backend/core/domain_dependencies.py`
- **Integration**: Register in `backend/api/router_config.py`

### 3. Frontend Implementation
- **API Client**: Create domain-specific API functions in `frontend/src/api/domains/`
- **Types**: Generate TypeScript types in `frontend/src/api/types/domains.ts`
- **React Hooks**: Implement hooks with optimistic updates in `frontend/src/hooks/domains/`
- **Components**: Create UI components using shadcn/ui for bulk operations

### 4. Testing & Documentation
- **Integration Tests**: Create comprehensive tests in `tests/api/test_domain_*_integration.py`
- **Frontend Tests**: Test hooks and components in `frontend/src/hooks/domains/__tests__/`
- **API Documentation**: Update OpenAPI documentation with examples
- **User Guide**: Add usage examples and migration notes

### 5. Performance & Monitoring
- **Caching**: Implement intelligent caching with TTL
- **Rate Limiting**: Configure appropriate rate limits by operation type
- **Monitoring**: Add Prometheus metrics and structured logging
- **Health Checks**: Implement domain-specific health endpoints

## File Templates

### Backend Schema Template
```python
# backend/schemas/{domain}.py
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class {Domain}Schema(BaseModel):
    """Schema for {domain} items."""

    id: str = Field(..., description="Unique identifier")
    name: str = Field(..., description="Human-readable name")
    created_at: datetime = Field(..., description="Creation timestamp")

    @classmethod
    def to_zod_schema(cls) -> dict:
        """Export TypeScript-compatible schema."""
        return {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "name": {"type": "string"},
                "created_at": {"type": "string", "format": "date-time"}
            },
            "required": ["id", "name", "created_at"]
        }
```

### Frontend Hook Template
```typescript
// frontend/src/hooks/domains/use{Domain}V2.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetch{Domain}ItemsV2, control{Domain}ItemV2 } from '../../api/domains/{domain}';

export const {domain}V2QueryKeys = {
  all: ['{domain}-v2'] as const,
  items: () => [...{domain}V2QueryKeys.all, 'items'] as const,
  item: (id: string) => [...{domain}V2QueryKeys.items(), id] as const,
};

export function use{Domain}ItemsV2(params?: {Domain}QueryParams) {
  return useQuery({
    queryKey: {domain}V2QueryKeys.items(),
    queryFn: () => fetch{Domain}ItemsV2(params),
    staleTime: 30000,
  });
}

export function useControl{Domain}ItemV2() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ itemId, command }: { itemId: string; command: any }) =>
      control{Domain}ItemV2(itemId, command),
    onMutate: async ({ itemId, command }) => {
      // Optimistic update implementation
    },
    onError: (err, variables, context) => {
      // Rollback optimistic update
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: {domain}V2QueryKeys.all });
    },
  });
}
```

## Checklist

### Backend Implementation
- [ ] Pydantic schema with `to_zod_schema()` method
- [ ] Domain service extending `DomainServiceBase`
- [ ] Domain router with standard endpoints
- [ ] Bulk operations if applicable
- [ ] Dependency injection setup
- [ ] Router registration
- [ ] Feature flag integration
- [ ] Caching and rate limiting
- [ ] Monitoring and logging
- [ ] Health check endpoint

### Frontend Implementation
- [ ] Domain API client functions
- [ ] TypeScript type definitions
- [ ] React hooks with optimistic updates
- [ ] Bulk operations hook if applicable
- [ ] Error handling
- [ ] shadcn/ui components
- [ ] Progressive migration support

### Testing & Quality
- [ ] Backend integration tests
- [ ] Frontend hook tests
- [ ] Component tests
- [ ] Error handling tests
- [ ] Performance tests
- [ ] Type checking passes
- [ ] Linting passes

### Documentation
- [ ] OpenAPI documentation
- [ ] Usage examples
- [ ] Migration guide if replacing legacy
- [ ] Performance characteristics
- [ ] Error codes and handling

## Key Principles

1. **Domain-Driven Design**: Organize by business domain, not technical concerns
2. **Type Safety**: End-to-end TypeScript with runtime validation
3. **Performance First**: Built-in caching, rate limiting, and monitoring
4. **Optimistic Updates**: Immediate UI feedback with proper rollback
5. **Progressive Migration**: Support gradual migration from legacy APIs
6. **Comprehensive Testing**: Unit, integration, and performance tests
7. **Developer Experience**: Clear APIs, good error messages, helpful documentation

## Common Patterns

- **List Endpoints**: Always support pagination, filtering, and sorting
- **Bulk Operations**: Implement for any operations that might be done on multiple items
- **Error Handling**: Use structured error responses with proper HTTP status codes
- **Caching**: Cache read operations with appropriate TTL
- **Monitoring**: Track request count, response time, error rate, cache hit rate
- **Authentication**: Support JWT, API Key, and Legacy authentication methods

Remember: Follow the examples in `backend/api/domains/entities.py` and `frontend/src/hooks/domains/useEntitiesV2.ts` as reference implementations!
