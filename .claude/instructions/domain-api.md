# Domain API v2 Development Instructions

This file provides specific guidance for developing with the Domain API v2 architecture in CoachIQ.

## Quick Reference

**🎯 Primary Goal**: Use Domain API v2 patterns for all new development
**📍 Location**: `/api/v2/{domain}` endpoints (e.g., `/api/v2/entities`)
**📋 Documentation**: See `docs/api/domain-api-v2.md` and `docs/development/domain-api-development.md`

## When to Use Domain API v2

- ✅ **All new features and components**
- ✅ **When implementing bulk operations**
- ✅ **When you need enhanced performance (caching, rate limiting)**
- ✅ **When building React components with optimistic updates**
- ✅ **When migrating from legacy endpoints**

## Backend Development Patterns

### 1. Creating a New Domain Router

```python
# backend/api/domains/new_domain.py
from fastapi import APIRouter, HTTPException, Query, status
from backend.schemas.new_domain import NewDomainSchema
from backend.core.domain_dependencies import NewDomainServiceDep

def create_new_domain_router() -> APIRouter:
    router = APIRouter(prefix="/new-domain", tags=["new-domain"])

    @router.get("/", response_model=List[NewDomainSchema])
    async def list_items(
        service: NewDomainServiceDep,
        page: int = Query(1, ge=1),
        page_size: int = Query(50, ge=1, le=100)
    ):
        return await service.list_items(page=page, page_size=page_size)

    return router
```

### 2. Schema with TypeScript Export

```python
# backend/schemas/new_domain.py
from pydantic import BaseModel, Field
from typing import List, Optional

class NewDomainSchema(BaseModel):
    item_id: str = Field(..., description="Unique identifier")
    name: str = Field(..., description="Human-readable name")

    @classmethod
    def to_zod_schema(cls) -> dict:
        """Export TypeScript-compatible schema"""
        return {
            "type": "object",
            "properties": {
                "item_id": {"type": "string"},
                "name": {"type": "string"}
            }
        }
```

### 3. Domain Service Implementation

```python
# backend/services/domains/new_domain_service.py
from backend.services.domains.domain_base import DomainServiceBase

class NewDomainService(DomainServiceBase):
    def __init__(self, app_state):
        super().__init__("new_domain", app_state)

    async def list_items(self, page: int = 1, page_size: int = 50):
        # Implement with caching, logging, monitoring
        pass
```

## Frontend Development Patterns

### 1. Domain API Client

```typescript
// frontend/src/api/domains/newDomain.ts
import { apiGet, apiPost } from '../client';

export async function fetchNewDomainItems(): Promise<NewDomainSchema[]> {
  return apiGet<NewDomainSchema[]>('/api/v2/new-domain');
}

export async function createNewDomainItem(data: CreateItemRequest): Promise<NewDomainSchema> {
  return apiPost<NewDomainSchema>('/api/v2/new-domain', data);
}
```

### 2. React Hooks with Optimistic Updates

```typescript
// frontend/src/hooks/domains/useNewDomain.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

export function useNewDomainItems() {
  return useQuery({
    queryKey: ['new-domain-v2', 'items'],
    queryFn: fetchNewDomainItems,
    staleTime: 30000,
  });
}

export function useCreateNewDomainItem() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createNewDomainItem,
    onMutate: async (newItem) => {
      // Optimistic update
      await queryClient.cancelQueries({ queryKey: ['new-domain-v2'] });
      const previousItems = queryClient.getQueryData(['new-domain-v2', 'items']);
      queryClient.setQueryData(['new-domain-v2', 'items'], old => [...old, newItem]);
      return { previousItems };
    },
    onError: (err, newItem, context) => {
      // Rollback on error
      if (context?.previousItems) {
        queryClient.setQueryData(['new-domain-v2', 'items'], context.previousItems);
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['new-domain-v2'] });
    },
  });
}
```

### 3. Bulk Operations Hook

```typescript
// For entities domain specifically
import { useBulkControlEntitiesV2, useEntitySelection } from '@/hooks/domains/useEntitiesV2';

export function MyComponent() {
  const { selectedEntityIds, executeBulkOperation } = useEntitySelection();

  const handleBulkTurnOff = async () => {
    await executeBulkOperation({
      command: { command: 'set', state: false }
    });
  };
}
```

## Key Patterns to Follow

### ✅ DO: Use Domain API v2 Patterns

```typescript
// ✅ Good: Domain API v2 with proper typing
import { useEntitiesV2, useControlEntityV2 } from '@/hooks/domains/useEntitiesV2';

const { data: entities } = useEntitiesV2({ device_type: 'light' });
const controlEntity = useControlEntityV2();
```

```python
# ✅ Good: Domain router with bulk operations
from backend.api.domains.entities import create_entities_router
router = create_entities_router()  # Includes bulk ops, caching, monitoring
```

### ❌ DON'T: Use Legacy Patterns for New Code

```typescript
// ❌ Bad: Using legacy API for new features
import { fetchEntities } from '@/api/endpoints';  // Legacy pattern
```

```python
# ❌ Bad: Direct entity endpoint instead of domain
@router.get("/entities")  # Should be in domain router
```

## Migration Patterns

### Progressive Migration

```typescript
// Use fallback pattern for gradual migration
import { withDomainAPIFallback } from '@/api/domains';

const entities = await withDomainAPIFallback(
  () => fetchEntitiesV2(params),      // Domain API v2
  () => fetchEntitiesLegacy(params),  // Legacy fallback
  { preferDomainAPI: true }
);
```

### Feature Flag Integration

```python
# Use feature flags to control domain API rollout
@router.get("/")
@require_feature("entities_domain_api")
async def list_entities():
    pass
```

## Performance Optimizations

### Caching

```python
# Domain services include automatic caching
class EntityDomainService(DomainServiceBase):
    @cached(ttl=300)  # 5 minute cache
    async def list_entities(self):
        pass
```

### Bulk Operations

```typescript
// Use bulk operations for multiple entity control
const bulkResult = await executeBulkOperation({
  entity_ids: ['light_001', 'light_002'],
  command: { command: 'set', state: false },
  ignore_errors: true
});
```

## Error Handling

### Structured Error Responses

```python
# Domain APIs return structured errors
{
  "detail": "Human-readable error message",
  "status_code": 400,
  "error_code": "VALIDATION_ERROR",
  "validation_errors": {"field": ["error message"]}
}
```

### Frontend Error Handling

```typescript
// Handle domain API errors properly
const mutation = useControlEntityV2();

mutation.mutate(
  { entityId: 'light_001', command: { command: 'toggle' } },
  {
    onError: (error) => {
      if (error.error_code === 'DEVICE_OFFLINE') {
        toast.error('Device is offline');
      } else {
        toast.error(`Failed: ${error.detail}`);
      }
    }
  }
);
```

## Documentation References

- **Complete API Docs**: `docs/api/domain-api-v2.md`
- **Development Guide**: `docs/development/domain-api-development.md`
- **Migration Strategy**: `docs/migration/legacy-to-domain-api-migration.md`
- **Integration Tests**: `tests/api/test_domain_entities_integration.py`

## Quick Commands

- `poetry run pytest tests/api/test_domain_entities_integration.py` - Run domain API tests
- `/domain-api-dev` - Use this Claude command for Domain API development help
- `/api-migration` - Use this Claude command for migration assistance

Remember: **Always prefer Domain API v2 patterns for new development!**
