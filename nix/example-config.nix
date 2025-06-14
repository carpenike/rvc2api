# Example NixOS configuration for CoachIQ
# This file demonstrates all available configuration options with their defaults
# Copy and modify this for your deployment

{ config, lib, pkgs, ... }:

{
  # Enable the CoachIQ service
  coachiq.enable = true;

  # Optional: Use a specific package version
  # coachiq.package = pkgs.coachiq.override { ... };

  coachiq.settings = {
    # Application metadata
    # appName = "CoachIQ";  # Default: "CoachIQ"
    # appVersion = "0.0.0"; # Default: "0.0.0"
    # apiTitle = "RV-C API"; # Default: "RV-C API"

    # Server configuration
    server = {
      # host = "0.0.0.0";     # Default: "0.0.0.0" - binds to all interfaces
      # port = 8000;          # Default: 8000
      # workers = 1;          # Default: 1 - number of worker processes
      # reload = false;       # Default: false - auto-reload for development
      # debug = false;        # Default: false - debug mode

      # Advanced server settings (rarely need to change)
      # keepAliveTimeout = 5;           # Default: 5 seconds
      # timeoutGracefulShutdown = 30;   # Default: 30 seconds
      # workerConnections = 1000;       # Default: 1000

      # SSL/TLS configuration (null means disabled)
      # sslKeyfile = "/path/to/key.pem";
      # sslCertfile = "/path/to/cert.pem";
    };

    # CORS configuration
    cors = {
      # allowedOrigins = ["*"];        # Default: ["*"] - all origins
      # allowedCredentials = true;     # Default: true
      # allowedMethods = ["*"];        # Default: ["*"] - all methods
      # allowedHeaders = ["*"];        # Default: ["*"] - all headers
    };

    # Security settings
    security = {
      # secretKey = null;              # REQUIRED for production!
      # jwtAlgorithm = "HS256";       # Default: "HS256"
      # jwtExpireMinutes = 30;        # Default: 30
    };

    # Logging configuration
    logging = {
      # level = "INFO";               # Default: "INFO" - Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
      # format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s";
      # logToFile = false;            # Default: false
      # logFile = "/var/log/coachiq/app.log";  # Only used if logToFile = true
    };

    # CAN bus configuration
    canbus = {
      # bustype = "socketcan";        # Default: "socketcan" for production
      # channels = ["can0", "can1"];  # Default: ["can0"]
      # interface = "can0";           # DEPRECATED - use channels

      # Interface mappings for logical to physical mapping
      # interfaceMappings = {
      #   house = "can0";      # House network on can0
      #   chassis = "can1";    # Chassis network on can1
      # };

      # bitrate = 250000;            # Default: 250000 (RV-C standard)
      # receiveOwnMessages = true;   # Default: true
      # fdEnabled = false;           # Default: false - CAN FD support
    };

    # Persistence configuration
    persistence = {
      enabled = true;                 # Default: true - SQLite persistence
      # dataDir = "/var/lib/coachiq"; # Default: "/var/lib/coachiq"
      # backupEnabled = true;         # Default: true
      # backupInterval = 3600;        # Default: 3600 seconds (1 hour)
      # backupRetentionDays = 7;      # Default: 7 days
    };

    # Feature flags - Core system features
    features = {
      # Core features (usually leave enabled)
      # enableApiDocs = true;         # Default: true - Swagger/ReDoc
      # enableMetrics = true;         # Default: true - Prometheus metrics
      # enableCORS = true;            # Default: true - CORS support

      # Optional features
      # enableMaintenanceTracking = false;  # Default: false
      # enableNotifications = false;        # Default: false
      # enableVectorSearch = true;          # Default: true - RV-C spec search
      # enableDeviceDiscovery = true;       # Default: true - Active device polling

      # Protocol support
      # enableJ1939 = false;               # Default: false - J1939 protocol
      # enableFirefly = false;             # Default: false - Firefly systems
      # enableSpartanK2 = false;           # Default: false - Spartan K2 chassis
      # enableMultiNetworkCAN = false;     # Default: false - Multi-network routing

      # Advanced features
      # enableAdvancedDiagnostics = true;   # Default: true - DTC processing
      # enablePerformanceAnalytics = true;  # Default: true - Performance monitoring

      # API versions (migration support)
      # enableDomainAPIv2 = true;          # Default: true - New Domain API
      # enableLegacyAPI = false;           # Default: false - Deprecated
    };

    # RV-C protocol settings
    rvc = {
      # configDir = null;               # Default: auto-detected
      # specPath = null;                # Default: bundled rvc.json
      # coachMappingPath = null;        # Default: based on modelSelector
      # coachModel = null;              # Example: "2021_Entegra_Aspire_44R"

      # Protocol features
      # enableEncoder = true;           # Default: true - Message encoding
      # enableValidator = true;         # Default: true - Message validation
      # enableSecurity = true;          # Default: true - Security checks
      # maxQueueSize = 10000;          # Default: 10000 messages
    };

    # J1939 protocol settings (only if enableJ1939 = true)
    j1939 = {
      # enableCumminsExtensions = true;    # Default: true
      # enableAllisonExtensions = true;    # Default: true
      # enableChassisExtensions = true;    # Default: true
      # enableRvcBridge = true;            # Default: true - RV-C bridging
      # defaultInterface = "chassis";      # Default: "chassis"
    };

    # Notification system (only if enableNotifications = true)
    notifications = {
      # enabled = false;                   # Default: false
      # defaultTitle = "CoachIQ Notification";

      # SMTP configuration
      smtp = {
        # enabled = false;
        # host = "smtp.gmail.com";
        # port = 587;
        # username = "";
        # password = "";  # Use secretKey for production
        # useTls = true;
        # useStarttls = true;
      };

      # Slack integration
      slack = {
        # enabled = false;
        # webhookUrl = "";
        # channel = "#general";
        # username = "CoachIQ Bot";
      };

      # Additional notification channels...
    };

    # Authentication settings
    auth = {
      # mode = "jwt";                    # Options: "jwt", "session", "none"
      # requireAuth = true;              # Default: true
      # sessionSecret = null;            # Required for session mode
      # sessionMaxAge = 86400;           # Default: 24 hours

      # MFA settings
      # mfaRequired = false;             # Default: false
      # mfaIssuer = "CoachIQ";
      # totpWindow = 1;                  # Default: 1 (30-second window)
    };

    # Model selector for coach-specific configurations
    # modelSelector = "2021_Entegra_Aspire_44R";

    # GitHub update checking
    # githubUpdateRepo = "carpenike/coachiq";  # Default: "carpenike/coachiq"
  };
}
