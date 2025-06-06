# Configuration Management

This document describes the configuration management approach used in the RVC2API project.

## Environment Variable Patterns

RVC2API uses a consistent pattern for environment variables to support hierarchical configuration:

- **Top-level settings**: `RVC2API_SETTING` (e.g., `RVC2API_APP_NAME`)
- **Nested settings**: `RVC2API_SECTION__SETTING` (e.g., `RVC2API_SERVER__HOST`)

This approach allows for organizing related settings while maintaining compatibility with standard environment variable patterns.

## Configuration Loading Order

The configuration values are loaded in the following order:

1. Default values specified in the Settings classes
2. Values from `.env` file (if present)
3. Environment variables (which override any previous values)

## Configuration Sections

The configuration is organized into logical sections:

### Top-level Settings

These settings apply to the entire application:

- `RVC2API_APP_NAME`: Application name
- `RVC2API_APP_VERSION`: Application version
- `RVC2API_APP_DESCRIPTION`: Application description
- `RVC2API_APP_TITLE`: API title for documentation
- `RVC2API_ENVIRONMENT`: Application environment (development, testing, staging, production)
- `RVC2API_DEBUG`: Enable debug mode
- `RVC2API_TESTING`: Enable testing mode
- `RVC2API_STATIC_DIR`: Static files directory
- `RVC2API_RVC_SPEC_PATH`: Path to RVC spec JSON file
- `RVC2API_RVC_COACH_MAPPING_PATH`: Path to RVC coach mapping YAML file
- `RVC2API_GITHUB_UPDATE_REPO`: GitHub repository for update checks (owner/repo)
- `RVC2API_CONTROLLER_SOURCE_ADDR`: Controller source address

### Server Settings

Server-specific settings with the prefix `RVC2API_SERVER__`:

- `RVC2API_SERVER__HOST`: Server host address
- `RVC2API_SERVER__PORT`: Server port
- `RVC2API_SERVER__RELOAD`: Enable auto-reload in development
- `RVC2API_SERVER__WORKERS`: Number of worker processes
- `RVC2API_SERVER__ACCESS_LOG`: Enable access logging
- `RVC2API_SERVER__DEBUG`: Enable server debug mode
- `RVC2API_SERVER__ROOT_PATH`: Root path for the application

### CORS Settings

CORS-specific settings with the prefix `RVC2API_CORS__`:

- `RVC2API_CORS__ENABLED`: Enable CORS middleware
- `RVC2API_CORS__ALLOW_ORIGINS`: Allowed origins for CORS (comma-separated)
- `RVC2API_CORS__ALLOW_CREDENTIALS`: Allow credentials in CORS
- `RVC2API_CORS__ALLOW_METHODS`: Allowed HTTP methods (comma-separated)
- `RVC2API_CORS__ALLOW_HEADERS`: Allowed headers (comma-separated)

### Security Settings

Security-specific settings with the prefix `RVC2API_SECURITY__`:

- `RVC2API_SECURITY__SECRET_KEY`: Secret key for session management
- `RVC2API_SECURITY__API_KEY`: API key for authentication
- `RVC2API_SECURITY__ALLOWED_IPS`: Allowed IP addresses (comma-separated)
- `RVC2API_SECURITY__RATE_LIMIT_ENABLED`: Enable rate limiting
- `RVC2API_SECURITY__RATE_LIMIT_REQUESTS`: Rate limit requests per minute

### Logging Settings

Logging-specific settings with the prefix `RVC2API_LOGGING__`:

- `RVC2API_LOGGING__LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `RVC2API_LOGGING__FORMAT`: Log format string
- `RVC2API_LOGGING__LOG_TO_FILE`: Enable logging to file
- `RVC2API_LOGGING__COLORIZE`: Enable colored logging output

### CAN Settings

CAN-specific settings with the prefix `RVC2API_CAN__`:

- `RVC2API_CAN__INTERFACE`: CAN interface name
- `RVC2API_CAN__BUSTYPE`: CAN bus type
- `RVC2API_CAN__BITRATE`: CAN bus bitrate
- `RVC2API_CAN__TIMEOUT`: CAN timeout in seconds
- `RVC2API_CAN__BUFFER_SIZE`: Message buffer size
- `RVC2API_CAN__AUTO_RECONNECT`: Auto-reconnect on CAN failure
- `RVC2API_CAN__FILTERS`: CAN message filters (comma-separated)

### Feature Flags

Feature-specific settings with the prefix `RVC2API_FEATURES__`:

- `RVC2API_FEATURES__ENABLE_MAINTENANCE_TRACKING`: Enable maintenance tracking
- `RVC2API_FEATURES__ENABLE_NOTIFICATIONS`: Enable notifications
- `RVC2API_FEATURES__ENABLE_VECTOR_SEARCH`: Enable vector search feature
- `RVC2API_FEATURES__ENABLE_UPTIMEROBOT`: Enable UptimeRobot integration
- `RVC2API_FEATURES__ENABLE_PUSHOVER`: Enable Pushover notifications
- `RVC2API_FEATURES__ENABLE_API_DOCS`: Enable API documentation
- `RVC2API_FEATURES__ENABLE_METRICS`: Enable metrics collection
- `RVC2API_FEATURES__MESSAGE_QUEUE_SIZE`: Message queue size

## Using Settings in Code

The settings are accessed through the `get_settings()` function, which returns a cached instance of the Settings class:

```python
from backend.core.config import get_settings

settings = get_settings()
app_name = settings.app_name
server_host = settings.server.host
```

For specific sections, you can use the convenience functions:

```python
from backend.core.config import get_server_settings, get_cors_settings

server_settings = get_server_settings()
cors_settings = get_cors_settings()
```

## Environment-Specific Configuration

Different environments can be configured by setting the `RVC2API_ENVIRONMENT` variable:

- `development`: Development environment (default)
- `testing`: Testing environment
- `staging`: Staging environment
- `production`: Production environment

You can check the current environment with:

```python
from backend.core.config import get_settings

settings = get_settings()
if settings.is_development():
    # Development-specific code
elif settings.is_production():
    # Production-specific code
```

## Tips for Working with Configuration

1. Use environment variables for all configuration that changes between environments
2. Use `.env` files for local development, but never commit them to version control
3. Use the provided settings classes rather than accessing environment variables directly
4. Validate and document all configuration options
5. Use feature flags to control feature availability
6. For sensitive information, use secret management services in production
