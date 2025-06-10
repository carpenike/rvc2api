# API Migration Command

**Command**: `/api-migration`
**Purpose**: Migrate legacy API endpoints to Domain API v2 with progressive rollout

## Usage

When the user needs to migrate from legacy APIs to Domain API v2, or when implementing progressive migration strategies, use this workflow:

## Migration Strategy Overview

The project supports **progressive migration** from legacy `/api/entities` endpoints to Domain API v2 `/api/v2/{domain}` endpoints with:

- ✅ **Zero downtime** - Both APIs run simultaneously
- ✅ **Feature flags** - Control rollout percentage
- ✅ **Automatic fallback** - Domain API failures fall back to legacy
- ✅ **Monitoring** - Track migration progress and performance
- ✅ **Emergency rollback** - Quick revert capabilities

## Migration Workflow Steps

### 1. Assessment Phase
- **Identify Legacy Endpoints**: Find which legacy endpoints need migration
- **Analyze Usage Patterns**: Check current API usage and performance
- **Plan Domain Structure**: Determine how legacy endpoints map to domains
- **Feature Flag Planning**: Design rollout strategy with percentages

### 2. Implementation Phase
- **Create Domain API**: Implement Domain API v2 endpoints following patterns
- **Add Compatibility Layer**: Implement data transformation between formats
- **Setup Feature Flags**: Configure progressive rollout controls
- **Add Monitoring**: Implement migration tracking and alerts

### 3. Migration Phase
- **Start Small**: Begin with 1-5% traffic to Domain API
- **Monitor Metrics**: Track error rates, performance, user feedback
- **Gradual Increase**: Incrementally increase percentage (5% → 25% → 50% → 75% → 100%)
- **Address Issues**: Fix problems discovered during rollout

### 4. Completion Phase
- **Full Migration**: Move 100% traffic to Domain API
- **Legacy Deprecation**: Mark legacy endpoints as deprecated
- **Cleanup**: Remove legacy code and migration infrastructure

## Implementation Templates

### Backend Migration Middleware

```python
# backend/middleware/migration_middleware.py
import random
from fastapi import Request, Response
from backend.core.config import get_settings

class APIMigrationMiddleware:
    """Progressive migration middleware for API endpoints."""

    def __init__(self):
        self.settings = get_settings()

    async def __call__(self, request: Request, call_next):
        # Check if this is a legacy API request
        if self._is_legacy_api_request(request):
            if self._should_migrate_request(request):
                # Try domain API with fallback to legacy
                return await self._try_domain_api_with_fallback(request, call_next)

        return await call_next(request)

    def _should_migrate_request(self, request: Request) -> bool:
        """Determine if request should use domain API based on rollout percentage."""
        rollout_percentage = self._get_rollout_percentage()

        # Use deterministic migration based on user ID if available
        user_id = getattr(request.state, 'user_id', None)
        if user_id:
            hash_value = hash(user_id) % 100
            return hash_value < (rollout_percentage * 100)

        # Random for anonymous users
        return random.random() < rollout_percentage
```

### Frontend Migration Hook

```typescript
// frontend/src/hooks/useMigrationStrategy.ts
import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';

interface MigrationConfig {
  entities_domain_enabled: boolean;
  rollout_percentage: number;
  enable_fallback: boolean;
}

export function useMigrationStrategy() {
  const [migrationConfig, setMigrationConfig] = useState<MigrationConfig | null>(null);

  const { data: config } = useQuery({
    queryKey: ['migration-config'],
    queryFn: () => fetch('/api/config/migration').then(r => r.json()),
    staleTime: 60000,
  });

  const shouldUseDomainAPI = (domain: string, userId?: string): boolean => {
    if (!migrationConfig?.entities_domain_enabled) return false;

    const rolloutPercentage = migrationConfig.rollout_percentage;

    if (userId) {
      // Deterministic based on user ID
      const hash = hashCode(userId);
      return (hash % 100) < (rolloutPercentage * 100);
    }

    // Use stored flag for session consistency
    const storageKey = `migration_${domain}`;
    const stored = localStorage.getItem(storageKey);

    if (stored !== null) {
      return stored === 'true';
    }

    const shouldMigrate = Math.random() < rolloutPercentage;
    localStorage.setItem(storageKey, shouldMigrate.toString());
    return shouldMigrate;
  };

  return { migrationConfig, shouldUseDomainAPI };
}
```

### Progressive Migration Client

```typescript
// frontend/src/api/migratedClient.ts
import { withDomainAPIFallback } from './domains';
import { fetchEntities as fetchEntitiesLegacy } from './endpoints';
import { fetchEntitiesV2 } from './domains/entities';
import { useMigrationStrategy } from '../hooks/useMigrationStrategy';

export class MigratedEntitiesClient {
  private migrationStrategy = useMigrationStrategy();

  async fetchEntities(params?: any, options: { preferDomainAPI?: boolean } = {}) {
    const shouldUseDomain = options.preferDomainAPI ??
      this.migrationStrategy.shouldUseDomainAPI('entities');

    if (shouldUseDomain) {
      return withDomainAPIFallback(
        () => fetchEntitiesV2(params),
        () => fetchEntitiesLegacy(params),
        { preferDomainAPI: true, fallbackToLegacy: true, logMigration: true }
      );
    }

    return fetchEntitiesLegacy(params);
  }
}
```

## Migration Monitoring

### Migration Dashboard Component

```typescript
// frontend/src/components/admin/MigrationDashboard.tsx
import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';

export function MigrationDashboard() {
  const { data: metrics } = useQuery({
    queryKey: ['migration-metrics'],
    queryFn: () => fetch('/api/admin/migration/metrics').then(r => r.json()),
    refetchInterval: 30000,
  });

  const [rolloutPercentage, setRolloutPercentage] = useState([10]);

  const updateMigrationConfig = useMutation({
    mutationFn: (config: any) =>
      fetch('/api/admin/migration/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config),
      }),
  });

  const handleEmergencyRollback = () => {
    updateMigrationConfig.mutate({
      entities_domain_rollout: 0,
      enable_legacy_fallback: true,
      emergency_rollback: true,
    });
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">API Migration Dashboard</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Migration Progress</CardTitle>
          </CardHeader>
          <CardContent>
            <Progress value={metrics?.migration_percentage || 0} />
            <div className="text-2xl font-bold">{metrics?.migration_percentage || 0}%</div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Migration Controls</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-sm font-medium">
              Domain API Rollout: {rolloutPercentage[0]}%
            </label>
            <Slider
              value={rolloutPercentage}
              onValueChange={setRolloutPercentage}
              max={100}
              step={5}
            />
          </div>

          <div className="flex gap-2">
            <Button onClick={() => updateMigrationConfig.mutate({ entities_domain_rollout: rolloutPercentage[0] / 100 })}>
              Update Configuration
            </Button>
            <Button variant="destructive" onClick={handleEmergencyRollback}>
              Emergency Rollback
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
```

## Migration Checklist

### Pre-Migration Setup
- [ ] Domain API v2 implementation complete and tested
- [ ] Migration middleware implemented
- [ ] Feature flags configured in `backend/services/feature_flags.yaml`
- [ ] Migration monitoring dashboard created
- [ ] Emergency rollback procedures tested
- [ ] Data transformation layers implemented
- [ ] Performance benchmarks established

### Migration Execution
- [ ] Start with 1% rollout and monitor for 24 hours
- [ ] Check error rates, performance metrics, user feedback
- [ ] Gradually increase: 5% → 10% → 25% → 50% → 75% → 100%
- [ ] At each stage, monitor for 24-48 hours before proceeding
- [ ] Address any issues found during rollout
- [ ] Document lessons learned

### Post-Migration Cleanup
- [ ] 100% traffic successfully migrated to Domain API v2
- [ ] Legacy endpoints marked as deprecated
- [ ] Migration infrastructure removed
- [ ] Documentation updated
- [ ] Team training on new API patterns completed

## Key Migration Patterns

### Feature Flag Configuration

```yaml
# backend/services/feature_flags.yaml
api_migration:
  enabled: true
  core: false
  description: "Progressive API migration control"
  config:
    entities_domain_rollout: 0.1  # Start with 10%
    enable_legacy_fallback: true
    log_migration_events: true
    max_error_rate: 0.05  # 5% error threshold
```

### Fallback Pattern

```typescript
// Always use fallback pattern for gradual migration
const result = await withDomainAPIFallback(
  () => fetchEntitiesV2(params),      // Try domain API first
  () => fetchEntitiesLegacy(params),  // Fall back to legacy
  {
    preferDomainAPI: true,
    fallbackToLegacy: true,
    logMigration: true,
    timeout: 5000
  }
);
```

### Error Handling

```typescript
// Handle migration-specific errors
try {
  const result = await domainAPICall();
  logMigrationSuccess('entities', 'list');
  return result;
} catch (error) {
  logMigrationError('entities', 'list', error);
  // Automatic fallback to legacy API
  return await legacyAPICall();
}
```

## Documentation References

- **Migration Guide**: `docs/migration/legacy-to-domain-api-migration.md`
- **Domain API Documentation**: `docs/api/domain-api-v2.md`
- **Feature Flags**: `backend/services/feature_flags.yaml`
- **Migration Tests**: `tests/api/test_domain_entities_integration.py`

## Emergency Procedures

### Immediate Rollback
```bash
# Set rollout to 0% immediately
curl -X POST /api/admin/migration/emergency-rollback \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"reason": "High error rate detected"}'
```

### Health Checks
```bash
# Check migration status
curl /api/admin/migration/status

# Check domain API health
curl /api/v2/entities/health

# Check legacy API health
curl /api/entities/health
```

Remember: **Migration should be gradual, monitored, and reversible at all times!**
