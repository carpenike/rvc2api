# API Refactoring Implementation Plan

## Domain-Driven Architecture with Service Integration

> **Generated:** 2025-01-09
> **Status:** Ready for Implementation
> **Target:** Refactor monolithic API layer into domain-driven architecture

---

## Executive Summary

This plan addresses the architectural limitations identified in Gemini's analysis of the entities.ts and types.ts files by implementing a phased refactoring approach that:

1. **Maintains business logic in the backend** using existing service management patterns
2. **Integrates with CoachIQ's service architecture** (Config Manager, Auth Manager, Feature Manager)
3. **Implements domain-driven organization** for both frontend and backend
4. **Adds runtime type safety** with Zod validation
5. **Improves security** with proper token management

---

## Current Architecture Assessment

### Critical Issues Identified

- **Monolithic API files**: `endpoints.ts` (1000+ lines), `types.ts` (1200+ lines)
- **Fragile optimistic updates**: 2-second timeout rollback strategy
- **N+1 API calls**: Light presets creating multiple individual requests
- **Client-side filtering**: Performance bottleneck with large datasets
- **Type safety gaps**: No runtime validation of API responses
- **Security vulnerabilities**: localStorage token storage

### Existing Service Architecture Strengths

- **Feature Management System**: YAML-driven with dependency resolution
- **Configuration Management**: Pydantic settings with environment variables
- **Authentication System**: JWT with MFA and magic links
- **Dependency Injection**: FastAPI state-based service injection
- **Domain Organization**: Integration-based structure in backend

---

## Implementation Strategy

### Business Logic Placement

**CRITICAL PRINCIPLE**: All business logic remains in the backend services, frontend handles only presentation and user interaction.

- **Backend Services**: Entity operations, data validation, business rules
- **Frontend API Layer**: Type-safe client with optimistic updates
- **Service Integration**: Leverage existing Config, Auth, and Feature managers

---

## Phase 1: Foundation & Backend Enhancement (Weeks 1-2)

### 1.1 Backend API Domain Organization

**Goal**: Create domain-specific backend services that integrate with existing service management platform.

#### Task 1.1.1: Create Domain-Specific Service Classes

```python
# backend/services/entity_domain_service.py
class EntityDomainService:
    """Domain-specific service for entity operations"""

    def __init__(
        self,
        config_manager: ConfigManager,
        auth_manager: AuthManager,
        feature_manager: FeatureManager,
        entity_service: EntityService
    ):
        self.config = config_manager
        self.auth = auth_manager
        self.features = feature_manager
        self.entities = entity_service

    async def bulk_control_entities(
        self,
        entity_ids: List[str],
        command: ControlCommand,
        user_context: AuthContext
    ) -> BulkOperationResult:
        """Business logic for bulk entity control"""
        # Validate permissions via auth_manager
        # Check feature flags via feature_manager
        # Execute operations via entity_service
        # Return structured results
```

#### Task 1.1.2: Create Domain Router Registration System

```python
# backend/api/domains/__init__.py
from .entities import register_entities_router
from .diagnostics import register_diagnostics_router
from .analytics import register_analytics_router

DOMAIN_ROUTERS = {
    "entities": register_entities_router,
    "diagnostics": register_diagnostics_router,
    "analytics": register_analytics_router,
}

def register_domain_routers(app: FastAPI, feature_manager: FeatureManager):
    """Register domain routers based on enabled features"""
    for domain, register_func in DOMAIN_ROUTERS.items():
        if feature_manager.is_feature_enabled(f"{domain}_api"):
            router = register_func(app.state)
            app.include_router(router, prefix=f"/api/{domain}")
```

#### Task 1.1.3: Enhanced Dependency Injection

```python
# backend/core/domain_dependencies.py
def get_entity_domain_service(request: Request) -> EntityDomainService:
    """Get entity domain service with all dependencies"""
    return EntityDomainService(
        config_manager=get_config_manager(request),
        auth_manager=get_auth_manager(request),
        feature_manager=get_feature_manager(request),
        entity_service=get_entity_service(request)
    )
```

### 1.2 Feature Flag Integration

#### Task 1.2.1: Add API Domain Features

```yaml
# backend/services/feature_flags.yaml (additions)
entities_api:
  enabled: true
  core: true
  depends_on: [authentication, can_interface]
  description: "Domain-specific entities API with bulk operations"

diagnostics_api:
  enabled: true
  core: false
  depends_on: [entities_api, j1939_integration]
  description: "Diagnostics domain API with DTC management"

analytics_api:
  enabled: false
  core: false
  depends_on: [entities_api, performance_analytics]
  description: "Analytics domain API with telemetry data"
```

#### Task 1.2.2: Configuration Integration

```python
# backend/core/config.py (additions)
class APIDomainSettings(BaseSettings):
    enable_bulk_operations: bool = True
    enable_optimistic_updates: bool = True
    max_bulk_operation_size: int = 100
    validation_mode: Literal["strict", "permissive"] = "strict"

class Settings(BaseSettings):
    # ... existing settings ...
    api_domains: APIDomainSettings = Field(default_factory=APIDomainSettings)
```

### 1.3 Runtime Type Validation with Zod

#### Task 1.3.1: Backend Schema Definitions

```python
# backend/schemas/entities.py
from pydantic import BaseModel
from typing import Dict, Any

class EntitySchema(BaseModel):
    """Server-side entity schema with validation"""
    entity_id: str
    name: str
    device_type: str
    protocol: str
    state: Dict[str, Any]

    @classmethod
    def to_zod_schema(cls) -> Dict[str, Any]:
        """Export Zod-compatible schema"""
        return {
            "type": "object",
            "properties": {
                "entity_id": {"type": "string"},
                "name": {"type": "string"},
                "device_type": {"type": "string"},
                "protocol": {"type": "string"},
                "state": {"type": "object"}
            },
            "required": ["entity_id", "name", "device_type", "protocol", "state"]
        }
```

#### Task 1.3.2: Schema Export Endpoint

```python
# backend/api/routers/schemas.py
@router.get("/schemas/entities", dependencies=[Depends(get_auth_manager)])
async def get_entity_schemas() -> Dict[str, Any]:
    """Export Zod-compatible schemas for frontend validation"""
    return {
        "Entity": EntitySchema.to_zod_schema(),
        "ControlCommand": ControlCommandSchema.to_zod_schema(),
        # ... other schemas
    }
```

### 1.4 Enhanced Security Implementation

#### Task 1.4.1: Secure Token Management

```python
# backend/services/token_service.py
class TokenService:
    """Secure token management service"""

    def __init__(self, auth_manager: AuthManager, config: Settings):
        self.auth = auth_manager
        self.config = config

    async def issue_access_token(self, refresh_token: str) -> TokenResponse:
        """Issue short-lived access token from httpOnly refresh token"""
        # Validate refresh token
        # Issue access token (15 minutes)
        # Return for memory storage

    async def refresh_token_cycle(self, old_refresh: str) -> TokenResponse:
        """Rotate refresh tokens for security"""
        # Invalidate old refresh token
        # Issue new refresh token (httpOnly cookie)
        # Issue new access token (memory)
```

---

## Phase 2: Frontend Domain Organization (Weeks 3-4)

### 2.1 Domain-Driven Frontend Structure

#### Task 2.1.1: Create Domain-Specific API Modules

```typescript
// frontend/src/api/domains/entities/endpoints.ts
import { apiClient } from "../../client";
import { EntitySchema } from "./schemas";
import { z } from "zod";

export const entitiesApi = {
  async getAll(params?: EntitiesQueryParams): Promise<EntityCollection> {
    const response = await apiClient.get<unknown>("/api/entities", { params });
    return EntityCollectionSchema.parse(response);
  },

  async bulkControl(request: BulkControlRequest): Promise<BulkOperationResult> {
    const response = await apiClient.post<unknown>(
      "/api/entities/bulk-control",
      request
    );
    return BulkOperationResultSchema.parse(response);
  },

  async getById(id: string): Promise<Entity> {
    const response = await apiClient.get<unknown>(`/api/entities/${id}`);
    return EntitySchema.parse(response);
  },
};
```

#### Task 2.1.2: Zod Schema Definitions

```typescript
// frontend/src/api/domains/entities/schemas.ts
import { z } from "zod";

export const EntitySchema = z.object({
  entity_id: z.string(),
  name: z.string(),
  device_type: z.string(),
  protocol: z.string(),
  state: z.record(z.unknown()),
  last_updated: z.string().datetime(),
});

export const ControlCommandSchema = z.object({
  command: z.enum(["set", "toggle", "brightness_up", "brightness_down"]),
  state: z.boolean().optional(),
  brightness: z.number().min(0).max(100).optional(),
});

export const BulkControlRequestSchema = z.object({
  entity_ids: z.array(z.string()),
  command: ControlCommandSchema,
  ignore_errors: z.boolean().default(false),
});

export type Entity = z.infer<typeof EntitySchema>;
export type ControlCommand = z.infer<typeof ControlCommandSchema>;
export type BulkControlRequest = z.infer<typeof BulkControlRequestSchema>;
```

### 2.2 Improved State Management Patterns

#### Task 2.2.1: Enhanced Optimistic Updates

```typescript
// frontend/src/hooks/entities/useOptimisticEntityControl.ts
export function useOptimisticEntityControl() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      entityId,
      command,
    }: {
      entityId: string;
      command: ControlCommand;
    }) => {
      const response = await entitiesApi.controlEntity(entityId, command);
      return ControlResultSchema.parse(response);
    },

    onMutate: async ({ entityId, command }) => {
      // Cancel outgoing queries
      await queryClient.cancelQueries({ queryKey: ["entities", entityId] });

      // Snapshot previous value
      const previousEntity = queryClient.getQueryData<Entity>([
        "entities",
        entityId,
      ]);

      // Optimistically update
      queryClient.setQueryData<Entity>(["entities", entityId], (old) => {
        if (!old) return undefined;
        return {
          ...old,
          state: predictOptimisticState(old.state, command),
          _optimistic: true,
        };
      });

      return { previousEntity };
    },

    onError: (err, variables, context) => {
      // Revert on error
      if (context?.previousEntity) {
        queryClient.setQueryData(
          ["entities", variables.entityId],
          context.previousEntity
        );
      }
      toast.error(`Failed to control ${variables.entityId}`);
    },

    onSettled: (data, error, variables) => {
      // Always refetch to ensure consistency
      queryClient.invalidateQueries({
        queryKey: ["entities", variables.entityId],
      });
    },
  });
}
```

#### Task 2.2.2: Bulk Operations Hook

```typescript
// frontend/src/hooks/entities/useBulkEntityControl.ts
export function useBulkEntityControl() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (request: BulkControlRequest) => {
      const response = await entitiesApi.bulkControl(request);
      return BulkOperationResultSchema.parse(response);
    },

    onMutate: async ({ entity_ids, command }) => {
      // Optimistically update all entities
      const previousStates = new Map();

      for (const entityId of entity_ids) {
        await queryClient.cancelQueries({ queryKey: ["entities", entityId] });
        const previous = queryClient.getQueryData<Entity>([
          "entities",
          entityId,
        ]);
        if (previous) {
          previousStates.set(entityId, previous);
          queryClient.setQueryData<Entity>(["entities", entityId], {
            ...previous,
            state: predictOptimisticState(previous.state, command),
            _optimistic: true,
          });
        }
      }

      return { previousStates };
    },

    onSuccess: (result) => {
      // Handle partial failures
      if (result.failed.length > 0) {
        toast.warning(`${result.failed.length} operations failed`);
      }
      if (result.succeeded.length > 0) {
        toast.success(`${result.succeeded.length} operations completed`);
      }
    },

    onError: (err, variables, context) => {
      // Revert all optimistic updates
      context?.previousStates.forEach((entity, entityId) => {
        queryClient.setQueryData(["entities", entityId], entity);
      });
      toast.error("Bulk operation failed");
    },

    onSettled: (data, error, variables) => {
      // Invalidate all affected entities
      variables.entity_ids.forEach((entityId) => {
        queryClient.invalidateQueries({ queryKey: ["entities", entityId] });
      });
      queryClient.invalidateQueries({ queryKey: ["entities"] });
    },
  });
}
```

### 2.3 API Client Refactoring

#### Task 2.3.1: Enhanced API Client with Validation

```typescript
// frontend/src/api/client.ts
import { z } from "zod";

class APIClient {
  private baseUrl: string;
  private accessToken: string | null = null;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  async request<T>(
    url: string,
    options: RequestInit = {},
    schema?: z.ZodType<T>
  ): Promise<T> {
    const response = await fetch(`${this.baseUrl}${url}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(this.accessToken && {
          Authorization: `Bearer ${this.accessToken}`,
        }),
        ...options.headers,
      },
    });

    if (!response.ok) {
      throw new APIError(response.status, await response.text());
    }

    const data = await response.json();

    if (schema) {
      const result = schema.safeParse(data);
      if (!result.success) {
        console.error("API validation failed:", result.error);
        throw new ValidationError(
          "API response validation failed",
          result.error
        );
      }
      return result.data;
    }

    return data;
  }

  setAccessToken(token: string | null) {
    this.accessToken = token;
  }
}

export const apiClient = new APIClient(import.meta.env.VITE_API_BASE_URL);
```

---

## Phase 3: Performance & Security Enhancements (Weeks 5-6)

### 3.1 WebSocket Message Batching

#### Task 3.1.1: Backend WebSocket Optimization

```python
# backend/websocket/batched_handler.py
import asyncio
from collections import deque
from typing import Dict, List

class BatchedWebSocketHandler:
    """Batch WebSocket messages for performance"""

    def __init__(self, batch_size: int = 50, batch_timeout: float = 0.1):
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.message_queue: deque = deque()
        self.batch_task: Optional[asyncio.Task] = None

    async def queue_message(self, message: WebSocketMessage):
        """Queue message for batched delivery"""
        self.message_queue.append(message)

        if len(self.message_queue) >= self.batch_size:
            await self._flush_batch()
        elif not self.batch_task:
            self.batch_task = asyncio.create_task(self._schedule_batch())

    async def _schedule_batch(self):
        """Schedule batch delivery after timeout"""
        await asyncio.sleep(self.batch_timeout)
        await self._flush_batch()
        self.batch_task = None

    async def _flush_batch(self):
        """Deliver batched messages"""
        if not self.message_queue:
            return

        batch = list(self.message_queue)
        self.message_queue.clear()

        # Group by connection and send
        grouped_messages = self._group_by_connection(batch)
        for connection, messages in grouped_messages.items():
            await connection.send_json({
                "type": "batch",
                "messages": messages
            })
```

#### Task 3.1.2: Frontend Batch Processing

```typescript
// frontend/src/contexts/websocket-provider.tsx
class BatchedWebSocketClient {
  private messageQueue: WebSocketMessage[] = [];
  private animationFrameId: number | null = null;

  private handleMessage = (event: MessageEvent) => {
    const message = JSON.parse(event.data);

    if (message.type === "batch") {
      // Queue all messages from batch
      this.messageQueue.push(...message.messages);
    } else {
      this.messageQueue.push(message);
    }

    // Process queue on next animation frame
    if (!this.animationFrameId) {
      this.animationFrameId = requestAnimationFrame(this.processBatch);
    }
  };

  private processBatch = () => {
    if (this.messageQueue.length === 0) return;

    const batch = this.messageQueue.slice();
    this.messageQueue = [];
    this.animationFrameId = null;

    // Process batch with React Query cache updates
    this.queryClient.batch(() => {
      batch.forEach((message) => this.processMessage(message));
    });
  };
}
```

### 3.2 Secure Token Management

#### Task 3.2.1: HttpOnly Cookie Implementation

```python
# backend/middleware/secure_auth.py
class SecureAuthMiddleware:
    """Secure authentication with httpOnly cookies"""

    async def __call__(self, request: Request, call_next):
        # Check for access token in Authorization header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            access_token = auth_header[7:]
            # Validate access token

        # Check for refresh token in httpOnly cookie
        refresh_token = request.cookies.get("refresh_token")
        if refresh_token and not access_token:
            # Issue new access token
            token_service = get_token_service(request)
            try:
                new_tokens = await token_service.refresh_access_token(refresh_token)
                # Set new refresh token cookie
                response = await call_next(request)
                response.set_cookie(
                    "refresh_token",
                    new_tokens.refresh_token,
                    httponly=True,
                    secure=True,
                    samesite="strict",
                    max_age=30 * 24 * 3600  # 30 days
                )
                # Return access token in response header
                response.headers["X-Access-Token"] = new_tokens.access_token
                return response
            except InvalidTokenError:
                # Clear invalid refresh token
                response = await call_next(request)
                response.delete_cookie("refresh_token")
                return response

        return await call_next(request)
```

#### Task 3.2.2: Frontend Token Management

```typescript
// frontend/src/lib/auth/token-manager.ts
class SecureTokenManager {
  private accessToken: string | null = null;
  private refreshPromise: Promise<string> | null = null;

  setAccessToken(token: string | null) {
    this.accessToken = token;
    if (token) {
      // Set automatic refresh before expiration
      const payload = JSON.parse(atob(token.split(".")[1]));
      const expiresIn = payload.exp * 1000 - Date.now() - 60000; // 1 minute buffer
      setTimeout(() => this.refreshAccessToken(), expiresIn);
    }
  }

  getAccessToken(): string | null {
    return this.accessToken;
  }

  async refreshAccessToken(): Promise<string> {
    if (this.refreshPromise) {
      return this.refreshPromise;
    }

    this.refreshPromise = this.performRefresh();
    try {
      const token = await this.refreshPromise;
      this.setAccessToken(token);
      return token;
    } finally {
      this.refreshPromise = null;
    }
  }

  private async performRefresh(): Promise<string> {
    const response = await fetch("/api/auth/refresh", {
      method: "POST",
      credentials: "include", // Include httpOnly cookie
    });

    if (!response.ok) {
      throw new Error("Token refresh failed");
    }

    const accessToken = response.headers.get("X-Access-Token");
    if (!accessToken) {
      throw new Error("No access token in refresh response");
    }

    return accessToken;
  }
}

export const tokenManager = new SecureTokenManager();
```

### 3.3 List Virtualization

#### Task 3.3.1: Virtualized Entity List Component

```typescript
// frontend/src/components/virtualized-entity-list.tsx
import { useVirtualizer } from "@tanstack/react-virtual";
import { useRef } from "react";

interface VirtualizedEntityListProps {
  entities: Entity[];
  onEntitySelect: (entity: Entity) => void;
  selectedEntities: Set<string>;
}

export function VirtualizedEntityList({
  entities,
  onEntitySelect,
  selectedEntities,
}: VirtualizedEntityListProps) {
  const parentRef = useRef<HTMLDivElement>(null);

  const rowVirtualizer = useVirtualizer({
    count: entities.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 80, // Estimated row height
    overscan: 10, // Render extra items outside viewport
  });

  return (
    <div ref={parentRef} className="h-[400px] overflow-auto">
      <div
        style={{
          height: `${rowVirtualizer.getTotalSize()}px`,
          width: "100%",
          position: "relative",
        }}
      >
        {rowVirtualizer.getVirtualItems().map((virtualItem) => {
          const entity = entities[virtualItem.index];
          return (
            <div
              key={virtualItem.key}
              style={{
                position: "absolute",
                top: 0,
                left: 0,
                width: "100%",
                height: `${virtualItem.size}px`,
                transform: `translateY(${virtualItem.start}px)`,
              }}
            >
              <EntityCard
                entity={entity}
                isSelected={selectedEntities.has(entity.entity_id)}
                onSelect={() => onEntitySelect(entity)}
              />
            </div>
          );
        })}
      </div>
    </div>
  );
}
```

---

## Phase 4: Testing & Documentation (Weeks 7-8)

### 4.1 Comprehensive Testing Strategy

#### Task 4.1.1: Backend Service Tests

```python
# tests/services/test_entity_domain_service.py
import pytest
from unittest.mock import Mock, AsyncMock
from backend.services.entity_domain_service import EntityDomainService

class TestEntityDomainService:
    @pytest.fixture
    def service(self):
        return EntityDomainService(
            config_manager=Mock(),
            auth_manager=Mock(),
            feature_manager=Mock(),
            entity_service=Mock()
        )

    @pytest.mark.asyncio
    async def test_bulk_control_entities_success(self, service):
        """Test successful bulk entity control"""
        # Setup mocks
        service.auth.verify_permissions = AsyncMock(return_value=True)
        service.features.is_feature_enabled = Mock(return_value=True)
        service.entities.control_entity = AsyncMock(return_value={"success": True})

        # Execute
        result = await service.bulk_control_entities(
            entity_ids=["light1", "light2"],
            command={"command": "set", "state": True},
            user_context=Mock()
        )

        # Verify
        assert result.succeeded == ["light1", "light2"]
        assert result.failed == []
        assert service.entities.control_entity.call_count == 2
```

#### Task 4.1.2: Frontend Hook Tests

```typescript
// frontend/src/hooks/__tests__/useOptimisticEntityControl.test.tsx
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useOptimisticEntityControl } from "../useOptimisticEntityControl";

describe("useOptimisticEntityControl", () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });
  });

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );

  it("should optimistically update entity state", async () => {
    // Mock entity data
    const entity = { entity_id: "light1", state: { on: false } };
    queryClient.setQueryData(["entities", "light1"], entity);

    const { result } = renderHook(() => useOptimisticEntityControl(), {
      wrapper,
    });

    // Execute mutation
    result.current.mutate({
      entityId: "light1",
      command: { command: "set", state: true },
    });

    // Verify optimistic update
    const optimisticEntity = queryClient.getQueryData(["entities", "light1"]);
    expect(optimisticEntity).toMatchObject({
      entity_id: "light1",
      state: { on: true },
      _optimistic: true,
    });
  });
});
```

### 4.2 API Documentation Enhancement

#### Task 4.2.1: OpenAPI Schema Generation

```python
# backend/api/docs/schema_generator.py
from fastapi.openapi.utils import get_openapi
from backend.schemas import EntitySchema, ControlCommandSchema

def generate_enhanced_openapi_schema(app: FastAPI) -> dict:
    """Generate comprehensive OpenAPI schema with domain organization"""

    schema = get_openapi(
        title="CoachIQ API",
        version="2.0.0",
        description="Domain-driven RV-C network management API",
        routes=app.routes,
    )

    # Add domain-specific tags
    schema["tags"] = [
        {
            "name": "entities",
            "description": "Entity management and control operations"
        },
        {
            "name": "diagnostics",
            "description": "Diagnostic trouble codes and system health"
        },
        {
            "name": "analytics",
            "description": "Performance analytics and telemetry"
        }
    ]

    # Add schema examples
    schema["components"]["schemas"]["Entity"]["example"] = {
        "entity_id": "light_living_room",
        "name": "Living Room Light",
        "device_type": "light",
        "protocol": "rvc",
        "state": {"on": True, "brightness": 75}
    }

    return schema
```

#### Task 4.2.2: Frontend API Documentation

```typescript
// frontend/src/api/docs/api-reference.ts
/**
 * CoachIQ Frontend API Reference
 *
 * Domain-organized API client with type safety and validation
 */

export const API_DOMAINS = {
  entities: {
    description: "Entity management and control",
    endpoints: {
      getAll: {
        method: "GET",
        path: "/api/entities",
        description: "Retrieve all entities with filtering",
        params: "EntitiesQueryParams",
        returns: "EntityCollection",
      },
      bulkControl: {
        method: "POST",
        path: "/api/entities/bulk-control",
        description: "Control multiple entities in a single operation",
        body: "BulkControlRequest",
        returns: "BulkOperationResult",
      },
    },
  },
  // ... other domains
} as const;
```

---

## Phase 5: Migration & Rollout (Weeks 9-10)

### 5.1 Incremental Migration Strategy

#### Task 5.1.1: Feature Flag Controlled Rollout

```typescript
// frontend/src/lib/feature-flags.ts
export const useFeatureFlags = () => {
  return {
    useDomainApi:
      process.env.NODE_ENV === "development" ||
      localStorage.getItem("feature_domain_api") === "true",
    useOptimizedWebSocket: true,
    useVirtualization: true,
  };
};

// Gradual rollout component
export function ApiProvider({ children }: { children: React.ReactNode }) {
  const { useDomainApi } = useFeatureFlags();

  const apiClient = useMemo(() => {
    return useDomainApi ? new DomainApiClient() : new LegacyApiClient();
  }, [useDomainApi]);

  return (
    <ApiContext.Provider value={apiClient}>{children}</ApiContext.Provider>
  );
}
```

#### Task 5.1.2: Backward Compatibility Layer

```python
# backend/api/legacy_compatibility.py
class LegacyAPICompatibility:
    """Maintain backward compatibility during migration"""

    def __init__(self, entity_domain_service: EntityDomainService):
        self.domain_service = entity_domain_service

    async def legacy_control_entity(self, entity_id: str, **kwargs):
        """Legacy endpoint that maps to new domain service"""

        # Convert legacy parameters to new command format
        command = self._convert_legacy_command(kwargs)

        # Call new domain service
        result = await self.domain_service.control_single_entity(
            entity_id=entity_id,
            command=command,
            user_context=get_current_user_context()
        )

        # Convert result to legacy format
        return self._convert_to_legacy_response(result)
```

### 5.2 Performance Monitoring

#### Task 5.2.1: API Performance Metrics

```python
# backend/middleware/performance_monitoring.py
import time
from typing import Dict
from backend.core.metrics import metrics_collector

class APIPerformanceMiddleware:
    """Monitor API performance and identify bottlenecks"""

    async def __call__(self, request: Request, call_next):
        start_time = time.time()

        # Extract domain from path
        domain = self._extract_domain(request.url.path)

        response = await call_next(request)

        duration = time.time() - start_time

        # Record metrics
        metrics_collector.record_api_call(
            domain=domain,
            endpoint=request.url.path,
            method=request.method,
            status_code=response.status_code,
            duration=duration
        )

        # Add performance headers
        response.headers["X-Response-Time"] = str(duration)

        return response
```

#### Task 5.2.2: Frontend Performance Dashboard

```typescript
// frontend/src/components/admin/performance-dashboard.tsx
export function PerformanceDashboard() {
  const { data: metrics } = useQuery({
    queryKey: ["performance-metrics"],
    queryFn: () => analyticsApi.getPerformanceMetrics(),
    refetchInterval: 30000, // 30 seconds
  });

  return (
    <div className="grid grid-cols-2 gap-4">
      <Card>
        <CardHeader>
          <CardTitle>API Response Times</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={metrics?.apiResponseTimes}>
              <XAxis dataKey="time" />
              <YAxis />
              <CartesianGrid strokeDasharray="3 3" />
              <Line type="monotone" dataKey="entities" stroke="#8884d8" />
              <Line type="monotone" dataKey="diagnostics" stroke="#82ca9d" />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>WebSocket Message Rate</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            {metrics?.websocketMessageRate}/sec
          </div>
          <p className="text-muted-foreground">
            Batching efficiency: {metrics?.batchingEfficiency}%
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
```

---

## Implementation Tracking

### Phase Completion Checklist

#### Phase 1: Foundation & Backend Enhancement

- [ ] Domain-specific service classes created
- [ ] Router registration system implemented
- [ ] Enhanced dependency injection configured
- [ ] Feature flags integrated
- [ ] Configuration settings updated
- [ ] Runtime type validation added
- [ ] Schema export endpoints created
- [ ] Secure token management implemented

#### Phase 2: Frontend Domain Organization

- [ ] Domain-specific API modules created
- [ ] Zod schema definitions implemented
- [ ] Enhanced optimistic updates configured
- [ ] Bulk operations hook created
- [ ] API client refactored with validation
- [ ] Type safety improvements verified

#### Phase 3: Performance & Security Enhancements

- [ ] WebSocket message batching implemented
- [ ] HttpOnly cookie authentication added
- [ ] List virtualization integrated
- [ ] Performance monitoring configured
- [ ] Security audits completed

#### Phase 4: Testing & Documentation

- [ ] Backend service tests written
- [ ] Frontend hook tests implemented
- [ ] OpenAPI schema enhanced
- [ ] API reference documentation created
- [ ] Integration tests passing

#### Phase 5: Migration & Rollout

- [ ] Feature flag controlled rollout implemented
- [ ] Backward compatibility maintained
- [ ] Performance monitoring active
- [ ] Migration completed successfully
- [ ] Legacy code removed

### Success Metrics

1. **Performance Improvements**

   - API response times reduced by 40%
   - WebSocket message processing improved by 60%
   - Frontend bundle size reduced by 25%

2. **Developer Experience**

   - Type safety coverage increased to 95%
   - API endpoint discovery time reduced by 70%
   - Development cycle time improved by 30%

3. **Reliability Improvements**

   - Runtime validation prevents 90% of API contract violations
   - Optimistic update conflicts reduced by 80%
   - Authentication security improved with httpOnly cookies

4. **Maintainability**
   - Code organization improved with domain separation
   - Service integration follows established patterns
   - Configuration management remains centralized

---

## Risk Mitigation

### Technical Risks

1. **Breaking Changes**: Maintain backward compatibility layer
2. **Performance Regression**: Continuous monitoring and rollback capability
3. **Type Safety Issues**: Comprehensive testing of Zod schemas

### Business Risks

1. **User Disruption**: Feature flag controlled rollout
2. **Data Loss**: Proper error handling and rollback procedures
3. **Security Vulnerabilities**: Security audit at each phase

### Operational Risks

1. **Deployment Issues**: Staged deployment with monitoring
2. **Service Dependencies**: Proper dependency injection testing
3. **Configuration Drift**: Automated configuration synchronization

---

## Conclusion

This implementation plan provides a comprehensive roadmap for refactoring the CoachIQ API architecture while maintaining integration with the existing service management platform. The phased approach ensures minimal disruption while delivering significant improvements in performance, security, and maintainability.

The plan emphasizes keeping business logic in the backend services, leveraging the existing Config Manager, Auth Manager, and Feature Manager systems, and following established architectural patterns for service integration and dependency injection.

Implementation should proceed phase by phase with thorough testing and monitoring at each stage to ensure successful delivery of the enhanced API architecture.

---

**Next Steps:**

1. Review and approve this implementation plan
2. Assign team members to specific phases
3. Set up monitoring and tracking systems
4. Begin Phase 1 implementation
5. Schedule regular review and adjustment meetings
