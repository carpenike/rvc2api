# Manage Database

Complete database development workflow including migrations, testing, and data management for the CoachIQ persistence system.

## Database Migration Management

### 1. Check Migration Status
```bash
# Enable persistence feature for database operations
export COACHIQ_FEATURES__ENABLE_PERSISTENCE=true

# Check current migration status
poetry run alembic current

# Show migration history
poetry run alembic history --verbose

# Check for pending migrations
poetry run alembic show
```

### 2. Create New Migration
```bash
# Auto-generate migration from model changes
poetry run alembic revision --autogenerate -m "Description of changes"

# Create empty migration file for manual changes
poetry run alembic revision -m "Manual migration description"

# Review generated migration file
ls -la backend/alembic/versions/
echo "Review the latest migration file before applying"
```

### 3. Apply Migrations
```bash
# Apply all pending migrations
poetry run alembic upgrade head

# Apply specific migration
# poetry run alembic upgrade <revision_id>

# Verify migration applied successfully
poetry run alembic current
```

## Database Setup and Reset

### 4. Initialize Fresh Database
```bash
# Set up development database environment
export COACHIQ_PERSISTENCE__ENABLED=true
export COACHIQ_PERSISTENCE__DATA_DIR=backend/data/persistent/database

# Create data directory if it doesn't exist
mkdir -p backend/data/persistent/database

# Initialize database with all migrations
poetry run alembic upgrade head

# Verify database initialization
poetry run python -c "
from backend.services.database_manager import DatabaseManager
from backend.core.config import get_settings
import asyncio

async def check_db():
    settings = get_settings()
    db_manager = DatabaseManager(settings.persistence)
    await db_manager.startup()

    health = await db_manager.get_health()
    print(f'Database health: {health}')

    await db_manager.shutdown()

asyncio.run(check_db())
"
```

### 5. Reset Development Database
```bash
# Backup existing database if needed
if [ -f "backend/data/persistent/database/coachiq.db" ]; then
    cp backend/data/persistent/database/coachiq.db backend/data/persistent/database/coachiq.db.backup.$(date +%Y%m%d_%H%M%S)
    echo "Database backed up"
fi

# Remove existing database
rm -f backend/data/persistent/database/coachiq.db

# Recreate from migrations
poetry run alembic upgrade head

echo "Database reset complete"
```

## Test Data Management

### 6. Seed Test Data
```bash
# Create sample entities and configurations for testing
poetry run python -c "
import asyncio
from backend.services.database_manager import DatabaseManager
from backend.services.repositories import ConfigRepository, DashboardRepository
from backend.core.config import get_settings

async def seed_test_data():
    settings = get_settings()
    db_manager = DatabaseManager(settings.persistence)
    await db_manager.startup()

    # Seed configuration data
    config_repo = ConfigRepository(db_manager)
    sample_config = {
        'can_interfaces': ['can0', 'can1'],
        'rvc_enabled': True,
        'vector_search_enabled': False
    }

    try:
        await config_repo.create(sample_config)
        print('✓ Sample configuration created')
    except Exception as e:
        print(f'Config already exists or error: {e}')

    # Seed dashboard data
    dashboard_repo = DashboardRepository(db_manager)
    sample_dashboard = {
        'dashboard_id': 'default',
        'layout': {'widgets': ['entities', 'can_status']},
        'preferences': {'theme': 'auto', 'refresh_rate': 1000}
    }

    try:
        await dashboard_repo.create(sample_dashboard)
        print('✓ Sample dashboard created')
    except Exception as e:
        print(f'Dashboard already exists or error: {e}')

    await db_manager.shutdown()
    print('Test data seeding complete')

asyncio.run(seed_test_data())
"
```

### 7. Validate Database Schema
```bash
# Test all repository operations
poetry run python -c "
import asyncio
from backend.services.database_manager import DatabaseManager
from backend.services.repositories import ConfigRepository, DashboardRepository
from backend.core.config import get_settings

async def validate_schema():
    settings = get_settings()
    db_manager = DatabaseManager(settings.persistence)
    await db_manager.startup()

    # Test configuration repository CRUD operations
    config_repo = ConfigRepository(db_manager)

    # Test create
    test_config = {'test_key': 'test_value', 'timestamp': '2024-01-01T00:00:00Z'}
    created = await config_repo.create(test_config)
    print(f'✓ Config create: {created[\"id\"]}')

    # Test read
    retrieved = await config_repo.get_by_id(created['id'])
    print(f'✓ Config read: {retrieved[\"test_key\"]}')

    # Test update
    updated_config = {'test_key': 'updated_value', 'new_field': 'new_data'}
    updated = await config_repo.update(created['id'], updated_config)
    print(f'✓ Config update: {updated[\"test_key\"]}')

    # Test delete
    await config_repo.delete(created['id'])
    print('✓ Config delete completed')

    # Test dashboard repository
    dashboard_repo = DashboardRepository(db_manager)

    # Test dashboard operations
    test_dashboard = {
        'dashboard_id': 'test_dashboard',
        'layout': {'test': True},
        'preferences': {'test_pref': 'value'}
    }

    created_dashboard = await dashboard_repo.create(test_dashboard)
    print(f'✓ Dashboard create: {created_dashboard[\"dashboard_id\"]}')

    # Cleanup test dashboard
    await dashboard_repo.delete(created_dashboard['id'])
    print('✓ Dashboard delete completed')

    await db_manager.shutdown()
    print('Database schema validation complete')

asyncio.run(validate_schema())
"
```

## Backup and Restore

### 8. Backup Database
```bash
# Create timestamped backup
BACKUP_DIR="backend/data/backups"
mkdir -p "$BACKUP_DIR"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/coachiq_backup_$TIMESTAMP.db"

# Copy database file
if [ -f "backend/data/persistent/database/coachiq.db" ]; then
    cp backend/data/persistent/database/coachiq.db "$BACKUP_FILE"
    echo "Database backed up to: $BACKUP_FILE"

    # Test backup integrity using persistence service
    poetry run python -c "
import asyncio
import shutil
from backend.services.persistence_service import PersistenceService
from backend.core.config import get_settings

async def test_backup():
    settings = get_settings()
    persistence_service = PersistenceService(settings.persistence)

    # Test backup operation
    backup_result = await persistence_service.backup_database()
    print(f'Backup service result: {backup_result}')

asyncio.run(test_backup())
"
else
    echo "No database file found to backup"
fi
```

### 9. Restore Database
```bash
# List available backups
echo "Available backups:"
ls -la backend/data/backups/ 2>/dev/null || echo "No backups found"

# Restore from latest backup (manual selection)
LATEST_BACKUP=$(ls -t backend/data/backups/coachiq_backup_*.db 2>/dev/null | head -1)

if [ -n "$LATEST_BACKUP" ] && [ "$1" = "--restore-latest" ]; then
    echo "Restoring from: $LATEST_BACKUP"

    # Backup current database
    if [ -f "backend/data/persistent/database/coachiq.db" ]; then
        mv backend/data/persistent/database/coachiq.db backend/data/persistent/database/coachiq.db.pre-restore
        echo "Current database backed up as coachiq.db.pre-restore"
    fi

    # Restore from backup
    cp "$LATEST_BACKUP" backend/data/persistent/database/coachiq.db
    echo "Database restored from backup"

    # Verify restored database
    poetry run alembic current
else
    echo "Use '--restore-latest' argument to restore from most recent backup"
    echo "Or manually copy desired backup file to backend/data/persistent/database/coachiq.db"
fi
```

## Performance and Monitoring

### 10. Database Performance Check
```bash
# Monitor database performance and connections
poetry run python -c "
import asyncio
import time
from backend.services.database_manager import DatabaseManager
from backend.core.config import get_settings

async def performance_check():
    settings = get_settings()
    db_manager = DatabaseManager(settings.persistence)
    await db_manager.startup()

    print('Starting database performance check...')

    # Test connection pool performance
    start_time = time.time()

    async def test_connection():
        async with db_manager.get_session() as session:
            # Simple query to test connection speed
            result = await session.execute('SELECT 1')
            return result.scalar()

    # Run multiple concurrent connections
    tasks = [test_connection() for _ in range(10)]
    results = await asyncio.gather(*tasks)

    end_time = time.time()

    print(f'✓ Connection test completed in {end_time - start_time:.2f}s')
    print(f'✓ All {len(results)} connections successful')

    # Check database size
    try:
        import os
        db_path = 'backend/data/persistent/database/coachiq.db'
        if os.path.exists(db_path):
            size_mb = os.path.getsize(db_path) / (1024 * 1024)
            print(f'✓ Database size: {size_mb:.2f} MB')
    except Exception as e:
        print(f'Could not check database size: {e}')

    await db_manager.shutdown()
    print('Performance check complete')

asyncio.run(performance_check())
"
```

## Cleanup and Health Check

### 11. Database Health Verification
```bash
# Comprehensive database health check
echo "=== Database Health Check ==="

# Check if persistence feature is enabled
poetry run python -c "
from backend.services.feature_manager import FeatureManager
import asyncio

async def check_persistence_feature():
    feature_manager = FeatureManager()
    await feature_manager.startup()

    if feature_manager.is_enabled('persistence'):
        print('✓ Persistence feature is enabled')
        persistence_feature = feature_manager.get_feature('persistence')
        print(f'✓ Persistence feature status: {persistence_feature.health}')
    else:
        print('✗ Persistence feature is disabled')
        print('Set COACHIQ_FEATURES__ENABLE_PERSISTENCE=true to enable')

    await feature_manager.shutdown()

asyncio.run(check_persistence_feature())
"

# Check migration status
echo "=== Migration Status ==="
poetry run alembic current 2>/dev/null || echo "No migrations applied or alembic not configured"

# Check database file
echo "=== Database Files ==="
if [ -f "backend/data/persistent/database/coachiq.db" ]; then
    echo "✓ Database file exists"
    ls -lh backend/data/persistent/database/coachiq.db
else
    echo "✗ Database file not found"
fi

# Check backup directory
echo "=== Backup Status ==="
if [ -d "backend/data/backups" ]; then
    backup_count=$(ls backend/data/backups/*.db 2>/dev/null | wc -l)
    echo "✓ Backup directory exists with $backup_count backup files"
else
    echo "✗ No backup directory found"
fi

echo "=== Database Management Complete ==="
```

## Arguments

$ARGUMENTS can specify:
- `--reset` - Reset database and apply all migrations
- `--seed` - Include test data seeding
- `--backup` - Create backup before any operations
- `--restore-latest` - Restore from most recent backup
- `--skip-validation` - Skip schema validation tests
- `--performance` - Run performance benchmarks
- `migrate-only` - Only run migration operations
- `backup-only` - Only perform backup operations

## Development Notes

### Database Configuration
- SQLite database stored in `backend/data/persistent/database/coachiq.db`
- Migrations in `backend/alembic/versions/`
- Use `COACHIQ_FEATURES__ENABLE_PERSISTENCE=true` to enable database features

### Troubleshooting
- If migrations fail, check `backend/alembic/env.py` configuration
- For permission errors, ensure write access to `backend/data/` directory
- If connection fails, verify database file exists and is not corrupted
- For performance issues, check database size and consider vacuum operations

This command provides complete database lifecycle management for development, testing, and maintenance of the CoachIQ persistence system.
