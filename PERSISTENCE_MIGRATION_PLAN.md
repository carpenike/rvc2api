# CoachIQ Persistence Migration Plan
## Transition from Optional to Mandatory SQLite Persistence

### Executive Summary

This document outlines a comprehensive plan to migrate CoachIQ from its current optional persistence architecture to a mandatory SQLite-based system. The migration addresses critical architectural issues including silent feature failures, maintenance overhead, and incomplete schema management while following SQLAlchemy 2.0+ best practices.

**Target Deployment**: Single-instance deployment on Raspberry Pi with USB SSD storage in motorhome environments with 1-5 concurrent users. USB SSD eliminates storage wear concerns and enables optimized performance settings.

### Current Architecture Analysis

#### Strengths
- **Clean Interface Abstraction**: Well-designed persistence interface with `PersistenceServiceInterface`
- **Graceful Degradation**: System currently works without persistence enabled
- **Feature Flag Control**: Centralized feature management via `feature_flags.yaml`
- **Dual-Mode Analytics**: Memory + optional SQLite storage
- **Multi-Backend Ready**: Foundation for PostgreSQL/MySQL support

#### Critical Issues
1. **Silent Feature Degradation**: Authentication, analytics, and predictive maintenance fail silently without persistence
2. **Maintenance Overhead**: Diverging implementations (SQLite vs in-memory)
3. **Incomplete Schema Management**: Auth and analytics tables missing from Alembic migrations
4. **Entity State Gap**: Entity states not persisted, reset on restart
5. **Implicit Dependencies**: Features depend on persistence but don't declare it

### Migration Strategy

#### Phase 1: Foundation & Schema Unification (Weeks 1-2)

**1.1 Feature Flag Dependencies Update**
```yaml
# Update feature_flags.yaml
persistence:
  enabled: true
  core: true  # Promote to non-disablable core service
  depends_on: []

authentication:
  enabled: true
  core: false
  depends_on: [persistence, notifications]  # Add explicit persistence dependency

system_analytics:
  enabled: true
  core: false
  depends_on: [persistence, entity_manager, can_interface]  # Add persistence

predictive_maintenance:
  enabled: true
  core: false
  depends_on: [persistence, entity_manager, can_interface]  # Add persistence

analytics_dashboard:
  enabled: true
  core: false
  depends_on: [persistence, performance_analytics, entity_manager]  # Add persistence
```

**1.2 Six-Layer Configuration Hierarchy**

Replace the current environment variable-heavy approach with a sophisticated, layered configuration system that properly handles protocol definitions, coach models, and user customizations:

**Layer 1: Core Protocol Specification (Nix-Deployed to `/var/lib/coachiq`)**
```json
// /var/lib/coachiq/config/rvc.json - RV-C protocol definitions
{
  "schema_version": "2.1",
  "pgns": {
    "0x1FEDA": {
      "name": "DC_DIMMER_COMMAND_2",
      "fields": [
        {"name": "Dimmer_Level", "type": "uint8", "units": "%"}
      ]
    }
  }
}
```

**Layer 2: Coach Model Base Definition (Nix-Deployed to `/var/lib/coachiq`)**
```yaml
# /var/lib/coachiq/config/models/2021_entegra_aspire_44r.yml - Coach-specific mappings
schema_version: 1.1
model_name: "Entegra Aspire 44R (2021)"

# Extend/override RV-C spec for manufacturer quirks
protocol_extensions:
  pgns:
    '0x1EF56':  # Entegra-specific PGN
      name: "ENTEGRA_AWNING_CONTROL"
      fields:
        - name: "LED_Brightness"
          type: "uint8"
          units: "%"

# Physical entity mapping for this specific coach
entities:
  lights:
    - id: "light.living_room_main"
      name: "Living Room Main"
      can_address: "0x23"
      pgn: "0x1FEDA"
      instance: 1
  tanks:
    - id: "tank.fresh_water"
      name: "Fresh Water"
      can_address: "0x32"
      capacity_gallons: 150
```

**Layer 3: User Structural Customizations (User-Managed via UI)**
```json
// /var/lib/coachiq/user_patches.json - JSON Patch operations
[
  {
    "op": "add",
    "path": "/entities/lights/-",
    "value": {
      "id": "light.custom_led_strip",
      "name": "Custom LED Strip",
      "can_address": "0x87",
      "pgn": "0x1FEDA",
      "instance": 15
    }
  },
  {
    "op": "replace",
    "path": "/entities/tanks/0/capacity_gallons",
    "value": 175
  }
]
```

**Layer 4: System Settings (Nix-Deployed to `/var/lib/coachiq`)**
```toml
# /var/lib/coachiq/config/system.toml - System deployment configuration
[coach]
default_model = "2021_entegra_aspire_44r"
model_directory = "/var/lib/coachiq/config/models"

[storage_profile]
type = "ssd"
data_dir = "/var/lib/coachiq"

[features]
enable_system_analytics = true
enable_authentication = true

[protocols]
rvc.enabled = true
j1939.enabled = false

[server]
host = "0.0.0.0"
port = 8080
workers = 1

[can]
interface_mappings = { house = "can0", chassis = "can1" }
bitrate = 500000
```

**Layer 5: User Config Overrides (User-Managed TOML)**
```toml
# /var/lib/coachiq/user/config-overrides.toml - User config overrides
[server]
port = 8081  # Override default port from system.toml

[logging]
level = "DEBUG"  # Override for troubleshooting

[features]
enable_development_features = true  # Enable dev features
```

**Layer 6: User Model Selection & System State (SQLite)**
```sql
-- /var/lib/coachiq/user/coachiq.db - Mutable system state
CREATE TABLE system_settings (
    key TEXT PRIMARY KEY,
    value TEXT,
    last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO system_settings VALUES
  ('active_coach_model', '2021_entegra_aspire_44r'),
  ('user_patches_file', '/var/lib/coachiq/user_patches.json'),
  ('base_model_hash', 'sha256:abc123...');  -- For detecting updates
```

**Layer 7: User Preferences (SQLite)**
```sql
-- /var/lib/coachiq/user/coachiq.db - User cosmetic preferences
CREATE TABLE user_settings (
    key TEXT PRIMARY KEY,
    value TEXT,
    last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO user_settings VALUES
  ('entity.light.living_room_main.display_name', 'Main Living Area'),
  ('entity.tank.fresh_water.show_percentage', 'true'),
  ('ui.dashboard.group_lights_by_room', 'true');
```

**Layer 8: Secrets & Runtime Overrides (Environment Variables)**
```bash
# Environment variables for secrets only
COACHIQ_SECURITY__SECRET_KEY_FILE=/run/secrets/secret_key
COACHIQ_AUTH__JWT_SECRET_FILE=/run/secrets/jwt_secret
COACHIQ_NOTIFICATIONS__SMTP__PASSWORD_FILE=/run/secrets/smtp_password

# Runtime overrides for emergency situations
COACHIQ_SERVER__DEBUG=true
COACHIQ_LOGGING__LEVEL=DEBUG
COACHIQ_CONFIG_FILE=/custom/path/config.toml
```

**Configuration Loading Implementation**:
```python
# In backend/core/config.py - Enhanced 8-layer loading strategy with read-only system protection
class ConfigurationLoader:
    def load_settings(self) -> AppConfig:
        """Load configuration with 8-layer hierarchical precedence and read-only system protection."""

        # 1. Load Core Protocol Specification (READ-ONLY system files)
        rvc_protocol = self._load_json('/var/lib/coachiq/config/rvc.json')
        self._validate_schema_version(rvc_protocol, min_version="2.0")
        self._verify_read_only_protection('/var/lib/coachiq/config/rvc.json')

        # 2. Determine active coach model
        active_model = (
            self.sqlite.get('system.active_coach_model') or
            self.system_config.get('coach.default_model') or
            'generic_rv'
        )

        # 3. Load base coach model definition (READ-ONLY system files)
        model_path = f'/var/lib/coachiq/config/models/{active_model}.yml'
        base_coach_model = self._load_yaml(model_path)
        self._validate_schema_version(base_coach_model, min_version="1.0")
        self._verify_read_only_protection(model_path)

        # 4. Apply protocol extensions from coach model
        if 'protocol_extensions' in base_coach_model:
            rvc_protocol = self._merge_protocol_extensions(
                rvc_protocol, base_coach_model['protocol_extensions']
            )

        # 5. Apply user structural customizations (WRITABLE user files)
        final_coach_model = base_coach_model
        patches_file = self.sqlite.get('system.user_patches_file') or '/var/lib/coachiq/user/user_patches.json'
        if Path(patches_file).exists():
            try:
                patches = self._load_json(patches_file)
                final_coach_model = self._apply_json_patches(base_coach_model, patches)
            except Exception as e:
                logger.error(f"Failed to apply user patches: {e}")
                self._flag_configuration_issue("user_patches_failed")

        # 6. Load system settings (READ-ONLY Nix-deployed)
        system_config = self._load_toml('/var/lib/coachiq/config/system.toml')
        self._verify_read_only_protection('/var/lib/coachiq/config/system.toml')

        # 7. Load user config overrides (WRITABLE user overrides)
        user_config_overrides = {}
        user_override_path = '/var/lib/coachiq/user/config-overrides.toml'
        if Path(user_override_path).exists():
            try:
                user_config_overrides = self._load_toml(user_override_path)
                logger.info(f"Loaded user config overrides from {user_override_path}")
            except Exception as e:
                logger.warning(f"Failed to load user config overrides: {e}")

        # 8. Merge system config with user overrides (user takes precedence)
        final_system_config = self._merge_configs(system_config, user_config_overrides)

        # 9. Load user preferences from SQLite
        user_preferences = self.sqlite.get_all_user_settings()

        # 10. Apply environment variable overrides (secrets only)
        env_overrides = self._load_env_overrides()

        return AppConfig(
            protocol=rvc_protocol,
            model=final_coach_model,
            system=final_system_config,
            user_overrides=user_config_overrides,
            preferences=user_preferences,
            secrets=env_overrides
        )

    def _verify_read_only_protection(self, file_path: str) -> None:
        """Verify that system config files have read-only permissions (444)."""
        try:
            path = Path(file_path)
            if path.exists():
                # Check if file is read-only (444 permissions)
                stat_info = path.stat()
                permissions = oct(stat_info.st_mode)[-3:]

                if permissions != '444':
                    logger.warning(f"System config file {file_path} has incorrect permissions: {permissions} (expected 444)")
                    # Attempt to fix permissions if we have write access to parent directory
                    try:
                        path.chmod(0o444)
                        logger.info(f"Fixed permissions for {file_path} to read-only (444)")
                    except PermissionError:
                        logger.warning(f"Cannot fix permissions for {file_path} - system may be compromised")
                else:
                    logger.debug(f"System config file {file_path} has correct read-only permissions")
        except Exception as e:
            logger.warning(f"Cannot verify permissions for {file_path}: {e}")

    def _merge_configs(self, system_config: dict, user_overrides: dict) -> dict:
        """
        Merge system configuration with user overrides.

        User overrides take precedence over system settings.
        Supports deep merging for nested dictionaries.
        """
        import copy

        # Start with system config as base
        merged = copy.deepcopy(system_config)

        # Apply user overrides recursively
        def deep_merge(base: dict, override: dict) -> dict:
            for key, value in override.items():
                if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                    # Recursively merge nested dictionaries
                    base[key] = deep_merge(base[key], value)
                else:
                    # Override the value
                    base[key] = value
                    logger.debug(f"User override applied: {key} = {value}")
            return base

        return deep_merge(merged, user_overrides)

    def _apply_json_patches(self, base_model: dict, patches: list) -> dict:
        """Apply JSON Patch operations with error handling."""
        import jsonpatch
        try:
            patch = jsonpatch.JsonPatch(patches)
            return patch.apply(base_model)
        except jsonpatch.JsonPatchException as e:
            logger.error(f"Invalid JSON patch: {e}")
            raise

    def _validate_schema_version(self, config: dict, min_version: str) -> None:
        """Validate schema version compatibility."""
        schema_version = config.get('schema_version')
        if not schema_version:
            raise ValueError("Missing schema_version in configuration file")

        # Semantic version comparison logic here
        if self._version_less_than(schema_version, min_version):
            raise ValueError(f"Unsupported schema version {schema_version}, minimum required: {min_version}")
```

**1.3 Entity State Persistence Model**
```python
# New file: backend/models/entity.py
from datetime import UTC, datetime
from sqlalchemy import JSON, DateTime, String, Index
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base

class EntityState(Base):
    """Persists the last known state of RV-C entities for restart recovery."""
    __tablename__ = "entity_states"

    entity_id: Mapped[str] = mapped_column(
        String(255),
        primary_key=True,
        comment="Unique identifier (e.g., 'inverter.1')"
    )

    state: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        comment="Complete entity state as JSON"
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
        index=True,
        comment="Last state update timestamp"
    )

    __table_args__ = (
        Index('ix_entity_states_updated_at', 'updated_at'),
    )
```

**1.4 Grand Unification Alembic Migration**
```bash
# Generate comprehensive migration with quality checks
poetry run alembic revision --autogenerate -m "unify_schemas_and_add_entity_state"

# Verify migration quality
poetry run pyright backend/models/       # Type check models
poetry run ruff check backend/models/    # Lint models
poetry run pytest tests/models/          # Test models
```

The generated migration will include:
- All authentication tables from `models/auth.py`
- New `entity_states` table
- Any missing analytics tables
- Proper indexes and constraints

**Quality Requirements for Phase 1:**
- All new SQLAlchemy models must pass type checking
- Migration scripts must be tested in isolated test database
- Configuration loader must have 100% test coverage
- All file I/O operations must have proper error handling

#### Phase 2: Core Logic Refactoring (Weeks 2-3)

**2.1 Application Startup Sequence**
```python
# In main.py - New startup sequence
async def startup_application():
    """Initialize application with fail-fast persistence validation."""

    # 1. Load configuration with mandatory validation
    try:
        settings = get_settings()
    except ValidationError as e:
        logger.critical("FATAL: Configuration validation failed")
        for error in e.errors():
            if error["loc"] == ("persistence", "data_dir"):
                logger.critical(
                    "COACHIQ_PERSISTENCE__DATA_DIR is required and must point to your USB SSD mount. "
                    f"Example: COACHIQ_PERSISTENCE__DATA_DIR=/media/pi/COACHIQ_SSD"
                )
            else:
                logger.critical(f"Configuration error: {error}")
        raise SystemExit(1)

    # 2. Initialize logging
    configure_logging(settings.logging)

    # 3. Backward compatibility check
    deprecated_enabled = os.getenv("COACHIQ_PERSISTENCE__ENABLED")
    if deprecated_enabled is not None:
        logger.critical(
            "FATAL: COACHIQ_PERSISTENCE__ENABLED is deprecated. "
            "Persistence is now mandatory and cannot be disabled. "
            "Please remove this environment variable and ensure "
            "COACHIQ_PERSISTENCE__DATA_DIR points to your USB SSD."
        )
        raise SystemExit(1)

    # 4. Initialize persistence (configuration already validated)
    try:
        # Create database directory structure (standardized on /var/lib/coachiq)
        data_dir = Path("/var/lib/coachiq")
        db_dir = data_dir / "database"
        backup_dir = data_dir / "backups"
        db_dir.mkdir(exist_ok=True)
        backup_dir.mkdir(exist_ok=True)

        # Create async engine with SQLite optimizations for USB SSD
        db_path = data_dir / "coachiq.db"  # Main database file
        engine = create_async_engine(
            f"sqlite+aiosqlite:///{db_path}",
            echo=settings.debug,
            pool_recycle=3600,
            pool_pre_ping=True,  # Validate connections
        )

        # Enable SQLite WAL mode for better concurrency
        @event.listens_for(engine.sync_engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA temp_store=MEMORY")
            cursor.close()

        # Run Alembic migrations to head
        await run_alembic_upgrade(engine)

    except Exception as e:
        logger.critical(f"FATAL: Persistence initialization failed: {e}")
        raise SystemExit(1)

    # 4. Initialize all other services
    await initialize_feature_manager(engine)
    await initialize_auth_manager(engine)
    await initialize_analytics_manager(engine)
    await initialize_entity_manager(engine)

    # 5. Start web server
    return engine
```

**Quality Requirements for Phase 2:**
```bash
# Required checks after each core logic change
poetry run pyright backend/core/              # Type check core modules
poetry run pyright backend/services/          # Type check services
poetry run pytest tests/core/ -v              # Test core functionality
poetry run pytest tests/services/ -v          # Test service integrations
poetry run pytest --cov=backend/core --cov=backend/services --cov-report=term-missing
```

**Integration Testing Requirements:**
- All new async methods must have comprehensive test coverage
- Entity manager persistence must be tested with real SQLite files
- Startup sequence must be tested with various configuration scenarios
- Database connection failures must be handled gracefully with proper logging

**2.2 Entity State Persistence Integration**
```python
# In backend/core/entity_manager.py
class EntityManager:
    """Enhanced with persistent state management."""

    def __init__(self, engine: AsyncEngine):
        self.engine = engine
        self.entities: dict[str, Entity] = {}
        self._dirty_entities: set[str] = set()
        self._persistence_task: asyncio.Task | None = None

    async def startup(self):
        """Load persisted entity states on startup."""
        async with AsyncSession(self.engine) as session:
            result = await session.execute(select(EntityState))
            for entity_state in result.scalars():
                # Restore entity from persisted state
                self.entities[entity_state.entity_id] = Entity.from_dict(
                    entity_state.entity_id,
                    entity_state.state
                )

        # Start background persistence task
        self._persistence_task = asyncio.create_task(self._persistence_worker())

    async def update_entity_state(self, entity_id: str, new_state: dict):
        """Update entity state with debounced persistence."""
        # Update in-memory immediately
        if entity_id in self.entities:
            self.entities[entity_id].update_state(new_state)

        # Mark for persistence
        self._dirty_entities.add(entity_id)

    async def _persistence_worker(self):
        """Background task for debounced entity state persistence."""
        while True:
            try:
                await asyncio.sleep(0.5)  # 500ms debounce for SSD performance

                if not self._dirty_entities:
                    continue

                # Batch write dirty entities
                dirty_ids = list(self._dirty_entities)
                self._dirty_entities.clear()

                async with AsyncSession(self.engine) as session:
                    for entity_id in dirty_ids:
                        if entity_id in self.entities:
                            entity = self.entities[entity_id]

                            # Upsert entity state
                            stmt = insert(EntityState).values(
                                entity_id=entity_id,
                                state=entity.to_dict(),
                                updated_at=datetime.now(UTC)
                            )
                            stmt = stmt.on_conflict_do_update(
                                index_elements=['entity_id'],
                                set_=dict(
                                    state=stmt.excluded.state,
                                    updated_at=stmt.excluded.updated_at
                                )
                            )
                            await session.execute(stmt)

                    await session.commit()

            except Exception as e:
                logger.error(f"Entity persistence error: {e}")
```

#### Phase 3: Service Integration (Week 3)

**3.1 Authentication Manager Integration**
```python
# In backend/services/auth_manager.py
class AuthManager:
    """Simplified with mandatory persistence."""

    def __init__(self, engine: AsyncEngine):
        self.engine = engine
        # Remove all in-memory fallback logic

    async def create_user(self, user_data: dict) -> User:
        """Create user with direct database storage."""
        async with AsyncSession(self.engine) as session:
            user = User(**user_data)
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user
```

**Quality Requirements for Phase 3:**
```bash
# Required checks for service integration
poetry run pyright backend/services/          # Type check all services
poetry run pytest tests/services/ -v --cov=backend/services --cov-report=term-missing
poetry run pytest tests/integrations/ -v     # Integration tests

# API endpoint validation
cd frontend && npm run typecheck              # Frontend type validation
cd frontend && npm run test                   # Frontend unit tests
cd frontend && npm run build                  # Verify frontend builds
```

**Service Integration Testing Requirements:**
- All service constructors must validate required dependencies
- Database session handling must be tested for connection failures
- Service shutdown must be tested for proper resource cleanup
- API response schemas must be validated with both backend and frontend

**3.2 Analytics Manager Integration**
```python
# In backend/services/analytics_storage_service.py
class AnalyticsStorageService:
    """Simplified analytics with mandatory SQLite storage."""

    def __init__(self, engine: AsyncEngine):
        self.engine = engine
        # Remove AnalyticsMemoryStorage fallback

    async def store_metric(self, metric: AnalyticsMetric):
        """Store metric directly to SQLite."""
        async with AsyncSession(self.engine) as session:
            session.add(metric)
            await session.commit()
```

#### Phase 4: Code Cleanup & Testing (Week 4)

**4.1 Code Quality Requirements**

All phases must maintain strict code quality standards:

**Backend Quality Checks (Required for each commit):**
```bash
# Type checking with Pyright
poetry run pyright backend

# Linting with Ruff
poetry run ruff check backend
poetry run ruff format backend

# Testing with pytest
poetry run pytest --cov=backend --cov-report=term-missing

# Pre-commit hooks
poetry run pre-commit run --all-files
```

**Frontend Quality Checks (Required for each commit):**
```bash
cd frontend

# Type checking with TypeScript
npm run typecheck

# Linting with ESLint
npm run lint

# Testing with Vitest
npm run test

# Build verification
npm run build
```

**Mandatory Quality Gates:**
1. **Zero type errors** - All TypeScript and Python type checking must pass
2. **Zero lint violations** - All ESLint and Ruff checks must pass
3. **Minimum 80% test coverage** - Both backend and frontend
4. **Successful builds** - Frontend build must complete without errors
5. **Pre-commit hooks pass** - All formatting and basic checks

**4.2 Remove Optional Persistence Code**
- Delete `backend/services/in_memory_persistence.py`
- Remove all `settings.persistence.enabled` conditional blocks
- Simplify `PersistenceFeature` startup logic
- Update all services to assume persistence is available

**Code Quality During Cleanup:**
```bash
# After each file modification, run quality checks
poetry run pyright backend                    # Type check
poetry run ruff check backend                 # Lint check
poetry run pytest tests/affected_test.py      # Test affected areas
```

**4.2 Testing Strategy with Tiered Configuration**

The new tiered configuration model changes how we approach testing:

```python
# In tests/conftest.py
import tempfile
from pathlib import Path
import pytest
from backend.core.config import Settings, PersistenceSettings

@pytest.fixture
def test_data_dir():
    """Provide temporary directory for test persistence."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        data_dir = Path(tmp_dir)
        (data_dir / "database").mkdir()
        (data_dir / "backups").mkdir()
        yield data_dir

@pytest.fixture
def test_settings(test_data_dir):
    """Provide test configuration with valid persistence settings."""
    # Override settings for testing - no environment variables needed
    persistence = PersistenceSettings(
        data_dir=test_data_dir,
        backup_enabled=False,  # Disable for speed
        cache_size_mb=16       # Minimal for tests
    )

    settings = Settings(persistence=persistence)
    return settings

@pytest.fixture
async def test_db_engine(test_settings):
    """Provide test database engine with file-based SQLite."""
    db_path = test_settings.persistence.data_dir / "database" / "test.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine
    await engine.dispose()

@pytest.fixture
async def entity_manager(test_db_engine):
    """Provide EntityManager with test database."""
    manager = EntityManager(test_db_engine)
    await manager.startup()
    yield manager
    if manager._persistence_task:
        manager._persistence_task.cancel()

# Integration test that validates full configuration
def test_persistence_settings_validation():
    """Test that persistence validation works correctly."""
    # This should fail - no data_dir provided
    with pytest.raises(ValidationError):
        PersistenceSettings()

    # This should fail - directory doesn't exist
    with pytest.raises(ValidationError):
        PersistenceSettings(data_dir="/nonexistent/path")
```

**Key Testing Changes:**
- Tests use **real SQLite files** (not in-memory) to match production behavior
- **No environment variable mocking** needed for persistence enable/disable
- **Temporary directories** provided automatically for each test
- **Configuration objects** created directly in tests for precision

### Performance Optimizations

#### SQLite Configuration
```python
# SQLite setup optimized for Raspberry Pi with USB SSD
@event.listens_for(engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")        # Better concurrency
    cursor.execute("PRAGMA synchronous=NORMAL")      # Balanced durability/performance
    cursor.execute("PRAGMA temp_store=MEMORY")       # Faster temp operations
    cursor.execute("PRAGMA mmap_size=134217728")     # 128MB memory mapping (SSD can handle more)
    cursor.execute("PRAGMA cache_size=4000")         # Larger cache for better performance
    cursor.execute("PRAGMA wal_autocheckpoint=1000") # Less frequent checkpoints (SSD friendly)
    cursor.execute("PRAGMA optimize")               # Periodic optimization
    cursor.execute("PRAGMA busy_timeout=30000")      # 30s timeout for busy database
    cursor.close()
```

#### Entity State Debouncing (USB SSD Optimized)
- **Write Frequency**: 500ms debounced writes (SSD can handle frequent writes)
- **Batch Operations**: Group multiple entity updates in single transaction
- **Memory-First**: Immediate in-memory updates for API responsiveness
- **Background Persistence**: Single async worker for resource efficiency
- **SSD Performance**: Leverage SSD speed for responsive persistence

### Nix Flake Deployment Strategy

#### Enhanced NixOS Module Configuration

**Storage Profile-Based Deployment** (with standardized `/var/lib/coachiq` storage):

```nix
# flake.nix - Enhanced NixOS module
{
  services.coachiq = {
    enable = true;

    # NEW: Explicit storage strategy selection
    storageProfile = "ssd";  # Options: "ssd", "sdcard", "custom"

    settings = {
      # Standardized data directory - always /var/lib/coachiq
      persistence = {
        dataDir = "/var/lib/coachiq";  # Standard Linux service data location
      };

      # Coach model configuration
      coach = {
        defaultModel = "2021_entegra_aspire_44r";
        modelDirectory = "/var/lib/coachiq/config/models";
      };

      # Server settings with profile-based defaults
      server = {
        port = 8080;
        debug = false;
      };

      # Storage profile automatically sets appropriate defaults
      logging.logToFile = lib.mkDefault (storageProfile != "sdcard");
      performanceAnalytics.telemetryCollectionIntervalSeconds =
        lib.mkDefault (if storageProfile == "sdcard" then 60.0 else 5.0);
    };
  };
}
```

#### Storage Profile Implementations

**SSD Profile (High Performance)**:
```nix
# Optimized for USB SSD deployment (direct mount)
services.coachiq = {
  storageProfile = "ssd";
  settings = {
    persistence = {
      dataDir = "/var/lib/coachiq";  # Direct mount point for USB SSD
      sqlitePragmas = {
        journal_mode = "WAL";
        synchronous = "NORMAL";
        cache_size = 4000;
      };
    };
    # High-frequency analytics and logging enabled
  };
};

# Direct mount USB SSD to standard service data directory
fileSystems."/var/lib/coachiq" = {
  device = "/dev/disk/by-label/COACHIQ_SSD";
  fsType = "ext4";
  options = [ "defaults" "rw" ];
};
```

**SD Card Profile (Durability Focus)**:
```nix
# Minimizes writes, uses tmpfs + periodic sync
services.coachiq = {
  storageProfile = "sdcard";
  settings = {
    persistence = {
      dataDir = "/var/lib/coachiq";  # Lives in tmpfs
      syncIntervalMinutes = 15;  # Configurable data loss window
      sqlitePragmas = {
        journal_mode = "MEMORY";  # Aggressive for tmpfs
        synchronous = "OFF";
      };
    };
    # Reduced-frequency analytics to minimize writes
  };
};
```

#### Generated Configuration File Approach

**NixOS Module Enhancement**:
```nix
# In nixosModules.coachiq
let
  # Generate comprehensive config file instead of dozens of env vars
  configFile = pkgs.writeTextFile {
    name = "coachiq-config.json";
    text = builtins.toJSON {
      inherit (config.coachiq) settings;
      storageProfile = config.coachiq.storageProfile;
    };
  };
in {
  systemd.services.coachiq = {
    environment = {
      # Single environment variable replaces dozens
      COACHIQ_CONFIG_FILE = configFile;
    };

    serviceConfig = {
      ExecStartPre = "${config.coachiq.package}/bin/coachiq-pre-start-hook";
      ExecStart = "${config.coachiq.package}/bin/coachiq-daemon";
      ExecStopPost = lib.mkIf (config.coachiq.storageProfile == "sdcard")
        "${config.coachiq.package}/bin/coachiq-sync-database";
    };
  };

  # SD Card specific: tmpfs mount + sync timer
  systemd.mounts = lib.mkIf (config.coachiq.storageProfile == "sdcard") [{
    what = "tmpfs";
    where = "${config.coachiq.settings.persistence.dataDir}/database";
    type = "tmpfs";
    options = "defaults,size=128M,uid=coachiq,gid=coachiq,mode=0755";
  }];

  systemd.timers.coachiq-db-sync = lib.mkIf (config.coachiq.storageProfile == "sdcard") {
    wantedBy = [ "timers.target" ];
    timerConfig = {
      OnCalendar = "*:0/${toString config.coachiq.settings.persistence.syncIntervalMinutes}";
      Persistent = true;
    };
  };
}
```

### SD Card Support Strategy

#### Mandatory Persistence with Write Protection

**The Challenge**: Maintain mandatory persistence while protecting SD cards from excessive writes.

**Solution**: tmpfs + Orchestrated Sync Strategy
```bash
# SD Card deployment architecture:
# 1. Database runs in RAM (tmpfs) for performance
# 2. Periodic sync to SD card for persistence
# 3. Startup loads from SD card to RAM
# 4. Shutdown saves from RAM to SD card

/var/lib/coachiq/
├── database/          # tmpfs mount (RAM)
│   └── coachiq.db    # Live database
├── database-persist/ # SD card storage
│   └── coachiq.db    # Persisted copy
└── backups/          # SD card storage
    └── *.db.backup   # Automated backups
```

#### Pre-Start Hook (Database Migration + Load)
```bash
#!/bin/bash
# coachiq-pre-start-hook
set -euo pipefail

CONFIG_FILE="${COACHIQ_CONFIG_FILE}"
STORAGE_PROFILE=$(jq -r '.storageProfile' "$CONFIG_FILE")
DATA_DIR=$(jq -r '.settings.persistence.dataDir' "$CONFIG_FILE")

if [[ "$STORAGE_PROFILE" == "sdcard" ]]; then
    echo "SD Card mode: Loading database from persistent storage..."

    PERSIST_DIR="${DATA_DIR}/database-persist"
    LIVE_DIR="${DATA_DIR}/database"

    mkdir -p "$PERSIST_DIR" "$LIVE_DIR"

    # Load existing database into tmpfs if it exists
    if [[ -f "${PERSIST_DIR}/coachiq.db" ]]; then
        cp "${PERSIST_DIR}/coachiq.db" "${LIVE_DIR}/coachiq.db"
        echo "Database loaded from persistent storage"
    else
        echo "No existing database found, will create new"
    fi
fi

# Run Alembic migrations (works for both SSD and SD card)
echo "Running database migrations..."
cd /var/lib/coachiq
coachiq-migrate upgrade head

echo "Pre-start hook completed successfully"
```

### Deployment Configuration Examples

#### Nix Flake (Primary Deployment)

**Your SSD Deployment**:
```nix
# /etc/nixos/configuration.nix
{ config, pkgs, ... }:
{
  imports = [
    inputs.coachiq.nixosModules.coachiq
  ];

  services.coachiq = {
    enable = true;
    storageProfile = "ssd";

    settings = {
      persistence.dataDir = "/var/lib/coachiq";  # Direct USB SSD mount
      server = {
        port = 8080;
        host = "0.0.0.0";
      };
      can.interfaces = [ "can0" "can1" ];
      features = {
        enableSystemAnalytics = true;
        enablePredictiveMaintenance = true;
      };
    };
  };

  # Direct mount USB SSD to service data directory
  fileSystems."/var/lib/coachiq" = {
    device = "/dev/disk/by-label/COACHIQ_SSD";
    fsType = "ext4";
    options = [ "defaults" "rw" ];
  };
}
```

**SD Card User Deployment**:
```nix
# /etc/nixos/configuration.nix
{ config, pkgs, ... }:
{
  services.coachiq = {
    enable = true;
    storageProfile = "sdcard";  # Automatically configures tmpfs + sync

    settings = {
      persistence = {
        dataDir = "/var/lib/coachiq";
        syncIntervalMinutes = 30;  # User choice: 30min data loss window
      };
      # Reduced-frequency defaults automatically applied
      performanceAnalytics.telemetryCollectionIntervalSeconds = 120.0;
      logging.logToFile = false;  # Use systemd journal instead
    };
  };
}
```

#### Debian Package (Secondary Deployment)

For users preferring traditional Raspberry Pi OS deployments:

```bash
# Install via APT repository (future)
echo "deb [trusted=yes] https://apt.coachiq.dev/ stable main" | \
  sudo tee /etc/apt/sources.list.d/coachiq.list

sudo apt update
sudo apt install coachiq

# Configure via environment variables (legacy support)
sudo systemctl edit coachiq
```

```ini
# /etc/systemd/system/coachiq.service.d/override.conf
[Service]
Environment="COACHIQ_PERSISTENCE__DATA_DIR=/media/coachiq-ssd"
Environment="COACHIQ_STORAGE_PROFILE=ssd"
```

#### Development/Testing Override

```bash
# For development with Nix
nix develop
export COACHIQ_CONFIG_FILE=$(mktemp)
cat > $COACHIQ_CONFIG_FILE << EOF
{
  "storageProfile": "custom",
  "settings": {
    "persistence": {
      "dataDir": "/tmp/coachiq-dev",
      "backupEnabled": false
    },
    "server": {
      "debug": true,
      "port": 8081
    }
  }
}
EOF

# Start development server
poetry run python run_server.py
```

### Nix Flake Migration Steps

#### Phase 1: Enhanced NixOS Module
Update `flake.nix` to support the new storage profile system:

```nix
# Enhanced nixosModules.coachiq in flake.nix
{ config, lib, pkgs, ... }:
let
  cfg = config.services.coachiq;

  # Generate config file from Nix settings
  configFile = pkgs.writeTextFile {
    name = "coachiq-config.json";
    text = builtins.toJSON {
      storageProfile = cfg.storageProfile;
      settings = cfg.settings;
    };
  };

  # Pre-start hook script
  preStartHook = pkgs.writeShellScript "coachiq-pre-start" ''
    set -euo pipefail

    CONFIG_FILE="${configFile}"
    STORAGE_PROFILE=$(${pkgs.jq}/bin/jq -r '.storageProfile' "$CONFIG_FILE")
    DATA_DIR=$(${pkgs.jq}/bin/jq -r '.settings.persistence.dataDir' "$CONFIG_FILE")

    if [[ "$STORAGE_PROFILE" == "sdcard" ]]; then
      echo "SD Card mode: Loading database from persistent storage..."
      PERSIST_DIR="${DATA_DIR}/database-persist"
      LIVE_DIR="${DATA_DIR}/database"

      mkdir -p "$PERSIST_DIR" "$LIVE_DIR"

      if [[ -f "${PERSIST_DIR}/coachiq.db" ]]; then
        cp "${PERSIST_DIR}/coachiq.db" "${LIVE_DIR}/coachiq.db"
        echo "Database loaded from persistent storage"
      fi
    fi

    echo "Running database migrations..."
    ${cfg.package}/bin/coachiq-migrate upgrade head
  '';

in {
  options.services.coachiq = {
    enable = lib.mkEnableOption "CoachIQ RV Management System";

    storageProfile = lib.mkOption {
      type = lib.types.enum [ "ssd" "sdcard" "custom" ];
      default = "ssd";
      description = ''
        Storage optimization profile:
        - ssd: High-performance mode for USB SSD storage
        - sdcard: Write-minimized mode with tmpfs + periodic sync
        - custom: Manual configuration of all persistence settings
      '';
    };

    settings = lib.mkOption {
      type = lib.types.attrsOf lib.types.anything;
      default = {};
      description = "CoachIQ application settings";
    };
  };

  config = lib.mkIf cfg.enable {
    systemd.services.coachiq = {
      description = "CoachIQ RV Management System";
      wantedBy = [ "multi-user.target" ];
      after = [ "network.target" ];

      environment = {
        COACHIQ_CONFIG_FILE = configFile;
      };

      serviceConfig = {
        Type = "simple";
        User = "coachiq";
        Group = "coachiq";
        ExecStartPre = preStartHook;
        ExecStart = "${cfg.package}/bin/coachiq-daemon";
        Restart = "always";
        RestartSec = "10";
      };
    };

    # SD Card specific configuration
    systemd.mounts = lib.mkIf (cfg.storageProfile == "sdcard") [{
      what = "tmpfs";
      where = "${cfg.settings.persistence.dataDir}/database";
      type = "tmpfs";
      options = "defaults,size=128M,uid=coachiq,gid=coachiq,mode=0755";
      wantedBy = [ "coachiq.service" ];
      before = [ "coachiq.service" ];
    }];

    # Periodic sync service for SD card mode
    systemd.services.coachiq-db-sync = lib.mkIf (cfg.storageProfile == "sdcard") {
      description = "Sync CoachIQ database from tmpfs to persistent storage";
      serviceConfig = {
        Type = "oneshot";
        User = "coachiq";
        ExecStart = pkgs.writeShellScript "coachiq-db-sync" ''
          set -euo pipefail
          DATA_DIR="${cfg.settings.persistence.dataDir}"
          PERSIST_DIR="$DATA_DIR/database-persist"
          LIVE_DIR="$DATA_DIR/database"

          mkdir -p "$PERSIST_DIR"

          if [[ -f "$LIVE_DIR/coachiq.db" ]]; then
            cp "$LIVE_DIR/coachiq.db" "$PERSIST_DIR/coachiq.db"
            echo "Database synced to persistent storage"
          fi
        '';
      };
    };

    systemd.timers.coachiq-db-sync = lib.mkIf (cfg.storageProfile == "sdcard") {
      description = "Timer for CoachIQ database sync";
      wantedBy = [ "timers.target" ];
      timerConfig = {
        OnCalendar = "*:0/${toString (cfg.settings.persistence.syncIntervalMinutes or 15)}";
        Persistent = true;
      };
    };

    # Set up proper file permissions for read-only system config protection
    systemd.tmpfiles.rules = [
      # Create directory structure with proper ownership
      "d /var/lib/coachiq 0755 coachiq coachiq -"
      "d /var/lib/coachiq/config 0755 coachiq coachiq -"
      "d /var/lib/coachiq/config/models 0755 coachiq coachiq -"
      "d /var/lib/coachiq/user 0755 coachiq coachiq -"
      "d /var/lib/coachiq/backups 0755 coachiq coachiq -"

      # Deploy system config files with read-only permissions (444)
      "C /var/lib/coachiq/config/system.toml 0444 coachiq coachiq - ${configFile}"
      "C /var/lib/coachiq/config/rvc.json 0444 coachiq coachiq - ${cfg.package}/share/coachiq/rvc.json"

      # Coach model files (read-only directory and files)
      "C /var/lib/coachiq/config/models 0555 coachiq coachiq - ${cfg.package}/share/coachiq/models"

      # Ensure user files have proper writable permissions
      "Z /var/lib/coachiq/user 0755 coachiq coachiq -"
    ];

    # Apply storage profile defaults
    services.coachiq.settings = lib.mkMerge [
      # Base defaults
      {
        persistence.dataDir = lib.mkDefault "/var/lib/coachiq";
        server.port = lib.mkDefault 8080;
      }

      # SSD profile defaults
      (lib.mkIf (cfg.storageProfile == "ssd") {
        persistence.sqlitePragmas = lib.mkDefault {
          journal_mode = "WAL";
          synchronous = "NORMAL";
          cache_size = 4000;
        };
        logging.logToFile = lib.mkDefault true;
        performanceAnalytics.telemetryCollectionIntervalSeconds = lib.mkDefault 5.0;
      })

      # SD Card profile defaults
      (lib.mkIf (cfg.storageProfile == "sdcard") {
        persistence = lib.mkDefault {
          syncIntervalMinutes = 15;
          sqlitePragmas = {
            journal_mode = "MEMORY";
            synchronous = "OFF";
          };
        };
        logging.logToFile = lib.mkDefault false;
        performanceAnalytics.telemetryCollectionIntervalSeconds = lib.mkDefault 60.0;
      })
    ];

    users.users.coachiq = {
      isSystemUser = true;
      group = "coachiq";
      home = cfg.settings.persistence.dataDir;
      createHome = true;
    };

    users.groups.coachiq = {};
  };
}
```

### Migration Deployment

#### Pre-Deployment Checklist

**Code Quality Verification:**
- [ ] All backend type checks pass: `poetry run pyright backend`
- [ ] All frontend type checks pass: `cd frontend && npm run typecheck`
- [ ] All linting passes: `poetry run ruff check backend` and `cd frontend && npm run lint`
- [ ] All tests pass with 80%+ coverage: `poetry run pytest --cov=backend --cov-report=term-missing`
- [ ] Frontend tests pass: `cd frontend && npm run test`
- [ ] Frontend builds successfully: `cd frontend && npm run build`
- [ ] Pre-commit hooks pass: `poetry run pre-commit run --all-files`

**Deployment Verification:**
- [ ] Database backup created
- [ ] Alembic migration tested in staging
- [ ] Performance benchmarks verified
- [ ] Rollback plan documented

#### Automated Quality Pipeline

**GitHub Actions Integration:**
```yaml
# .github/workflows/quality-check.yml
name: Code Quality Check
on: [push, pull_request]

jobs:
  backend-quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install Poetry
        uses: snok/install-poetry@v1
      - name: Install dependencies
        run: poetry install
      - name: Type check with Pyright
        run: poetry run pyright backend
      - name: Lint with Ruff
        run: poetry run ruff check backend
      - name: Format check with Ruff
        run: poetry run ruff format --check backend
      - name: Test with pytest
        run: poetry run pytest --cov=backend --cov-report=xml
      - name: Upload coverage reports
        uses: codecov/codecov-action@v3

  frontend-quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '18'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json
      - name: Install dependencies
        run: cd frontend && npm ci
      - name: Type check with TypeScript
        run: cd frontend && npm run typecheck
      - name: Lint with ESLint
        run: cd frontend && npm run lint
      - name: Test with Vitest
        run: cd frontend && npm run test
      - name: Build frontend
        run: cd frontend && npm run build
```

**Local Development Quality Script:**
```bash
#!/bin/bash
# scripts/quality-check.sh - Run all quality checks locally

set -e

echo "🔍 Running Backend Quality Checks..."
poetry run pyright backend
poetry run ruff check backend
poetry run ruff format backend
poetry run pytest --cov=backend --cov-report=term-missing

echo "🔍 Running Frontend Quality Checks..."
cd frontend
npm run typecheck
npm run lint
npm run test
npm run build
cd ..

echo "✅ All quality checks passed!"
```

#### Deployment Steps
1. **Quality Gate**: Run full quality pipeline: `./scripts/quality-check.sh`
2. **Stop Application**: Graceful shutdown to ensure data consistency
3. **Backup Database**: Create manual backup of existing SQLite file
4. **Deploy Code**: Update application with new persistence logic
5. **Start Application**: Automatic Alembic migration on startup
6. **Verify Migration**: Check all tables created and data intact
7. **Post-Deploy Quality Check**: Verify all services respond correctly
8. **Monitor Performance**: Watch for I/O bottlenecks

#### Rollback Plan
```bash
# If migration fails
cp /var/lib/coachiq/database/coachiq.db.backup /var/lib/coachiq/database/coachiq.db
git checkout previous_release_tag
systemctl restart coachiq
```

### Risk Assessment & Mitigation

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Migration script failure | Low | High | Comprehensive testing, automated backups |
| USB SSD disconnect | Low | High | Proper mounting, USB power management settings |
| Power loss during migration | Low | Critical | WAL mode, UPS recommended for Pi |
| Performance degradation | Very Low | Low | SSD-optimized SQLite settings, fast write performance |
| Startup failures | Low | High | Fail-fast with clear error messages |

### Success Metrics

#### Architectural Improvements
- [ ] 50%+ reduction in persistence-related code complexity
- [ ] Elimination of silent feature failures
- [ ] 100% test coverage for persistence layer
- [ ] Single source of truth for all data

#### Performance Targets (Pi + USB SSD Context)
- [ ] <100ms p95 API response time (SSD enables faster responses)
- [ ] <512MB memory usage on Raspberry Pi 4 (leaving room for OS)
- [ ] <10MB/hour SQLite file growth under normal load
- [ ] Zero data loss during graceful shutdowns
- [ ] Startup time <20 seconds on Pi 4 (SSD boot speed)
- [ ] Database operations <50ms p95

### Post-Migration Maintenance

#### Database Maintenance (USB SSD Context)
- **Backup Strategy**: Daily automated backups with 30-day retention (SSD has ample storage)
- **Vacuum Schedule**: Weekly `VACUUM` operations during low usage hours
- **SSD Health Monitoring**: Track database file size and SSD health
- **Power Loss Protection**: WAL mode ensures database integrity during power events
- **USB Mount Monitoring**: Ensure SSD remains properly mounted
- **Migration Testing**: Automated testing on Pi hardware before deployment

#### Future Enhancements (SSD Deployment Ready)
- **Backup to Cloud**: Optional cloud backup when internet available
- **Data Export**: Export historical data for analysis or backup
- **Maintenance Dashboard**: Simple UI for database and SSD health monitoring
- **SSD Redundancy**: Optional second SSD for backup/failover

### Conclusion

This migration plan transforms CoachIQ from an optionally-persistent system to a robust, mandatory-persistence architecture optimized for single-user motorhome deployments on Raspberry Pi hardware. The phased approach minimizes risk while delivering significant architectural improvements including simplified code, better performance, and eliminated silent failures.

**Key adaptations for the motorhome/Pi + USB SSD context:**
- **SSD Performance**: Optimized SQLite settings for SSD speed and durability
- **Resource Constraints**: Memory-conscious configuration suitable for Pi hardware
- **Power Resilience**: WAL mode protection against sudden power loss
- **Simplified Scaling**: No need for multi-user or high-availability features
- **Maintenance-Free**: Automated backup and maintenance suitable for non-technical users
- **Storage Reliability**: USB SSD provides durability and performance for database operations

**Revolutionary Configuration Philosophy:**
- **Tiered Environment Variables**: Clear separation between architectural constants, mandatory runtime config, and optional tuning
- **Fail-Fast Validation**: Comprehensive startup checks prevent silent failures and data loss
- **Deployment Safety**: Impossible to accidentally run without proper storage configuration
- **Backward Compatibility**: Clear migration path with helpful error messages for deprecated settings

**Nix-First Deployment Strategy:**
- **Storage Profiles**: Explicit `ssd`, `sdcard`, `custom` profiles that automatically optimize the entire system
- **Generated Configuration**: Single JSON config file replaces dozens of environment variables
- **SD Card Support**: tmpfs + orchestrated sync strategy maintains mandatory persistence while protecting SD cards
- **Automatic Migration**: systemd hooks handle Alembic migrations and database lifecycle management
- **Type Safety**: NixOS module validation prevents invalid configurations at build time

The plan follows SQLAlchemy 2.0+ best practices, maintains async compatibility, and ensures all business logic remains properly encapsulated in the backend services. Upon completion, CoachIQ will have a solid, reliable foundation perfectly suited for its intended single-instance motorhome deployment environment.

## Complete Environment Variable Categorization

The migration eliminates environment variable proliferation by implementing a three-tiered configuration hierarchy. All existing `COACHIQ_*__` variables have been analyzed and categorized:

### **Category A: Architectural & Feature Configuration**
*Generated config file - defines application behavior and enabled features*

**Environment Variables → Config File Sections:**
- `COACHIQ_FEATURES__ENABLE_*` → `[features]` section
- `COACHIQ_RVC__*`, `COACHIQ_J1939__*`, `COACHIQ_FIREFLY__*`, `COACHIQ_SPARTAN_K2__*` → `[protocols]` section
- `COACHIQ_CAN__INTERFACE_MAPPINGS`, `COACHIQ_CAN__BITRATE` → `[can]` section
- `COACHIQ_API_DOMAINS__*` → `[api_domains]` section
- `COACHIQ_CORS__*` → `[cors]` section
- `COACHIQ_AUTH__ENABLE_*`, `COACHIQ_AUTH__JWT_EXPIRE_MINUTES` → `[authentication]` section

**Example Generated Config:**
```toml
# /etc/coachiq/config.toml - Category A
[features]
enable_system_analytics = true
enable_predictive_maintenance = true
enable_authentication = true

[protocols]
rvc.enabled = true
rvc.enable_encoder = true
j1939.enabled = false
firefly.enabled = false

[can]
interface_mappings = { house = "can0", chassis = "can1" }
bitrate = 500000
auto_reconnect = true

[authentication]
enable_magic_links = true
enable_refresh_tokens = true
jwt_expire_minutes = 15
```

### **Category B: Environmental & Deployment Configuration**
*Config file section - environment-specific, overridable by env vars*

**Environment Variables → Config File Sections:**
- `COACHIQ_SERVER__HOST`, `COACHIQ_SERVER__PORT`, `COACHIQ_SERVER__WORKERS` → `[server]` section
- `COACHIQ_PERSISTENCE__DATA_DIR` → `[persistence]` section (set by storage profile)
- `COACHIQ_LOGGING__LEVEL`, `COACHIQ_LOGGING__LOG_TO_FILE` → `[logging]` section
- `COACHIQ_SECURITY__ALLOWED_IPS`, `COACHIQ_SECURITY__RATE_LIMIT_*` → `[security]` section
- `COACHIQ_PERFORMANCE_ANALYTICS__*` → `[performance_analytics]` section
- Protocol-specific operational settings → respective protocol sections

**Example Config:**
```toml
# /etc/coachiq/config.toml - Category B
[server]
host = "0.0.0.0"
port = 8080
workers = 1
debug = false

[persistence]
data_dir = "/media/coachiq-ssd"
storage_profile = "ssd"
backup_enabled = true

[logging]
level = "INFO"
log_to_file = true

[performance_analytics]
telemetry_collection_interval_seconds = 5.0
cpu_warning_threshold_percent = 80.0
```

### **Category C: Secrets & Runtime Overrides**
*Environment variables only - sensitive data and emergency overrides*

**Retained Environment Variables (15-20 total):**
```bash
# Secrets (file-based preferred)
COACHIQ_SECURITY__SECRET_KEY_FILE=/run/secrets/secret_key
COACHIQ_AUTH__JWT_SECRET_FILE=/run/secrets/jwt_secret
COACHIQ_NOTIFICATIONS__SMTP__PASSWORD_FILE=/run/secrets/smtp_password

# Legacy secrets (deprecated but supported)
COACHIQ_SECURITY__SECRET_KEY=your-secret-key
COACHIQ_AUTH__JWT_SECRET=your-jwt-secret

# Runtime overrides
COACHIQ_SERVER__DEBUG=true  # Emergency debug mode
COACHIQ_LOGGING__LEVEL=DEBUG  # Emergency log level override
COACHIQ_CONFIG_FILE=/custom/path/config.toml

# Admin credentials (single-user mode)
COACHIQ_AUTH__ADMIN_USERNAME=admin
COACHIQ_AUTH__ADMIN_PASSWORD=secure-password

# Runtime notification settings
COACHIQ_NOTIFICATIONS__SMTP__HOST=smtp.gmail.com
COACHIQ_NOTIFICATIONS__SMTP__USERNAME=user@example.com
```

### **Removed/Deprecated Environment Variables**

**Complete Elimination (80+ variables):**
```bash
# REMOVED - Mandatory persistence
COACHIQ_PERSISTENCE__ENABLED  # Always true

# REMOVED - Storage profiles replace manual config
COACHIQ_PERSISTENCE__DATA_DIR  # Set by storage profile

# REMOVED - Feature flags in config file
COACHIQ_FEATURES__ENABLE_SYSTEM_ANALYTICS
COACHIQ_FEATURES__ENABLE_PREDICTIVE_MAINTENANCE
COACHIQ_FEATURES__ENABLE_VECTOR_SEARCH
# ... (all 30+ feature flags)

# REMOVED - CAN interface config in config file
COACHIQ_CAN__INTERFACE
COACHIQ_CAN__INTERFACES
COACHIQ_CAN__FILTERS

# REMOVED - App metadata set at build time
COACHIQ_APP_NAME
COACHIQ_APP_VERSION
COACHIQ_ENVIRONMENT

# REMOVED - SSL paths set by NixOS module
COACHIQ_SERVER__SSL_KEYFILE
COACHIQ_SERVER__SSL_CERTFILE

# REMOVED - File paths bundled by Nix
COACHIQ_RVC__CONFIG_DIR
COACHIQ_RVC__SPEC_PATH
COACHIQ_RVC__COACH_MAPPING_PATH

# REMOVED - Protocol operational settings in config
COACHIQ_J1939__ADDRESS_RANGE_START
COACHIQ_FIREFLY__MULTIPLEX_BUFFER_SIZE
COACHIQ_SPARTAN_K2__BRAKE_PRESSURE_THRESHOLD
# ... (50+ protocol settings)
```

### **Configuration Loading Implementation**

**Updated `backend/core/config.py`:**
```python
class ConfigurationLoader:
    def load_settings(self) -> Settings:
        """Load configuration with hierarchical precedence."""

        # 1. Hardcoded defaults
        config = self._load_defaults()

        # 2. Config file (Categories A & B)
        config_path = os.getenv("COACHIQ_CONFIG_FILE", "/etc/coachiq/config.toml")
        if Path(config_path).exists():
            config.update(self._load_config_file(config_path))

        # 3. Environment overrides (Category C only)
        config.update(self._load_env_overrides())

        return config

    def _load_env_overrides(self) -> dict:
        """Load only Category C environment variables."""
        secret_patterns = [
            "COACHIQ_SECURITY__SECRET_KEY*",
            "COACHIQ_AUTH__*_SECRET*",
            "COACHIQ_NOTIFICATIONS__*__PASSWORD*",
            "COACHIQ_AUTH__ADMIN_*",
            "COACHIQ_SERVER__DEBUG",
            "COACHIQ_LOGGING__LEVEL",
            "COACHIQ_CONFIG_FILE"
        ]

        overrides = {}
        for env_var, value in os.environ.items():
            if self._matches_secret_pattern(env_var, secret_patterns):
                overrides[env_var] = value
            elif env_var.startswith("COACHIQ_") and self._is_deprecated(env_var):
                logger.warning(f"Deprecated: {env_var} - migrate to config file")

        return overrides
```

### **Migration Benefits**

**Environmental Variable Reduction:**
- **Before:** 100+ `COACHIQ_*__` environment variables
- **After:** 15-20 Category C variables for secrets and overrides
- **Reduction:** 85% fewer environment variables to manage

**Configuration Clarity:**
- **Architectural decisions** → Explicit config file sections
- **Deployment settings** → Environment-specific config profiles
- **Secrets** → Secure environment variable or file-based injection
- **Emergency overrides** → Runtime environment variables only

**Deployment Simplification:**
- **Nix deployment:** Single generated config file replaces dozens of environment variables
- **Development:** Clear config file with reasonable defaults
- **Production:** Secrets via systemd credentials or external secret management
- **Testing:** Override config file path, no environment pollution

This approach transforms CoachIQ's configuration from environment-variable-heavy to a clean, hierarchical system optimized for the Nix-first deployment strategy while maintaining backward compatibility during the migration period.

## Standardized Storage Architecture

### **Complete `/var/lib/coachiq` Structure**

Following Linux Standard Base conventions for system service data storage:

```
/var/lib/coachiq/                   # Service data directory (USB SSD mount point)
├── config/                         # Nix-deployed system config (READ-ONLY)
│   ├── system.toml                 # Base system settings & feature flags (444 perms)
│   ├── rvc.json                    # RV-C protocol specification (444 perms)
│   └── models/                     # Coach model definitions (555 perms)
│       ├── 2021_entegra_aspire_44r.yml
│       ├── 2022_newmar_mountain_aire.yml
│       ├── 2020_winnebago_forza.yml
│       └── generic_rv.yml
├── user/                           # User-managed data (WRITABLE)
│   ├── coachiq.db                  # Main SQLite database (ALL service data)
│   ├── user_patches.json          # User structural customizations
│   └── config-overrides.toml      # User config overrides (takes precedence)
├── backups/                        # Automated backups
│   ├── coachiq.db.2024-01-15      # Daily database backups
│   ├── coachiq.db.2024-01-14
│   └── user_patches.json.backup   # Backup of customizations
├── cache/                          # Optional performance caching
│   ├── protocol_cache.json        # Cached parsed protocol definitions
│   └── entity_discovery_cache.json # Cached CAN device discovery results
└── logs/                           # Application logs (if not using systemd journal)
    ├── coachiq.log
    └── archived/
        └── coachiq.log.2024-01-14
```

### **Read-Only System Configuration Protection**

**Problem Solved**: User accidentally modifying Nix-deployed system configuration files, causing their changes to be overwritten on updates.

**Solution**: Two-tier configuration system with read-only system config and user overrides.

**Implementation**:
1. **System Config Files** (deployed by Nix, read-only 444 permissions):
   - `/var/lib/coachiq/config/system.toml` - Base system settings
   - `/var/lib/coachiq/config/rvc.json` - Protocol specification
   - `/var/lib/coachiq/config/models/*.yml` - Coach model definitions

2. **User Override Files** (writable 644 permissions):
   - `/var/lib/coachiq/user/config-overrides.toml` - User configuration overrides
   - `/var/lib/coachiq/user/user_patches.json` - Structural customizations

**Protection Mechanisms**:
- **File Permissions**: System files set to 444 (read-only for all)
- **Directory Permissions**: System config directory set to 555 (read + execute only)
- **Runtime Verification**: Configuration loader checks and fixes incorrect permissions
- **Merge Strategy**: User overrides take precedence over system settings during configuration loading
- **Update Safety**: Nix updates only touch read-only system files, never user files

**User Experience**:
- Users can safely modify `/var/lib/coachiq/user/config-overrides.toml` without fear of losing changes
- System updates preserve all user customizations
- Clear separation between system-managed and user-managed configuration
- Deep merge support for nested configuration objects

**Example Configuration Override**:
```bash
# System config (READ-ONLY): /var/lib/coachiq/config/system.toml
[server]
port = 8080
host = "0.0.0.0"
debug = false

[logging]
level = "INFO"
log_to_file = true

[features]
enable_system_analytics = true
enable_authentication = true
```

```bash
# User override (WRITABLE): /var/lib/coachiq/user/config-overrides.toml
[server]
port = 8081  # Override: User wants different port

[logging]
level = "DEBUG"  # Override: User needs debug logging

# The merged result will be:
# server.port = 8081 (user override)
# server.host = "0.0.0.0" (system default)
# server.debug = false (system default)
# logging.level = "DEBUG" (user override)
# logging.log_to_file = true (system default)
# features.* = system defaults (unchanged)
```

### **Storage Profile Handling**

**SSD Profile (Primary)**:
- `/var/lib/coachiq` → direct USB SSD mount point
- High-performance storage for maximum throughput
- Full logging and high-frequency analytics enabled

**SD Card Profile (Durability)**:
- `/var/lib/coachiq` → tmpfs mount (RAM-based)
- Periodic sync to `/var/lib/coachiq-persist` on SD card
- Reduced write frequency, minimal logging

**Development Profile**:
- `/var/lib/coachiq` → `/tmp/coachiq-dev-${USER}`
- Temporary storage for development/testing
- Full debug logging enabled

### **Database Schema Evolution**

The `coachiq.db` SQLite database contains multiple logical schemas:

```sql
-- System configuration state
CREATE TABLE system_settings (
    key TEXT PRIMARY KEY,
    value TEXT,
    last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User cosmetic preferences
CREATE TABLE user_settings (
    key TEXT PRIMARY KEY,
    value TEXT,
    last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Entity state persistence (for startup recovery)
CREATE TABLE entity_states (
    entity_id TEXT PRIMARY KEY,
    state JSON NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Schema versioning for migrations
CREATE TABLE schema_info (
    version TEXT PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Coach model change tracking
CREATE TABLE model_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_name TEXT NOT NULL,
    activated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    base_model_hash TEXT,
    user_patches_hash TEXT
);
```

### **Configuration File Locations**

**Complete Service Directory (USB SSD Mount Point)**:
```
/var/lib/coachiq/                  # Single directory contains everything
├── config/                        # Nix-deployed system configuration
│   ├── system.toml                # System settings & feature flags
│   ├── rvc.json                   # RV-C protocol specification
│   └── models/                    # Coach model definitions
│       ├── 2021_entegra_aspire_44r.yml
│       ├── 2022_newmar_mountain_aire.yml
│       ├── 2020_winnebago_forza.yml
│       └── generic_rv.yml         # Fallback model
├── coachiq.db                     # All service data (system + user + analytics + auth)
├── user_patches.json             # User structural customizations
└── backups/                       # Automated backups
    ├── coachiq.db.2024-01-15
    └── user_patches.json.backup
```

### **Backup & Restore Strategy**

**Complete System Backup**:
```bash
# Single command backs up entire CoachIQ installation
tar -czf ~/coachiq-full-backup-$(date +%Y%m%d).tar.gz \
  /var/lib/coachiq/
```

**User Data Only Backup**:
```bash
# Backup just user-specific data (excludes Nix-deployed config)
tar -czf ~/coachiq-user-backup-$(date +%Y%m%d).tar.gz \
  /var/lib/coachiq/coachiq.db \
  /var/lib/coachiq/user_patches.json
```

**System Recovery**:
```bash
# Complete restore (includes all config files)
cd /
tar -xzf ~/coachiq-full-backup-20240115.tar.gz
systemctl restart coachiq

# Or user data only (after Nix deployment)
cd /var/lib/coachiq
tar -xzf ~/coachiq-user-backup-20240115.tar.gz --strip-components=3
systemctl restart coachiq
```

**Factory Reset**:
```sql
-- Via web UI or SQL command
DELETE FROM user_settings;
DELETE FROM entity_states;
UPDATE system_settings SET value = NULL WHERE key LIKE 'user.%';
```

### **Benefits of Unified `/var/lib/coachiq` Approach**

**Simplified Backup & Recovery:**
- **Single directory** contains entire CoachIQ installation
- **Complete backup** with one `tar` command
- **User data isolation** still possible for selective restore
- **USB SSD portability** - entire system on one device

**Enhanced Development Experience:**
- **One mount point** to manage during development
- **Clear ownership** - coachiq user owns everything
- **Simplified permissions** - no cross-directory permission issues
- **Container-friendly** - single volume mount

**Deployment Advantages:**
- **Nix flexibility** - can deploy config anywhere, not limited to `/etc`
- **Atomic operations** - USB SSD contains complete system state
- **Migration simplicity** - move entire `/var/lib/coachiq` between systems
- **Disaster recovery** - restore from USB SSD backup to any Pi

**Storage Profile Benefits:**
- **SSD Profile**: Direct mount, all data on high-performance storage
- **SD Card Profile**: tmpfs for `/var/lib/coachiq`, periodic sync to SD persistent storage
- **Development**: Temporary `/tmp/coachiq-dev` without affecting system

This unified approach maintains clear separation between Nix-deployed system configuration and user-managed data while simplifying the overall architecture and backup strategy.

## Code Quality Assurance Summary

**Mandatory Quality Standards Throughout Migration:**

✅ **Zero Tolerance Policy:**
- **Type Errors**: All TypeScript and Python code must pass type checking
- **Lint Violations**: All ESLint and Ruff checks must pass
- **Test Failures**: Minimum 80% coverage with all tests passing
- **Build Failures**: Frontend must build successfully at all times

✅ **Required Tools Integration:**
- **Pyright** for Python type checking
- **Ruff** for Python linting and formatting
- **ESLint** for TypeScript/React linting
- **pytest** with coverage reporting
- **Vitest** for frontend testing
- **Pre-commit hooks** for automated quality gates

✅ **Development Workflow:**
```bash
# Before any commit
./scripts/quality-check.sh

# Before any pull request
poetry run pre-commit run --all-files
cd frontend && npm run build
```

✅ **CI/CD Integration:**
- GitHub Actions quality pipeline prevents merging of poor-quality code
- Automated testing on multiple environments
- Coverage reporting and trend analysis
- Integration with code review process

This ensures the persistence migration delivers not just functional improvements, but maintains the highest code quality standards throughout the transformation.
