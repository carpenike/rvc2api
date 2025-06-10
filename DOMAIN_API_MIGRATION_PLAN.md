# Domain API v2 Migration Plan

## Executive Summary

This document outlines the migration plan from legacy API endpoints to a modern domain-driven API architecture (Domain API v2) for the CoachIQ platform. Since this is a **greenfield application with no production users**, we can implement a streamlined migration approach focused on speed and simplicity rather than complex zero-downtime strategies.

## Project Context

- **Application**: CoachIQ - Intelligent RV-C network management system
- **Architecture**: Local vehicle computer (Raspberry Pi) with web interface
- **Backend**: FastAPI with Python 3.11+ running on Pi
- **Frontend**: React SPA with TypeScript, Vite, TailwindCSS (localhost access)
- **Integration**: Direct CAN bus connection for vehicle component control
- **Current State**: Legacy monolithic API endpoints at `/api/*`
- **Target State**: Domain-driven API architecture at `/api/v2/{domain}`
- **Risk Level**: Low (no production users, local system only)

## Migration Overview

### Legacy API Consolidation
We are consolidating **14 legacy API routers** into **6 domain-specific APIs**:

| Legacy Endpoints | New Domain API | Description |
|------------------|----------------|-------------|
| `/api/entities`, `/api/dashboard`, `/api/bulk_operations` | `/api/v2/entities` | Entity control and bulk operations |
| `/api/can`, `/api/multi_network` | `/api/v2/networks` | CAN interface management |
| `/api/logs`, `/api/config` | `/api/v2/system` | System configuration and logging |
| `/api/advanced_diagnostics`, `/api/predictive_maintenance` | `/api/v2/diagnostics` | DTC management and health monitoring |
| `/api/analytics_dashboard`, `/api/performance_analytics` | `/api/v2/analytics` | Performance metrics and trend analysis |
| `/api/auth` | `/api/v2/auth` | Authentication and user management |

### Domain API v2 Architecture

```
/api/v2/
├── entities/     # Entity control, bulk operations
├── networks/     # CAN interface, message history
├── system/       # Configuration, features, logs, health
├── diagnostics/  # DTCs, fault correlation, maintenance
├── analytics/    # Performance metrics, trends, reports
└── auth/         # Authentication, user management
```

## Implementation Strategy

### Phase 1: Frontend API Client Migration (Days 1-2)

**Objective**: Update React frontend to use Domain API v2 endpoints

**Tasks**:
1. **Update API Client Architecture**
   ```typescript
   // frontend/src/api/v2/client.ts
   export class DomainAPIClient {
     entities = new EntitiesAPI('/api/v2/entities');
     networks = new NetworksAPI('/api/v2/networks');
     system = new SystemAPI('/api/v2/system');
     analytics = new AnalyticsAPI('/api/v2/analytics');
     auth = new AuthAPI('/api/v2/auth');
     diagnostics = new DiagnosticsAPI('/api/v2/diagnostics');
   }
   ```

2. **Create Domain-Specific API Modules**
   - `frontend/src/api/v2/entities.ts` - Entity control operations
   - `frontend/src/api/v2/networks.ts` - CAN interface management
   - `frontend/src/api/v2/system.ts` - Configuration and logging
   - `frontend/src/api/v2/diagnostics.ts` - DTC and health monitoring
   - `frontend/src/api/v2/analytics.ts` - Performance analytics
   - `frontend/src/api/v2/auth.ts` - Authentication flows

3. **Update Component API Calls**
   ```typescript
   // Before: /api/entities
   const entities = await fetch('/api/entities');

   // After: /api/v2/entities
   const entities = await apiClient.entities.getEntities();
   ```

4. **Endpoint Mapping Guide**
   - `GET /api/entities` → `GET /api/v2/entities`
   - `GET /api/logs` → `GET /api/v2/system/logs`
   - `GET /api/config` → `GET /api/v2/system/configuration`
   - `GET /api/can` → `GET /api/v2/networks`
   - `POST /api/bulk_operations` → `POST /api/v2/entities/bulk`

5. **Code Quality Checks (Throughout Phase 1)**
   ```bash
   # Run after each major change
   cd frontend
   npm run typecheck      # Verify TypeScript compilation
   npm run lint          # ESLint validation
   npm run lint:fix      # Auto-fix linting issues
   npm run build         # Production build verification
   ```

**Quality Gates**:
- ✅ All TypeScript errors resolved before proceeding
- ✅ ESLint passes with zero warnings/errors
- ✅ Production build completes successfully
- ✅ No unused imports or dead code

**Deliverables**:
- ✅ New API client with domain organization
- ✅ Updated React components using v2 endpoints
- ✅ TypeScript interfaces for v2 response models
- ✅ Clean codebase passing all quality checks

### Phase 2: Backend Domain API Activation (Day 1)

**Objective**: Enable all Domain API v2 features

**Tasks**:
1. **Enable Domain API Features**
   ```yaml
   # backend/services/feature_flags.yaml
   entities_api: {enabled: true}
   networks_api: {enabled: true}
   auth_api: {enabled: true}
   diagnostics_api: {enabled: true}
   analytics_api: {enabled: true}
   system_api: {enabled: true}  # Already enabled
   ```

2. **Verify Domain Router Registration**
   - Confirm all 6 domains register at `/api/v2/{domain}`
   - Test feature flag integration
   - Validate dependency injection

3. **Backend Code Quality Checks**
   ```bash
   # Run after feature flag changes
   cd backend
   poetry run pyright backend     # Type checking
   poetry run ruff check .        # Linting
   poetry run ruff format backend # Code formatting
   poetry run python run_server.py --debug  # Test server startup
   ```

**Deliverables**:
- ✅ All domain APIs accessible at `/api/v2/*`
- ✅ Feature flags properly configured
- ✅ API documentation updated in Swagger UI
- ✅ Backend code passes type checking and linting

### Phase 3: Testing & Validation (Days 2-3)

**Objective**: Ensure feature parity and system stability

**Tasks**:
1. **API Parity Testing**
   ```bash
   # Test all domain endpoints
   curl http://localhost:8080/api/v2/entities
   curl http://localhost:8080/api/v2/system/health
   curl http://localhost:8080/api/v2/networks/interfaces
   ```

2. **Frontend Integration Testing**
   - Verify all pages load with v2 APIs
   - Test entity control operations
   - Validate WebSocket connections
   - Check authentication flows

3. **Performance Validation**
   - Compare response times: legacy vs domain APIs
   - Test concurrent request handling
   - Validate WebSocket real-time updates

4. **Comprehensive Code Quality Validation**
   ```bash
   # Frontend quality checks
   cd frontend
   npm run typecheck && npm run lint && npm run build

   # Backend quality checks
   cd ../backend
   poetry run pyright backend && poetry run ruff check . && poetry run pytest

   # Integration test
   poetry run python run_server.py --debug &
   sleep 5
   curl -f http://localhost:8080/api/v2/entities/health || exit 1
   ```

**Quality Gates for Phase 3**:
- ✅ Zero TypeScript compilation errors
- ✅ Zero ESLint warnings or errors
- ✅ Frontend builds successfully for production
- ✅ Backend passes all type checking
- ✅ All backend tests pass
- ✅ API endpoints respond correctly

**Deliverables**:
- ✅ All functional tests passing
- ✅ Performance metrics within acceptable ranges
- ✅ No broken features or regressions
- ✅ Comprehensive code quality validation complete

### Phase 4: Legacy Cleanup (Days 3-4)

**Objective**: Remove legacy code and consolidate architecture

**Tasks**:
1. **Remove Legacy API Routers**
   ```bash
   # Delete legacy router files
   rm backend/api/routers/{entities,can,config,logs,dashboard}.py
   rm backend/api/routers/{bulk_operations,analytics_dashboard}.py
   rm backend/api/routers/{advanced_diagnostics,predictive_maintenance}.py
   ```

2. **Clean Up Route Registration**
   - Remove legacy router imports in `main.py`
   - Update API documentation
   - Clean up unused dependencies

3. **Update Documentation**
   - API documentation pointing to `/api/v2/*`
   - Remove legacy endpoint references
   - Update development guides

4. **Final Code Quality Verification**
   ```bash
   # Verify clean codebase after removal
   cd frontend
   npm run typecheck && npm run lint && npm run build

   cd ../backend
   poetry run pyright backend && poetry run ruff check . && poetry run pytest

   # Verify no dead imports or unused code
   poetry run ruff check . --select F401,F841
   ```

**Final Quality Gates**:
- ✅ No unused imports or dead code
- ✅ All quality checks pass post-cleanup
- ✅ Production build successful
- ✅ Test suite passes completely

**Deliverables**:
- ✅ Legacy code removed
- ✅ Clean codebase with only Domain API v2
- ✅ Updated documentation
- ✅ Final quality verification complete

### Phase 5: Documentation & Polish (Day 4-5)

**Objective**: Complete migration with proper documentation

**Tasks**:
1. **API Documentation Update**
   - OpenAPI specs reflect only v2 endpoints
   - Swagger UI shows domain organization
   - Response examples for all endpoints

2. **Developer Documentation**
   - Update README with new API patterns
   - Add domain API usage examples
   - Document TypeScript interfaces

3. **Final Quality Assurance**
   ```bash
   # Complete project quality verification
   cd frontend
   npm run typecheck && npm run lint && npm run build && npm run test

   cd ../backend
   poetry run pyright backend && poetry run ruff check . && poetry run pytest --cov=backend

   # Generate fresh API documentation
   poetry run python scripts/export_openapi.py
   ```

**Final Project Quality Standards**:
- ✅ 100% TypeScript compilation success
- ✅ Zero linting warnings or errors
- ✅ All tests passing with good coverage
- ✅ Production build ready
- ✅ API documentation up-to-date

**Deliverables**:
- ✅ Complete API documentation
- ✅ Developer guides updated
- ✅ Migration officially complete
- ✅ Project meets all quality standards

## Risk Management

### Risk Assessment: **VERY LOW**
- No production users to impact
- No external API consumers
- Local system deployment (no distributed system complexity)
- Full control over both frontend and backend
- Direct Pi access for debugging and rollbacks
- Ability to make breaking changes without notice

### Mitigation Strategies

1. **Incremental Testing**
   - Test each domain individually before full migration
   - Validate feature parity systematically
   - Monitor performance at each step

2. **Rollback Plan**
   ```bash
   # Simple Git rollback if issues arise
   git checkout main
   git reset --hard <previous-commit>
   ```

3. **Monitoring & Validation**
   - Check all page loads after migration
   - Verify WebSocket connections
   - Test authentication flows
   - Validate entity control operations

## Technical Considerations

### Local System Architecture
Since this is a **local vehicle computer system** (Pi + React frontend), we have several advantages:
- **No network latency concerns** - All communication is localhost or LAN
- **Reliable connectivity** - No intermittent connection issues to handle
- **Single deployment target** - Pi environment is controlled and consistent
- **Direct CAN bus access** - Real-time vehicle data without network overhead

### API Response Compatibility
Since we control both frontend and backend, we can make breaking changes to response formats. The new domain APIs use enhanced schemas with:
- Consistent error handling patterns
- Standardized pagination
- Improved type safety
- Better validation

### WebSocket Migration
WebSocket endpoints will be migrated to domain-specific paths for better organization:
```
/ws/entities → /api/v2/entities/ws      # Real-time entity state changes
/ws/logs → /api/v2/system/ws/logs       # Live log streaming
/ws/analytics → /api/v2/analytics/ws    # Performance metrics updates
```

This approach provides cleaner separation of real-time data streams and allows the frontend to subscribe only to relevant domain updates.

### Authentication Integration
Domain APIs integrate with existing authentication:
- JWT token validation
- Role-based access control
- Feature flag permissions
- User context injection

## Success Criteria

### Functional Requirements
- ✅ All existing functionality preserved
- ✅ Frontend successfully using Domain API v2
- ✅ WebSocket real-time updates working
- ✅ Authentication and authorization intact
- ✅ Entity control operations functional

### Non-Functional Requirements
- ✅ Response times ≤ legacy API performance
- ✅ API documentation complete and accurate
- ✅ TypeScript types properly defined
- ✅ No broken links or 404 errors
- ✅ Clean codebase without legacy artifacts

### Code Quality
- ✅ Domain separation properly implemented
- ✅ Dependency injection working correctly
- ✅ Feature flags controlling access
- ✅ Error handling consistent across domains
- ✅ OpenAPI specs automatically generated
- ✅ TypeScript compilation error-free
- ✅ ESLint rules enforced throughout
- ✅ Backend type checking passes
- ✅ Test coverage maintained/improved
- ✅ No unused imports or dead code

## Timeline Summary

| Phase | Duration | Key Activities |
|-------|----------|----------------|
| **Phase 1** | Days 1-2 | Frontend API client migration |
| **Phase 2** | Day 1 | Backend domain API activation |
| **Phase 3** | Days 2-3 | Testing and validation |
| **Phase 4** | Days 3-4 | Legacy cleanup |
| **Phase 5** | Days 4-5 | Documentation and polish |

**Total Duration**: 4-5 days

## Post-Migration Benefits

### Developer Experience
- **Cleaner API Organization**: Domain-driven structure is more intuitive
- **Better Type Safety**: Enhanced TypeScript integration
- **Improved Documentation**: Automatic OpenAPI generation
- **Consistent Patterns**: Standardized request/response formats

### System Architecture
- **Reduced Complexity**: 14 routers → 6 domains
- **Better Separation of Concerns**: Clear domain boundaries
- **Enhanced Scalability**: Feature flag controlled APIs
- **Future-Proof Design**: Domain-driven architecture supports growth

### Maintenance Benefits
- **Easier Testing**: Domain-specific test suites
- **Simpler Debugging**: Clear request routing
- **Better Monitoring**: Domain-level metrics
- **Cleaner Codebase**: Eliminated legacy technical debt

## Conclusion

This migration plan leverages the greenfield nature of the CoachIQ application to implement a clean, efficient transition to Domain API v2. With no production users to impact, we can focus on speed and simplicity while establishing a robust, scalable API architecture for future development.

The 4-5 day timeline provides a systematic approach to migrating from 14 legacy endpoints to 6 well-organized domain APIs, resulting in a cleaner codebase, better developer experience, and a more maintainable system architecture.
