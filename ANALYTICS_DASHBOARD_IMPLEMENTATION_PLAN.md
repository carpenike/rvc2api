# Analytics Dashboard Implementation Plan

## Overview

This document outlines the phased implementation plan for enhancing the analytics dashboard from its current in-memory implementation to a production-ready system with persistent storage, improved UX, and scalable architecture.

**Current Status**: Analytics dashboard is functionally complete but uses in-memory storage unsuitable for production.

**Goal**: Transform to a robust, scalable analytics platform suitable for 1-5 RV users with potential for growth.

## Research Summary

Based on technical research conducted via Perplexity and Context7:

### Storage Solution: SQLite + Hybrid Approach
- **Recommendation**: SQLite with limited in-memory caching for recent data (2 hours)
- **Rationale**: Perfect balance for small-scale systems (1-5 users), persistent storage, no additional services
- **Performance**: Use indexes on timestamp columns, batch inserts, window functions for aggregations

### Background Processing: FastAPI Built-in Async Tasks
- **Approach**: Use FastAPI's lifespan events and asyncio background tasks
- **Rationale**: Simpler than Celery for small scale, integrated with existing service management
- **Pattern**: Periodic data flushing, cleanup, and insight generation tasks

## Phase 1: Optional Persistent Storage (Critical Priority)

**Duration**: 3-5 days
**Goal**: Add optional SQLite persistence while maintaining full in-memory functionality

### 1.1 Persistence-Aware Storage Service Architecture

**Core Principle**: All analytics functionality works without persistence enabled

```python
class AnalyticsStorageService:
    """Storage service with optional SQLite persistence"""

    def __init__(self, feature_manager, settings):
        self.feature_manager = feature_manager
        self.settings = settings
        self.persistence_enabled = feature_manager.is_enabled("persistence")

        # Core in-memory storage (always present)
        self.metric_history = defaultdict(list)
        self.insights_cache = []
        self.pattern_cache = []

        # Optional SQLite components
        self.db_connection = None
        if self.persistence_enabled:
            self._initialize_sqlite()

    def _initialize_sqlite(self):
        """Initialize SQLite only if persistence is enabled"""
        try:
            # Create connection and tables
            # If fails, log warning and continue with in-memory only
        except Exception as e:
            logger.warning(f"SQLite initialization failed, using in-memory only: {e}")
            self.persistence_enabled = False
```

### 1.2 Conditional Database Schema (Only if Persistence Enabled)

```sql
-- Created only when persistence feature flag is enabled
CREATE TABLE IF NOT EXISTS analytics_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_name TEXT NOT NULL,
    value REAL NOT NULL,
    metadata JSON,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS analytics_insights (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    insight_id TEXT UNIQUE,
    title TEXT NOT NULL,
    description TEXT,
    category TEXT,
    severity TEXT CHECK(severity IN ('low', 'medium', 'high', 'critical')),
    confidence REAL CHECK(confidence >= 0 AND confidence <= 1),
    impact_score REAL CHECK(impact_score >= 0 AND impact_score <= 1),
    recommendations JSON,
    metadata JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME
);

CREATE TABLE IF NOT EXISTS analytics_patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_id TEXT UNIQUE,
    pattern_type TEXT,
    description TEXT,
    confidence REAL,
    frequency TEXT,
    correlation_factors JSON,
    metadata JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Indexes created only if tables exist
CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON analytics_metrics(timestamp);
CREATE INDEX IF NOT EXISTS idx_metrics_name_time ON analytics_metrics(metric_name, timestamp);
CREATE INDEX IF NOT EXISTS idx_insights_severity ON analytics_insights(severity, created_at);
CREATE INDEX IF NOT EXISTS idx_patterns_type ON analytics_patterns(pattern_type, created_at);
```

### 1.3 Dual-Mode Service Implementation

**File**: `backend/services/analytics_storage_service.py`

```python
class AnalyticsStorageService:
    """Analytics storage with optional persistence support"""

    async def record_metric(self, metric_name: str, value: float, metadata=None):
        # ALWAYS store in memory for immediate access
        timestamp = time.time()
        metric_entry = {
            "value": value,
            "timestamp": timestamp,
            "metadata": metadata
        }
        self.metric_history[metric_name].append(metric_entry)

        # OPTIONALLY persist to SQLite if enabled
        if self.persistence_enabled and self.db_connection:
            try:
                await self._persist_metric_to_sqlite(metric_name, value, metadata, timestamp)
            except Exception as e:
                logger.warning(f"Failed to persist metric to SQLite: {e}")
                # Continue with in-memory only - no functionality loss

        # Cleanup old in-memory data based on retention settings
        await self._cleanup_memory_cache(metric_name)

    async def get_metrics_trend(self, metric_name: str, hours: int = 24):
        # Start with in-memory data (always available)
        cutoff = time.time() - (hours * 3600)
        memory_data = [
            entry for entry in self.metric_history[metric_name]
            if entry["timestamp"] >= cutoff
        ]

        # If persistence enabled, supplement with historical data
        if self.persistence_enabled and self.db_connection and hours > self.memory_retention_hours:
            try:
                historical_data = await self._query_historical_metrics(metric_name, hours)
                # Merge memory + historical, deduplicate
                return self._merge_metric_data(memory_data, historical_data)
            except Exception as e:
                logger.warning(f"Failed to query historical data: {e}")
                # Fall back to memory data only

        return memory_data
```

### 1.4 Environment Variable Configuration

**Core analytics works with just these environment variables**:

```bash
# Core functionality (no persistence required)
COACHIQ_ANALYTICS__ENABLED=true
COACHIQ_ANALYTICS__MEMORY_RETENTION_HOURS=2
COACHIQ_ANALYTICS__INSIGHT_GENERATION_INTERVAL=900
COACHIQ_ANALYTICS__PATTERN_ANALYSIS_INTERVAL=1800

# Optional persistence settings (only used if persistence feature enabled)
COACHIQ_ANALYTICS__DB_PATH=data/analytics.db
COACHIQ_ANALYTICS__PERSISTENCE_RETENTION_DAYS=30
COACHIQ_ANALYTICS__ENABLE_BACKGROUND_PERSISTENCE=true
```

### 1.5 Feature Flag Integration

**Update**: `backend/services/feature_flags.yaml`

```yaml
analytics_dashboard:
  enabled: true
  core: false
  depends_on: [performance_analytics, entity_manager]
  description: "Advanced analytics dashboard with performance visualization, trend analysis, and system health monitoring"
  friendly_name: "Analytics Dashboard"
  # Core settings (always available)
  memory_retention_hours: 2
  insight_generation_interval_seconds: 900
  pattern_analysis_interval_seconds: 1800
  max_memory_insights: 100
  max_memory_patterns: 50
  # Persistence settings (only used if persistence feature enabled)
  persistence_retention_days: 30
  enable_background_persistence: true
  sqlite_batch_size: 100
```

### 1.6 Migration Strategy

**Phase 1a: Core In-Memory Enhancement**
- Improve current in-memory implementation
- Add retention policies for memory management
- Ensure graceful degradation if any component fails

**Phase 1b: Optional Persistence Layer**
- Add SQLite support as enhancement layer
- Test with persistence disabled to ensure core functionality
- Validate graceful fallback when SQLite fails

**Phase 1c: Integration Testing**
- Test all scenarios: persistence enabled/disabled/failed
- Verify environment-variable-only operation
- Ensure zero functionality loss in any mode

## Phase 2: Background Task Enhancement (High Priority)

**Duration**: 2-3 days
**Goal**: Implement proper background processing using FastAPI patterns

### 2.1 Background Task Manager
**File**: `backend/services/analytics_background_service.py`

```python
class AnalyticsBackgroundService:
    """Manages periodic analytics tasks using FastAPI lifespan"""

    async def start(self):
        # Create background tasks for:
        # - Data cleanup (hourly)
        # - Insight generation (every 15 minutes)
        # - Pattern analysis (every 30 minutes)
        # - Cache maintenance (every 5 minutes)

    async def _periodic_cleanup(self):
        # Remove metrics older than retention period
        # Cleanup expired insights and patterns

    async def _generate_insights(self):
        # Analyze recent metrics for anomalies
        # Generate actionable recommendations
        # Store in insights cache
```

### 2.2 Integration with Main Application
- **Update**: `main.py` lifespan function to start background service
- **Coordinate**: With existing feature manager and service lifecycle
- **Configure**: Background task intervals via settings

### 2.3 Data Retention and Cleanup
- **Default retention**: 30 days for metrics, 7 days for insights
- **Configurable**: Via environment variables and feature flags
- **Efficient cleanup**: Batch deletions with proper indexing

## Phase 3: API and Data Model Improvements (Medium Priority)

**Duration**: 2-3 days
**Goal**: Enhance API design with proper Pydantic models and type safety

### 3.1 Response Models
**File**: `backend/models/analytics.py`

```python
class PerformanceTrendsResponse(BaseModel):
    time_window_hours: int
    resolution: str
    summary: TrendsSummary
    metrics: Dict[str, MetricTrendData]
    alerts: List[PerformanceAlert]
    generated_at: datetime

class SystemInsightsResponse(BaseModel):
    total_insights: int
    insights: List[SystemInsight]
    severity_distribution: Dict[str, int]
    summary: InsightsSummary
    generated_at: datetime
```

### 3.2 API Endpoint Improvements
- **Replace**: `dict[str, Any]` with proper response models
- **Enhance**: Query parameter handling (native FastAPI list support)
- **Add**: Comprehensive OpenAPI documentation
- **Implement**: Proper error handling and validation

### 3.3 Business Logic Validation
- **Move**: Complex analytics logic to backend services
- **Simplify**: Frontend to pure presentation layer
- **Validate**: All inputs at API boundary
- **Sanitize**: User-provided parameters

## Phase 4: User Experience Enhancements (Medium Priority)

**Duration**: 3-4 days
**Goal**: Transform from "wall of numbers" to actionable insights

### 4.1 Visual Data Presentation
**Frontend Files**:
- `frontend/src/components/analytics/TrendChart.tsx`
- `frontend/src/components/analytics/CorrelationHeatmap.tsx`
- `frontend/src/components/analytics/PatternVisualization.tsx`

**Implementation**:
- **Add**: Recharts for time-series visualization
- **Create**: Interactive trend charts with anomaly highlighting
- **Build**: Correlation heatmap for metric relationships
- **Display**: Pattern cyclical behavior overlays

### 4.2 Actionable Insights
**Backend**: Structured recommendation format
```python
class ActionableRecommendation(BaseModel):
    text: str
    action: Optional[DeviceAction] = None
    estimated_impact: Optional[str] = None
    severity: str

class DeviceAction(BaseModel):
    type: str  # "DEVICE_CONTROL", "CONFIGURATION_CHANGE"
    target_device_id: str
    command: str
    payload: Dict[str, Any]
```

**Frontend**: One-click action buttons for recommendations

### 4.3 Real-time Updates
- **Implement**: WebSocket notifications for critical insights
- **Use**: TanStack Query invalidation on WebSocket messages
- **Provide**: Real-time feel without constant polling

## Phase 5: Configuration and Customization (Enhancement)

**Duration**: 2-3 days
**Goal**: User-configurable analytics parameters

### 5.1 Configuration Interface
- **Metric thresholds**: User-defined alert levels
- **Custom KPIs**: Combine multiple metrics
- **Notification preferences**: Email/SMS via background tasks
- **Dashboard layouts**: Persistent user preferences

### 5.2 Feature Flag Integration
**File**: `backend/services/feature_flags.yaml`
```yaml
analytics_dashboard_enhanced:
  enabled: true
  depends_on: [analytics_dashboard, database_manager]
  description: "Enhanced analytics with persistent storage and background processing"
  custom_retention_days: 30
  enable_background_tasks: true
  enable_actionable_insights: true
```

## Integration Requirements

### Service Management Platform Integration

All components must integrate with existing platform services:

#### Config Manager Integration
```python
# Use existing settings pattern
class AnalyticsSettings(BaseSettings):
    # Core settings (always available)
    enabled: bool = True
    memory_retention_hours: int = 2
    insight_generation_interval: int = 900  # 15 minutes
    pattern_analysis_interval: int = 1800   # 30 minutes
    max_memory_insights: int = 100
    max_memory_patterns: int = 50

    # Persistence settings (only used if persistence feature enabled)
    db_path: str = "data/analytics.db"
    persistence_retention_days: int = 30
    enable_background_persistence: bool = True
    sqlite_batch_size: int = 100

    class Config:
        env_prefix = "COACHIQ_ANALYTICS_"
```

#### Persistence Feature Detection
```python
class AnalyticsDashboardService:
    def __init__(self, feature_manager, settings):
        self.feature_manager = feature_manager
        self.settings = settings

        # Core functionality always available
        self.memory_storage = AnalyticsMemoryStorage(settings)

        # Optional persistence layer
        self.persistence_enabled = feature_manager.is_enabled("persistence")
        self.sqlite_storage = None

        if self.persistence_enabled:
            try:
                self.sqlite_storage = AnalyticsSQLiteStorage(settings)
                logger.info("Analytics persistence enabled with SQLite")
            except Exception as e:
                logger.warning(f"SQLite initialization failed, using memory-only: {e}")
                self.persistence_enabled = False
        else:
            logger.info("Analytics running in memory-only mode")
```

#### Auth Manager Integration
```python
# All API endpoints use existing auth middleware
@router.get("/analytics/trends")
async def get_performance_trends(
    request: Request,
    current_user: User = Depends(get_current_user),  # Existing auth
    service: AnalyticsDashboardService = Depends(get_analytics_service)
):
```

#### Feature Manager Integration
```python
# Check analytics feature enabled, but NOT persistence
def _check_analytics_enabled(request: Request) -> None:
    feature_manager = get_feature_manager_from_request(request)
    if not feature_manager.is_enabled("analytics_dashboard"):
        raise HTTPException(status_code=404, detail="Analytics dashboard disabled")
    # Note: persistence is optional and checked separately in service
```

### Database Manager Integration
- **Use**: Existing database configuration patterns
- **Share**: Connection pooling where applicable
- **Coordinate**: Migration and initialization scripts

## Implementation Timeline

| Phase | Duration | Priority | Dependencies |
|-------|----------|----------|--------------|
| Phase 1: Storage Migration | 3-5 days | Critical | None |
| Phase 2: Background Tasks | 2-3 days | High | Phase 1 |
| Phase 3: API Improvements | 2-3 days | Medium | Phase 1 |
| Phase 4: UX Enhancements | 3-4 days | Medium | Phase 2,3 |
| Phase 5: Configuration | 2-3 days | Enhancement | All others |

**Total Estimated Duration**: 12-18 days

## Risk Mitigation

### Technical Risks
1. **SQLite Performance**: Monitor query performance, add indexes as needed
2. **Memory Usage**: Implement proper cache size limits and cleanup
3. **Background Task Failures**: Add error handling and restart logic

### Migration Risks
1. **Data Loss**: Implement backup/restore procedures
2. **Downtime**: Design for zero-downtime migration with feature flags
3. **Rollback**: Maintain compatibility with previous in-memory version

## Success Metrics

### Phase 1 Success Criteria
- [ ] **Environment-Variable-Only Mode**: Full analytics functionality with just env vars, no persistence
- [ ] **Optional Persistence**: When enabled, data persists across restarts without breaking functionality
- [ ] **Graceful Degradation**: SQLite failures don't break in-memory analytics
- [ ] **Feature Flag Integration**: Persistence can be toggled without service restart
- [ ] **No Performance Degradation**: In-memory mode performs as well as current implementation

### Core Functionality Requirements (Must Work Without Persistence)
- [ ] Performance trends analysis (last 2 hours in memory)
- [ ] System insights generation (up to 100 cached insights)
- [ ] Pattern detection (up to 50 cached patterns)
- [ ] Real-time metric recording and retrieval
- [ ] Background insight/pattern generation tasks
- [ ] API endpoints return data from memory when persistence disabled

### Enhanced Functionality (Only When Persistence Enabled)
- [ ] Historical data beyond memory retention window
- [ ] Long-term trend analysis (weeks/months)
- [ ] Data survives service restarts
- [ ] Background SQLite maintenance tasks

### Phase 2 Success Criteria
- [ ] Background tasks work in both memory-only and persistent modes
- [ ] Memory cleanup prevents unbounded growth
- [ ] Insights generated and cached appropriately in both modes
- [ ] System maintains responsiveness under load

### Overall Success Criteria
- [ ] **Memory-Only Mode**: Dashboard loads in < 2 seconds with recent data
- [ ] **Persistent Mode**: Dashboard loads in < 2 seconds with historical data
- [ ] Real-time updates feel instant (< 500ms) in both modes
- [ ] Users can take direct action on recommendations
- [ ] System scales to handle 5 concurrent users
- [ ] **Memory-Only**: RAM usage bounded to < 50MB for analytics
- [ ] **Persistent Mode**: SQLite database bounded to < 100MB for 30 days

## Monitoring and Observability

### Metrics to Track
- SQLite query performance and execution times
- Background task execution frequency and duration
- Cache hit/miss ratios for recent metrics
- API response times for analytics endpoints
- Database size growth over time
- Memory usage of in-memory cache

### Alerting
- Background task failures
- Database connection issues
- Excessive memory usage
- API response time degradation

## Future Considerations

### Scalability Path
If the system grows beyond 5 users:
1. **Phase A**: Migrate to PostgreSQL with TimescaleDB
2. **Phase B**: Implement Celery for background processing
3. **Phase C**: Add Redis for caching layer
4. **Phase D**: Consider microservices architecture

### Advanced Analytics
- Machine learning for predictive insights
- Anomaly detection using statistical models
- Cross-RV fleet analytics for benchmarking
- Integration with external IoT platforms

---

**Document Version**: 1.0
**Last Updated**: December 2024
**Next Review**: After Phase 1 completion
