# flake# ▸ CLI apps (run with `nix run .#<n>`) for:
#    - `test`     → run unit tests
#    - `lint`     → run ruff, pyright, djlint
#    - `format`   → run ruff format and djlint in reformat mode — Nix flake definition for rvc2api
#
# This flake provides:
#
# ▸ A Python-based CANbus FastAPI web service built with Poetry
# ▸ Unified versioning via the root-level `VERSION` file
# ▸ Reproducible developer environments with `devShells.default` and `devShells.ci`
# ▸ CLI apps (run with `nix run .#<name>`) for:
#    - `test`     → run unit tests
#    - `lint`     → run ruff, mypy, djlint
#    - `format`   → run ruff format and djlint in reformat mode
#    - `ci`       → run full gate: pre-commit, tests, lints, poetry lock
#    - `precommit`→ run pre-commit checks across the repo
# ▸ Nix flake checks (via `nix flake check`) for:
#    - pytest suite
#    - style (ruff, pyright, djlint)
#    - lockfile validation (poetry check --lock --no-interaction)
# ▸ Package build output under `packages.<system>.coachiq`
#
# Best Practices:
# - Canonical version is managed in `VERSION` file
# - `pyproject.toml` is synchronized with the VERSION file during builds
# - Release automation is handled via `release-please`, which updates `VERSION` and `flake.nix`
# - Runtime version is available in the app via `core_daemon._version.VERSION`
#
# Usage (in this repo):
#   nix develop             # Enter the default dev environment
#   nix run .#test          # Run tests
#   nix run .#lint          # Run linter suite
#   nix flake check         # Run CI-grade validation
#   nix build .#coachiq     # Build the package
#
# Usage (in a system flake or NixOS configuration):
#
#   # In your flake inputs:
#   inputs.rvc2api.url = "github:carpenike/rvc2api";
#
#   # As a package:
#   environment.systemPackages = [ inputs.rvc2api.packages.${system}.coachiq ];
#
#   # As a NixOS module:
#   imports = [ inputs.rvc2api.nixosModules.coachiq ];
#   # Then configure it:
#   coachiq.settings = { ... };
#
#   # Or to reference CLI apps:
#   nix run inputs.rvc2api#check
#
# See docs/nixos-integration.md for more details

{
  description = "CoachIQ Python package and devShells";

  inputs = {
    nixpkgs.url     = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils, ... }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
        python = pkgs.python312;
        pythonPackages = pkgs.python312Packages;

        # Read version from VERSION file (source of truth)
        version = builtins.replaceStrings ["\n"] [""] (builtins.readFile ./VERSION);

        coachiqPackage = pythonPackages.buildPythonPackage {
          pname = "coachiq";
          inherit version;
          src      = self;
          format   = "pyproject";

          nativeBuildInputs = with pythonPackages; [ poetry-core ];
          propagatedBuildInputs = [
            pythonPackages.coloredlogs
            pythonPackages.fastapi
            pythonPackages.httptools
            pythonPackages.httpx
            pythonPackages.langchain-community
            pythonPackages.langchain-core
            pythonPackages.prometheus_client
            pythonPackages.pydantic
            pythonPackages.pyroute2
            pythonPackages.python-can
            pythonPackages.python-dotenv
            pythonPackages.pyyaml
            pythonPackages.uvicorn
            pythonPackages.watchfiles
            pythonPackages.websockets
          ] ++ pkgs.lib.optionals (pkgs.stdenv.isLinux || pkgs.stdenv.isDarwin) [
            pythonPackages.uvloop   # Uvicorn standard extra (conditional)
          ] ++ [
          ] ++ pkgs.lib.optionals pkgs.stdenv.isLinux [
            pythonPackages.pyroute2
          ];

          doCheck    = true;
          checkInputs = [ pythonPackages.pytest ];

          # Install configuration files to the package site-packages directory
          # This allows the NixOS module to reference them at the expected path
          postInstall = ''
            mkdir -p $out/${python.sitePackages}/config
            cp -r $src/config/* $out/${python.sitePackages}/config/
          '';

          meta = with pkgs.lib; {
            description = "CAN‑bus web service exposing RV‑C network data via HTTP & WebSocket";
            homepage    = "https://github.com/carpenike/rvc2api";
            license     = licenses.asl20;
            maintainers = [{
              name   = "Ryan Holt";
              email  = "ryan@ryanholt.net";
              github = "carpenike";
            }];
          };
        };

        devShell = pkgs.mkShell {
          buildInputs = [
            # --- Backend dependencies ---
            python
            pkgs.poetry
            pythonPackages.fastapi
            pythonPackages.uvicorn
            pythonPackages.websockets
            pythonPackages.httptools
            pythonPackages.python-dotenv
            pythonPackages.watchfiles
            pythonPackages.python-can
            pythonPackages.pydantic
            pythonPackages.pyyaml
            pythonPackages.prometheus_client
            pythonPackages.coloredlogs
            pythonPackages.jinja2
            pythonPackages.pytest
            pythonPackages.mypy
            pythonPackages.ruff
            pythonPackages.types-pyyaml
            pkgs.fish
            pythonPackages.pytest-asyncio

            # --- Dev Tools dependencies ---
            pythonPackages.langchain
            pythonPackages."langchain-openai"
            pythonPackages.pymupdf  # PyMuPDF, imported as fitz
            pythonPackages."faiss"

            # --- Frontend dependencies ---
            # Only include Node.js runtime, npm will manage package dependencies
            pkgs.nodejs_20

            # --- Development tools ---
            pkgs.pyright  # For Python type checking
          ] ++ pkgs.lib.optionals (pkgs.stdenv.isLinux || pkgs.stdenv.isDarwin) [
            pythonPackages.uvloop
          ] ++ pkgs.lib.optionals pkgs.stdenv.isLinux [
            pythonPackages.pyroute2
            pkgs.iproute2
            pkgs.stdenv.cc.cc.lib
            pkgs.zlib
          ];
          shellHook = ''
            export PYTHONPATH=$PWD:$PYTHONPATH
            # Helper: run poetry with Nix's libstdc++ only for Python invocations
            poetry() {
              LD_LIBRARY_PATH=${pkgs.zlib}/lib:${pkgs.stdenv.cc.cc.lib}/lib''${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH} command poetry "$@"
            }
            export -f poetry
            # Set prompt reliably in bash (including VS Code) and zsh
            if [ -n "$BASH_VERSION" ]; then
              export OLD_PS1="$PS1"
              export PS1="\[\033[1;32m\](nix develop)\[\033[0m\] $OLD_PS1"
            elif [ -n "$ZSH_VERSION" ]; then
              export PS1="%F{green}(nix develop)%f $PS1"
            fi
            if [ -n "$FISH_VERSION" ] || [ -x "$(command -v fish)" ]; then
              mkdir -p "$HOME/.config/fish/conf.d"
              cat > "$HOME/.config/fish/conf.d/nix_devshell_prompt.fish" <<'EOF'
function fish_prompt
  set_color green
  echo -n "(nix develop) "
  set_color normal
  echo -n (prompt_pwd) " > "
end
EOF
              if [ -n "$FISH_VERSION" ]; then
                source "$HOME/.config/fish/conf.d/nix_devshell_prompt.fish"
              fi
            fi
            # Set up Node.js environment
            export NODE_PATH=$PWD/frontend/node_modules

            echo "🐚 Entered rvc2api devShell on ${pkgs.system} with Python ${python.version} and Node.js $(node --version)"
            echo "💡 Backend commands:"
            echo "  • poetry install              # Install Python dependencies (now always uses correct LD_LIBRARY_PATH)"
            echo "  • poetry run python run_server.py  # Run API server"
            echo "  • poetry run pytest           # Run tests"
            echo "  • poetry run ruff check .     # Lint"
            echo "  • poetry run ruff format backend  # Format"
            echo "  • poetry run pyright backend  # Type checking"
            echo ""
            echo "💡 Frontend commands:"
            echo "  • cd frontend && npm install    # Install frontend dependencies"
            echo "  • cd frontend && npm run dev    # Start React dev server"
            echo "  • cd frontend && npm run build  # Build production frontend"
            echo ""
            echo "💡 Dev Tools commands:"
            echo "  • poetry install --with devtools  # Install dev tools dependencies"
            echo "  • python dev_tools/generate_embeddings.py  # Process RV-C spec PDF"
            echo "  • python dev_tools/query_faiss.py \"query\"  # Search RV-C spec"

            # Setup frontend if frontend directory exists
            if [ -d "frontend" ] && [ ! -d "frontend/node_modules" ]; then
              echo "🔧 Setting up frontend development environment..."
              (cd frontend && npm install)
              echo "✅ Frontend dependencies installed"
            fi
          '';
        };

        ciShell = pkgs.mkShell {
          buildInputs = [
            python
            pkgs.poetry
            pythonPackages.pytest
            pythonPackages.pyyaml
            pythonPackages.uvicorn
            pythonPackages.websockets
            pythonPackages.httptools
            pythonPackages.python-dotenv
            pythonPackages.watchfiles
            pythonPackages.pytest-asyncio
            pkgs.pyright

            # --- Dev Tools dependencies for CI ---
            pythonPackages.langchain
            pythonPackages."langchain-openai"
            pythonPackages.pymupdf  # PyMuPDF, imported as fitz
            pythonPackages."faiss"
            pkgs.nodejs_20
          ] ++ pkgs.lib.optionals (pkgs.stdenv.isLinux || pkgs.stdenv.isDarwin) [
            pythonPackages.uvloop
          ] ++ pkgs.lib.optionals pkgs.stdenv.isLinux [
            pkgs.can-utils
            pythonPackages.pyroute2
            pkgs.iproute2
          ];
          shellHook = ''
            export PYTHONPATH=$PWD:$PYTHONPATH
            echo "🧪 Entered CI shell with vcan support"
            sudo modprobe vcan  || true
            sudo ip link add dev vcan0 type vcan  || true
            sudo ip link set up vcan0  || true
          '';
        };

        apps = {
          precommit = (flake-utils.lib.mkApp {
            drv = pkgs.writeShellApplication {
              name = "precommit";
              runtimeInputs = [ pkgs.poetry ];
              text = ''
                export SKIP=djlint
                poetry install --no-root --with dev
                poetry run pre-commit run --all-files
              '';
            };
          }) // {
            meta = {
              description = "Run pre-commit checks across the repo";
              maintainers = [ "carpenike" ];
              license = pkgs.lib.licenses.asl20;
            };
          };

          test = (flake-utils.lib.mkApp {
            drv = pkgs.writeShellApplication {
              name = "test";
              runtimeInputs = [ pkgs.poetry ];
              text = ''
                poetry install --no-root
                poetry run pytest
              '';
            };
          }) // {
            meta = {
              description = "Run unit tests";
              maintainers = [ "carpenike" ];
              license = pkgs.lib.licenses.asl20;
            };
          };

          lint = (flake-utils.lib.mkApp {
            drv = pkgs.writeShellApplication {
              name = "lint";
              runtimeInputs = [ pkgs.poetry ];
              text = ''
                # Backend linting
                poetry install --no-root
                poetry run ruff check .
                poetry run pyright backend

                # Frontend linting (if frontend directory exists)
                if [ -d "frontend" ]; then
                  cd frontend
                  npm run lint
                  npm run typecheck
                fi
              '';
            };
          }) // {
            meta = {
              description = "Run Python and frontend linters";
              maintainers = [ "carpenike" ];
              license = pkgs.lib.licenses.asl20;
            };
          };

          format = (flake-utils.lib.mkApp {
            drv = pkgs.writeShellApplication {
              name = "format";
              runtimeInputs = [ pkgs.poetry ];
              text = ''
                # Backend formatting
                poetry install --no-root
                poetry run ruff format backend

                # Frontend formatting (if frontend directory exists)
                if [ -d "frontend" ];then
                  cd frontend
                  npm run lint -- --fix
                fi
              '';
            };
          }) // {
            meta = {
              description = "Format Python and frontend code";
              maintainers = [ "carpenike" ];
              license = pkgs.lib.licenses.asl20;
            };
          };

          build-frontend = (flake-utils.lib.mkApp {
            drv = pkgs.writeShellApplication {
              name = "build-frontend";
              runtimeInputs = [ pkgs.nodejs_20 ];
              text = ''
                if [ ! -d "frontend" ]; then
                  echo "Error: frontend directory not found"
                  exit 1
                fi

                cd frontend
                echo "📦 Installing frontend dependencies..."
                npm ci
                echo "🏗️ Building frontend..."
                npm run build

                echo "✅ Frontend built successfully to frontend/dist/"
                echo "To deploy, copy the dist directory to your webserver"
              '';
            };
          }) // {
            meta = {
              description = "Build the frontend (React) application";
              maintainers = [ "carpenike" ];
              license = pkgs.lib.licenses.asl20;
            };
          };

          ci = (flake-utils.lib.mkApp {
            drv = pkgs.writeShellApplication {
              name = "ci";
              runtimeInputs = [ pkgs.poetry pkgs.nodejs_20 ];
              text = ''
                set -e
                export SKIP=djlint
                poetry install --no-root --with dev
                poetry check --lock --no-interaction

                # Frontend deps must be installed before pre-commit
                if [ -d "frontend" ]; then
                  echo "🔍 Installing frontend dependencies..."
                  cd frontend
                  npm ci
                  cd ..
                fi

                poetry run pre-commit run --all-files

                # Frontend checks
                # if [ -d "frontend" ]; then
                #   echo "🔍 Running frontend checks..."
                #   cd frontend
                #   npm run lint
                #   npm run typecheck
                #   npm run build
                #   cd ..
                # fi
              '';
            };
          }) // {
            meta = {
              description = "Run the full CI suite (pre-commit, tests, lint, build)";
              maintainers = [ "carpenike" ];
              license = pkgs.lib.licenses.asl20;
            };
          };
        };

        checks = {
          # only lock‑file validation in `nix flake check`
          poetry-lock-check = pkgs.runCommand "poetry-lock-check" {
            src         = ./.;
            buildInputs = [ pkgs.poetry ];
          } ''
            cd $src
            poetry check --lock --no-interaction
            touch $out
          '';
        };
      in {
        packages = {
          coachiq = coachiqPackage;
          default = coachiqPackage;
          frontend = pkgs.buildNpmPackage {
            pname = "coachiq-frontend";
            inherit version;
            src = ./frontend;

            npmDepsHash = "sha256-iJcUkGCi+ALmVkAQ/fu0EzsDGRLQZr+8F+ZuuL4EG/s=";

            nativeBuildInputs = [
              pkgs.nodejs_20
              pkgs.python3
              pkgs.pkg-config
            ] ++ pkgs.lib.optionals pkgs.stdenv.isDarwin [
              pkgs.darwin.apple_sdk.frameworks.Security
            ] ++ pkgs.lib.optionals pkgs.stdenv.isLinux [
              pkgs.libsecret
            ];

            # Use Vite directly to avoid TypeScript path resolution issues
            buildPhase = ''
              runHook preBuild
              npx vite build
              runHook postBuild
            '';

            installPhase = ''
              mkdir -p $out
              cp -r dist/* $out/
            '';

            meta = {
              description = "CoachIQ React frontend static files (built with Vite)";
              license = pkgs.lib.licenses.mit;
              platforms = pkgs.lib.platforms.unix;
            };
          };
        };

        devShells = {
          default = devShell;
          ci      = ciShell;
        };

        inherit apps checks;
      }
    ) //
    {
      nixosModules.coachiq = { config, lib, pkgs, ... }: {
        options.coachiq = {
          enable = lib.mkEnableOption "Enable CoachIQ RV-C network server";

          package = lib.mkOption {
            type = lib.types.package;
            default = self.packages.${pkgs.system}.coachiq;
            description = "The CoachIQ package to use";
          };

          settings = {
            # App metadata
            appName = lib.mkOption {
              type = lib.types.str;
              default = "rvc2api";
              description = "Application name";
            };

            appVersion = lib.mkOption {
              type = lib.types.str;
              default = "0.0.0";
              description = "Application version";
            };

            appDescription = lib.mkOption {
              type = lib.types.str;
              default = "API for RV-C CANbus";
              description = "Application description";
            };

            appTitle = lib.mkOption {
              type = lib.types.str;
              default = "RV-C API";
              description = "API title for documentation";
            };

            # Server configuration
            server = {
              host = lib.mkOption {
                type = lib.types.str;
                default = "0.0.0.0";
                description = "Host to bind the server to";
              };

              port = lib.mkOption {
                type = lib.types.int;
                default = 8000;
                description = "Port to bind the server to";
              };

              workers = lib.mkOption {
                type = lib.types.int;
                default = 1;
                description = "Number of worker processes";
              };

              reload = lib.mkOption {
                type = lib.types.bool;
                default = false;
                description = "Enable auto-reload for development";
              };

              debug = lib.mkOption {
                type = lib.types.bool;
                default = false;
                description = "Enable debug mode";
              };

              rootPath = lib.mkOption {
                type = lib.types.str;
                default = "";
                description = "Root path for the application";
              };

              accessLog = lib.mkOption {
                type = lib.types.bool;
                default = true;
                description = "Enable access logging";
              };

              keepAliveTimeout = lib.mkOption {
                type = lib.types.int;
                default = 5;
                description = "Keep-alive timeout in seconds";
              };

              timeoutGracefulShutdown = lib.mkOption {
                type = lib.types.int;
                default = 30;
                description = "Graceful shutdown timeout";
              };

              limitConcurrency = lib.mkOption {
                type = lib.types.nullOr lib.types.int;
                default = null;
                description = "Maximum number of concurrent connections";
              };

              limitMaxRequests = lib.mkOption {
                type = lib.types.nullOr lib.types.int;
                default = null;
                description = "Maximum number of requests before worker restart";
              };

              timeoutNotify = lib.mkOption {
                type = lib.types.int;
                default = 30;
                description = "Timeout for worker startup notification";
              };

              # SSL/TLS settings
              sslKeyfile = lib.mkOption {
                type = lib.types.nullOr lib.types.str;
                default = null;
                description = "SSL key file path";
              };

              sslCertfile = lib.mkOption {
                type = lib.types.nullOr lib.types.str;
                default = null;
                description = "SSL certificate file path";
              };

              sslCaCerts = lib.mkOption {
                type = lib.types.nullOr lib.types.str;
                default = null;
                description = "SSL CA certificates file path";
              };

              sslCertReqs = lib.mkOption {
                type = lib.types.int;
                default = 0;
                description = "SSL certificate verification mode (0=CERT_NONE, 1=CERT_OPTIONAL, 2=CERT_REQUIRED)";
              };

              workerClass = lib.mkOption {
                type = lib.types.str;
                default = "uvicorn.workers.UvicornWorker";
                description = "Worker class to use";
              };

              workerConnections = lib.mkOption {
                type = lib.types.int;
                default = 1000;
                description = "Maximum number of simultaneous clients";
              };

              serverHeader = lib.mkOption {
                type = lib.types.bool;
                default = true;
                description = "Include server header in responses";
              };

              dateHeader = lib.mkOption {
                type = lib.types.bool;
                default = true;
                description = "Include date header in responses";
              };
            };

            # CORS settings
            cors = {
              allowedOrigins = lib.mkOption {
                type = lib.types.listOf lib.types.str;
                default = [ "*" ];
                description = "Allowed origins for CORS";
              };

              allowedCredentials = lib.mkOption {
                type = lib.types.bool;
                default = true;
                description = "Allow credentials in CORS";
              };

              allowedMethods = lib.mkOption {
                type = lib.types.listOf lib.types.str;
                default = [ "*" ];
                description = "Allowed methods for CORS";
              };

              allowedHeaders = lib.mkOption {
                type = lib.types.listOf lib.types.str;
                default = [ "*" ];
                description = "Allowed headers for CORS";
              };
            };

            # Security settings
            security = {
              secretKey = lib.mkOption {
                type = lib.types.nullOr lib.types.str;
                default = null;
                description = "Secret key for JWT tokens";
              };

              jwtAlgorithm = lib.mkOption {
                type = lib.types.str;
                default = "HS256";
                description = "JWT algorithm";
              };

              jwtExpireMinutes = lib.mkOption {
                type = lib.types.int;
                default = 30;
                description = "JWT token expiration in minutes";
              };
            };

            # Logging settings
            logging = {
              level = lib.mkOption {
                type = lib.types.str;
                default = "INFO";
                description = "Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)";
              };

              format = lib.mkOption {
                type = lib.types.str;
                default = "%(asctime)s - %(name)s - %(levelname)s - %(message)s";
                description = "Log message format";
              };

              logToFile = lib.mkOption {
                type = lib.types.bool;
                default = false;
                description = "Enable file logging";
              };

              logFile = lib.mkOption {
                type = lib.types.nullOr lib.types.str;
                default = null;
                description = "Log file path";
              };

              maxFileSize = lib.mkOption {
                type = lib.types.int;
                default = 10485760;
                description = "Max log file size in bytes (10MB)";
              };

              backupCount = lib.mkOption {
                type = lib.types.int;
                default = 5;
                description = "Number of backup log files to keep";
              };
            };

            # CAN bus settings
            canbus = {
              bustype = lib.mkOption {
                type = lib.types.str;
                default = "virtual";
                description = ''
                  CAN bus type. Options:
                  - "virtual": Cross-platform virtual CAN (recommended for development)
                  - "socketcan": Linux-only socketcan interface
                  - "pcan": PEAK CAN hardware
                '';
              };

              channels = lib.mkOption {
                type = lib.types.listOf lib.types.str;
                default = [ "virtual0" ];
                description = ''
                  CAN channels to use.
                  Default is [ "virtual0" ] for cross-platform development.
                  For Linux with socketcan: [ "can0" ] or [ "vcan0" ]
                  For multiple interfaces: [ "can0" "can1" ]
                '';
              };

              bitrate = lib.mkOption {
                type = lib.types.int;
                default = 500000;
                description = "CAN bus bitrate (RV-C standard is 500000)";
              };

              interfaceMappings = lib.mkOption {
                type = lib.types.attrsOf lib.types.str;
                default = { house = "can0"; chassis = "can1"; };
                description = ''
                  Logical to physical CAN interface mappings.
                  Maps logical interface names (used in coach configs) to physical interfaces.
                  Example: { house = "can0"; chassis = "can1"; engine = "can2"; }
                '';
              };
            };

            # Persistence settings
            persistence = {
              enabled = lib.mkOption {
                type = lib.types.bool;
                default = false;
                description = "Enable data persistence";
              };

              dataDir = lib.mkOption {
                type = lib.types.str;
                default = "/var/lib/coachiq";
                description = "Base directory for persistent data storage";
              };

              createDirs = lib.mkOption {
                type = lib.types.bool;
                default = true;
                description = "Automatically create data directories if they don't exist";
              };

              backupEnabled = lib.mkOption {
                type = lib.types.bool;
                default = true;
                description = "Enable automatic backups";
              };

              backupRetentionDays = lib.mkOption {
                type = lib.types.int;
                default = 30;
                description = "Number of days to retain backups (1-365)";
              };

              maxBackupSizeMb = lib.mkOption {
                type = lib.types.int;
                default = 500;
                description = "Maximum backup size in MB (1-10000)";
              };
            };

            # Feature flags
            features = {
              enableMaintenanceTracking = lib.mkOption {
                type = lib.types.bool;
                default = false;
                description = "Enable maintenance tracking features";
              };

              enableNotifications = lib.mkOption {
                type = lib.types.bool;
                default = false;
                description = "Enable notification services";
              };

              enableUptimerobot = lib.mkOption {
                type = lib.types.bool;
                default = false;
                description = "Enable UptimeRobot integration";
              };

              enablePushover = lib.mkOption {
                type = lib.types.bool;
                default = false;
                description = "Enable Pushover notifications";
              };

              enableVectorSearch = lib.mkOption {
                type = lib.types.bool;
                default = true;
                description = "Enable vector search features";
              };

              enableApiDocs = lib.mkOption {
                type = lib.types.bool;
                default = true;
                description = "Enable API documentation endpoints";
              };

              enableMetrics = lib.mkOption {
                type = lib.types.bool;
                default = true;
                description = "Enable Prometheus metrics";
              };
            };

            # Maintenance settings
            maintenance = {
              checkInterval = lib.mkOption {
                type = lib.types.int;
                default = 3600;
                description = "Check interval in seconds (minimum 60)";
              };

              notificationThresholdDays = lib.mkOption {
                type = lib.types.int;
                default = 7;
                description = "Days before due to send notifications";
              };

              databasePath = lib.mkOption {
                type = lib.types.nullOr lib.types.str;
                default = null;
                description = "Maintenance database path";
              };
            };

            # Notification settings
            notifications = {
              # Pushover settings
              pushoverUserKey = lib.mkOption {
                type = lib.types.nullOr lib.types.str;
                default = null;
                description = "Pushover user key";
              };

              pushoverApiToken = lib.mkOption {
                type = lib.types.nullOr lib.types.str;
                default = null;
                description = "Pushover API token";
              };

              pushoverDevice = lib.mkOption {
                type = lib.types.nullOr lib.types.str;
                default = null;
                description = "Pushover device name";
              };

              pushoverPriority = lib.mkOption {
                type = lib.types.nullOr lib.types.int;
                default = null;
                description = "Pushover message priority (-2 to 2)";
              };

              # UptimeRobot settings
              uptimerobotApiKey = lib.mkOption {
                type = lib.types.nullOr lib.types.str;
                default = null;
                description = "UptimeRobot API key";
              };
            };

            # Legacy compatibility options (for existing deployments)
            pushover = {
              enable = lib.mkOption {
                type = lib.types.bool;
                default = false;
                description = "DEPRECATED: Use features.enablePushover instead";
              };
              apiToken = lib.mkOption {
                type = lib.types.str;
                default = "";
                description = "DEPRECATED: Use notifications.pushoverApiToken instead";
              };
              userKey = lib.mkOption {
                type = lib.types.str;
                default = "";
                description = "DEPRECATED: Use notifications.pushoverUserKey instead";
              };
              device = lib.mkOption {
                type = lib.types.nullOr lib.types.str;
                default = null;
                description = "DEPRECATED: Use notifications.pushoverDevice instead";
              };
              priority = lib.mkOption {
                type = lib.types.nullOr lib.types.int;
                default = null;
                description = "DEPRECATED: Use notifications.pushoverPriority instead";
              };
            };

            uptimerobot = {
              enable = lib.mkOption {
                type = lib.types.bool;
                default = false;
                description = "DEPRECATED: Use features.enableUptimerobot instead";
              };
              apiKey = lib.mkOption {
                type = lib.types.str;
                default = "";
                description = "DEPRECATED: Use notifications.uptimerobotApiKey instead";
              };
            };

            # File paths
            rvcSpecPath = lib.mkOption {
              type = lib.types.nullOr lib.types.str;
              default = null;
              description = "Override path to rvc.json (RVC spec file)";
            };

            rvcCoachMappingPath = lib.mkOption {
              type = lib.types.nullOr lib.types.str;
              default = null;
              description = "Coach mapping file path";
            };

            rvcCoachModel = lib.mkOption {
              type = lib.types.nullOr lib.types.str;
              default = null;
              description = ''
                RV-C coach model for automatic mapping selection.
                Example: "2021_Entegra_Aspire_44R"
                If set, will load the corresponding coach mapping file with interface requirements.
              '';
            };

            staticDir = lib.mkOption {
              type = lib.types.str;
              default = "static";
              description = "Static files directory";
            };

            deviceMappingPath = lib.mkOption {
              type = lib.types.nullOr lib.types.str;
              default = null;
              description = "Override path to coach_mapping.default.yml or a model-specific mapping file. If not set, uses modelSelector if provided.";
            };

            modelSelector = lib.mkOption {
              type = lib.types.nullOr lib.types.str;
              default = null;
              description = ''
                Model selector for coach mapping file. Example: "2021_Entegra_Aspire_44R" will use
                "${config.coachiq.package}/share/rvc2api/mappings/" + config.coachiq.settings.modelSelector + ".yml" as the mapping file if deviceMappingPath is not set.
                If both are unset, falls back to coach_mapping.default.yml.
              '';
            };

            userCoachInfoPath = lib.mkOption {
              type = lib.types.nullOr lib.types.str;
              default = null;
              description = "Path to user coach info YAML file";
            };

            # Legacy server configuration (for backward compatibility)
            host = lib.mkOption {
              type = lib.types.str;
              default = "0.0.0.0";
              description = "DEPRECATED: Use server.host instead - Host IP to bind the API server to";
            };

            port = lib.mkOption {
              type = lib.types.int;
              default = 8000;
              description = "DEPRECATED: Use server.port instead - Port to run the API server on";
            };

            logLevel = lib.mkOption {
              type = lib.types.str;
              default = "INFO";
              description = "DEPRECATED: Use logging.level instead - Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)";
            };

            # Controller configuration
            controllerSourceAddr = lib.mkOption {
              type = lib.types.str;
              default = "0xF9";
              description = "Controller source address in hex (default: 0xF9)";
            };

            # GitHub update checker
            githubUpdateRepo = lib.mkOption {
              type = lib.types.nullOr lib.types.str;
              default = null;
              description = "GitHub repository to check for updates (format: owner/repo)";
            };
          };
        };

        config = lib.mkIf config.coachiq.enable {
          # Include the package in systemPackages
          environment.systemPackages = [ config.coachiq.package ];

          # Create persistent data directory with proper permissions
          systemd.tmpfiles.rules = lib.mkIf config.coachiq.settings.persistence.enabled [
            "d ${config.coachiq.settings.persistence.dataDir} 0755 coachiq coachiq -"
            "d ${config.coachiq.settings.persistence.dataDir}/database 0755 coachiq coachiq -"
            "d ${config.coachiq.settings.persistence.dataDir}/backups 0755 coachiq coachiq -"
            "d ${config.coachiq.settings.persistence.dataDir}/config 0755 coachiq coachiq -"
            "d ${config.coachiq.settings.persistence.dataDir}/themes 0755 coachiq coachiq -"
            "d ${config.coachiq.settings.persistence.dataDir}/dashboards 0755 coachiq coachiq -"
            "d ${config.coachiq.settings.persistence.dataDir}/logs 0755 coachiq coachiq -"
          ];

          # Create system user for coachiq service
          users.users.coachiq = {
            isSystemUser = true;
            group = "coachiq";
            description = "CoachIQ service user";
          };

          users.groups.coachiq = {};

          # Set up the systemd service
          systemd.services.coachiq = {
            description = "CoachIQ RV-C HTTP/WebSocket API";
            after       = [ "network.target" ];
            wantedBy    = [ "multi-user.target" ];

            serviceConfig = {
              ExecStart = "${config.coachiq.package}/bin/coachiq-daemon";
              Restart    = "always";
              RestartSec = 5;
              User = "coachiq";
              Group = "coachiq";
              # Ensure the service can access CAN interfaces if needed
              SupplementaryGroups = [ "dialout" ];
            };

            environment = lib.filterAttrs (n: v: v != null) ({
              # Always set environment (for production deployment)
              COACHIQ_ENVIRONMENT = "production";

              # App metadata - only if explicitly configured
              COACHIQ_APP_NAME = lib.mkIf (config.coachiq.settings.appName != "rvc2api") config.coachiq.settings.appName;
              COACHIQ_APP_VERSION = lib.mkIf (config.coachiq.settings.appVersion != "0.0.0") config.coachiq.settings.appVersion;

              # Server settings - only if different from defaults or necessary for production
              COACHIQ_SERVER__HOST = lib.mkIf (config.coachiq.settings.server.host != "0.0.0.0") config.coachiq.settings.server.host;
              COACHIQ_SERVER__PORT = lib.mkIf (config.coachiq.settings.server.port != 8000) (toString config.coachiq.settings.server.port);
              COACHIQ_SERVER__WORKERS = lib.mkIf (config.coachiq.settings.server.workers > 1) (toString config.coachiq.settings.server.workers);

              # Never set reload in production - let application handle this based on environment
              # COACHIQ_SERVER__RELOAD is intentionally not set here

              # CORS - only if not using defaults
              COACHIQ_CORS__ALLOW_ORIGINS = lib.mkIf
                (config.coachiq.settings.cors.allowedOrigins != ["*"])
                (lib.concatStringsSep "," config.coachiq.settings.cors.allowedOrigins);

              # Security - only if provided
              COACHIQ_SECURITY__SECRET_KEY = lib.mkIf (config.coachiq.settings.security.secretKey != null) config.coachiq.settings.security.secretKey;

              # Logging - only if explicitly set
              COACHIQ_LOGGING__LEVEL = lib.mkIf (config.coachiq.settings.logging.level != "INFO") config.coachiq.settings.logging.level;
              COACHIQ_LOGGING__LOG_FILE = lib.mkIf (config.coachiq.settings.logging.logFile != null) config.coachiq.settings.logging.logFile;

              # CAN settings - only if not default
              COACHIQ_CAN__BUSTYPE = lib.mkIf (config.coachiq.settings.canbus.bustype != "virtual") config.coachiq.settings.canbus.bustype;
              COACHIQ_CAN__INTERFACES = lib.mkIf
                (config.coachiq.settings.canbus.channels != ["virtual0"])
                (builtins.toJSON config.coachiq.settings.canbus.channels);

              # Persistence - only if enabled
              COACHIQ_PERSISTENCE__ENABLED = lib.mkIf config.coachiq.settings.persistence.enabled "true";
              COACHIQ_PERSISTENCE__DATA_DIR = lib.mkIf
                (config.coachiq.settings.persistence.enabled && config.coachiq.settings.persistence.dataDir != "/var/lib/coachiq")
                config.coachiq.settings.persistence.dataDir;

              # Features - only if different from defaults
              COACHIQ_FEATURES__ENABLE_MAINTENANCE_TRACKING = lib.mkIf config.coachiq.settings.features.enableMaintenanceTracking "true";
              COACHIQ_FEATURES__ENABLE_NOTIFICATIONS = lib.mkIf config.coachiq.settings.features.enableNotifications "true";
              COACHIQ_FEATURES__ENABLE_VECTOR_SEARCH = lib.mkIf (!config.coachiq.settings.features.enableVectorSearch) "false";
              COACHIQ_FEATURES__ENABLE_API_DOCS = lib.mkIf (!config.coachiq.settings.features.enableApiDocs) "false";
              COACHIQ_FEATURES__ENABLE_METRICS = lib.mkIf (!config.coachiq.settings.features.enableMetrics) "false";

              # Optional paths - only if provided
              COACHIQ_RVC_SPEC_PATH = lib.mkIf (config.coachiq.settings.rvcSpecPath != null) config.coachiq.settings.rvcSpecPath;
              COACHIQ_RVC_COACH_MAPPING_PATH = lib.mkIf (config.coachiq.settings.rvcCoachMappingPath != null) config.coachiq.settings.rvcCoachMappingPath;
              COACHIQ_RVC__COACH_MODEL = lib.mkIf (config.coachiq.settings.rvcCoachModel != null) config.coachiq.settings.rvcCoachModel;

              # GitHub update repo - only if provided
              COACHIQ_GITHUB_UPDATE_REPO = lib.mkIf (config.coachiq.settings.githubUpdateRepo != null) config.coachiq.settings.githubUpdateRepo;

              # Legacy compatibility - only if using non-default values
              COACHIQ_HOST = lib.mkIf (config.coachiq.settings.host != "0.0.0.0") config.coachiq.settings.host;
              COACHIQ_PORT = lib.mkIf (config.coachiq.settings.port != 8000) (toString config.coachiq.settings.port);
            });
          };
        };
      };
    };
}
