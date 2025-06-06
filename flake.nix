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
# ▸ Package build output under `packages.<system>.rvc2api`
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
#   nix build .#rvc2api     # Build the package
#
# Usage (in a system flake or NixOS configuration):
#
#   # In your flake inputs:
#   inputs.rvc2api.url = "github:carpenike/rvc2api";
#
#   # As a package:
#   environment.systemPackages = [ inputs.rvc2api.packages.${system}.rvc2api ];
#
#   # As a NixOS module:
#   imports = [ inputs.rvc2api.nixosModules.rvc2api ];
#   # Then configure it:
#   rvc2api.settings = { ... };
#
#   # Or to reference CLI apps:
#   nix run inputs.rvc2api#check
#
# See docs/nixos-integration.md for more details

{
  description = "rvc2api Python package and devShells";

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

        rvc2apiPackage = pythonPackages.buildPythonPackage {
          pname = "rvc2api";
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
            export NODE_PATH=$PWD/web_ui/node_modules

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
            echo "  • cd web_ui && npm install    # Install frontend dependencies"
            echo "  • cd web_ui && npm run dev    # Start React dev server"
            echo "  • cd web_ui && npm run build  # Build production frontend"
            echo ""
            echo "💡 Dev Tools commands:"
            echo "  • poetry install --with devtools  # Install dev tools dependencies"
            echo "  • python dev_tools/generate_embeddings.py  # Process RV-C spec PDF"
            echo "  • python dev_tools/query_faiss.py \"query\"  # Search RV-C spec"

            # Setup frontend if web_ui directory exists
            if [ -d "web_ui" ] && [ ! -d "web_ui/node_modules" ]; then
              echo "🔧 Setting up frontend development environment..."
              (cd web_ui && npm install)
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

                # Frontend linting (if web_ui directory exists)
                if [ -d "web_ui" ]; then
                  cd web_ui
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

                # Frontend formatting (if web_ui directory exists)
                if [ -d "web_ui" ]; then
                  cd web_ui
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
                if [ ! -d "web_ui" ]; then
                  echo "Error: web_ui directory not found"
                  exit 1
                fi

                cd web_ui
                echo "📦 Installing frontend dependencies..."
                npm ci
                echo "🏗️ Building frontend..."
                npm run build

                echo "✅ Frontend built successfully to web_ui/dist/"
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
                if [ -d "web_ui" ]; then
                  echo "🔍 Installing frontend dependencies..."
                  cd web_ui
                  npm ci
                  cd ..
                fi

                poetry run pre-commit run --all-files

                # Frontend checks
                # if [ -d "web_ui" ]; then
                #   echo "🔍 Running frontend checks..."
                #   cd web_ui
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
          rvc2api = rvc2apiPackage;
          default = rvc2apiPackage;
          frontend = pkgs.stdenv.mkDerivation {
            pname = "rvc2api-frontend";
            version = "1.0.0";
            src = ./web_ui;
            buildInputs = [ pkgs.nodejs pkgs.yarn ];
            buildPhase = ''
              export HOME=$TMPDIR
              yarn install --frozen-lockfile || npm install
              yarn build || npm run build
            '';
            installPhase = ''
              mkdir -p $out
              cp -r dist/* $out/
            '';
            meta = {
              description = "rvc2api React frontend static files (built with Vite)";
              license = pkgs.lib.licenses.mit;
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
      nixosModules.rvc2api = { config, lib, pkgs, ... }: {
        options.rvc2api = {
          enable = lib.mkEnableOption "Enable rvc2api RV-C network server";

          package = lib.mkOption {
            type = lib.types.package;
            default = self.packages.${pkgs.system}.rvc2api;
            description = "The rvc2api package to use";
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
                default = "socketcan";
                description = "CAN bus type";
              };

              channels = lib.mkOption {
                type = lib.types.listOf lib.types.str;
                default = [ "vcan0" ];
                description = ''
                  CAN channels to use.
                  Default is [ "vcan0" ].
                  To use multiple interfaces, set to e.g. [ "can0" "can1" ] in your configuration.
                '';
              };

              bitrate = lib.mkOption {
                type = lib.types.int;
                default = 500000;
                description = "CAN bus bitrate";
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
                "${config.rvc2api.package}/share/rvc2api/mappings/" + config.rvc2api.settings.modelSelector + ".yml" as the mapping file if deviceMappingPath is not set.
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

        config = lib.mkIf config.rvc2api.enable {
          # Include the package in systemPackages
          environment.systemPackages = [ config.rvc2api.package ];

          # Set up the systemd service
          systemd.services.rvc2api = {
            description = "RV-C HTTP/WebSocket API";
            after       = [ "network.target" ];
            wantedBy    = [ "multi-user.target" ];

            serviceConfig = {
              ExecStart = "${config.rvc2api.package}/bin/rvc2api-daemon";
              Restart    = "always";
              RestartSec = 5;
            };

            environment = {
              # App metadata
              RVC2API_APP_NAME = config.rvc2api.settings.appName;
              RVC2API_APP_VERSION = config.rvc2api.settings.appVersion;
              RVC2API_APP_DESCRIPTION = config.rvc2api.settings.appDescription;
              RVC2API_APP_TITLE = config.rvc2api.settings.appTitle;

              # Server settings (using new nested structure)
              RVC2API_SERVER__HOST = config.rvc2api.settings.server.host;
              RVC2API_SERVER__PORT = toString config.rvc2api.settings.server.port;
              RVC2API_SERVER__WORKERS = toString config.rvc2api.settings.server.workers;
              RVC2API_SERVER__RELOAD = if config.rvc2api.settings.server.reload then "true" else "false";
              RVC2API_SERVER__DEBUG = if config.rvc2api.settings.server.debug then "true" else "false";
              RVC2API_SERVER__ROOT_PATH = config.rvc2api.settings.server.rootPath;
              RVC2API_SERVER__ACCESS_LOG = if config.rvc2api.settings.server.accessLog then "true" else "false";
              RVC2API_SERVER__KEEP_ALIVE_TIMEOUT = toString config.rvc2api.settings.server.keepAliveTimeout;
              RVC2API_SERVER__TIMEOUT_GRACEFUL_SHUTDOWN = toString config.rvc2api.settings.server.timeoutGracefulShutdown;
              RVC2API_SERVER__WORKER_CLASS = config.rvc2api.settings.server.workerClass;
              RVC2API_SERVER__WORKER_CONNECTIONS = toString config.rvc2api.settings.server.workerConnections;
              RVC2API_SERVER__SERVER_HEADER = if config.rvc2api.settings.server.serverHeader then "true" else "false";
              RVC2API_SERVER__DATE_HEADER = if config.rvc2api.settings.server.dateHeader then "true" else "false";

              # Optional server settings
              RVC2API_SERVER__LIMIT_CONCURRENCY = lib.mkIf (config.rvc2api.settings.server.limitConcurrency != null)
                (toString config.rvc2api.settings.server.limitConcurrency);
              RVC2API_SERVER__LIMIT_MAX_REQUESTS = lib.mkIf (config.rvc2api.settings.server.limitMaxRequests != null)
                (toString config.rvc2api.settings.server.limitMaxRequests);
              RVC2API_SERVER__TIMEOUT_NOTIFY = toString config.rvc2api.settings.server.timeoutNotify;

              # SSL/TLS settings
              RVC2API_SERVER__SSL_KEYFILE = lib.mkIf (config.rvc2api.settings.server.sslKeyfile != null)
                config.rvc2api.settings.server.sslKeyfile;
              RVC2API_SERVER__SSL_CERTFILE = lib.mkIf (config.rvc2api.settings.server.sslCertfile != null)
                config.rvc2api.settings.server.sslCertfile;
              RVC2API_SERVER__SSL_CA_CERTS = lib.mkIf (config.rvc2api.settings.server.sslCaCerts != null)
                config.rvc2api.settings.server.sslCaCerts;
              RVC2API_SERVER__SSL_CERT_REQS = toString config.rvc2api.settings.server.sslCertReqs;

              # CORS settings
              RVC2API_CORS__ALLOWED_ORIGINS = lib.concatStringsSep "," config.rvc2api.settings.cors.allowedOrigins;
              RVC2API_CORS__ALLOWED_CREDENTIALS = if config.rvc2api.settings.cors.allowedCredentials then "true" else "false";
              RVC2API_CORS__ALLOWED_METHODS = lib.concatStringsSep "," config.rvc2api.settings.cors.allowedMethods;
              RVC2API_CORS__ALLOWED_HEADERS = lib.concatStringsSep "," config.rvc2api.settings.cors.allowedHeaders;

              # Security settings
              RVC2API_SECURITY__SECRET_KEY = lib.mkIf (config.rvc2api.settings.security.secretKey != null)
                config.rvc2api.settings.security.secretKey;
              RVC2API_SECURITY__JWT_ALGORITHM = config.rvc2api.settings.security.jwtAlgorithm;
              RVC2API_SECURITY__JWT_EXPIRE_MINUTES = toString config.rvc2api.settings.security.jwtExpireMinutes;

              # Logging settings
              RVC2API_LOGGING__LEVEL = config.rvc2api.settings.logging.level;
              RVC2API_LOGGING__FORMAT = config.rvc2api.settings.logging.format;
              RVC2API_LOGGING__LOG_TO_FILE = if config.rvc2api.settings.logging.logToFile then "true" else "false";
              RVC2API_LOGGING__LOG_FILE = lib.mkIf (config.rvc2api.settings.logging.logFile != null)
                config.rvc2api.settings.logging.logFile;
              RVC2API_LOGGING__MAX_FILE_SIZE = toString config.rvc2api.settings.logging.maxFileSize;
              RVC2API_LOGGING__BACKUP_COUNT = toString config.rvc2api.settings.logging.backupCount;

              # CAN bus settings
              RVC2API_CAN__BUSTYPE = config.rvc2api.settings.canbus.bustype;
              RVC2API_CAN__INTERFACE = config.rvc2api.settings.canbus.channels[0];
              RVC2API_CAN__CHANNELS = lib.concatStringsSep "," config.rvc2api.settings.canbus.channels;
              RVC2API_CAN__BITRATE = toString config.rvc2api.settings.canbus.bitrate;

              # Feature flags
              RVC2API_FEATURES__ENABLE_MAINTENANCE_TRACKING = if config.rvc2api.settings.features.enableMaintenanceTracking then "true" else "false";
              RVC2API_FEATURES__ENABLE_NOTIFICATIONS = if config.rvc2api.settings.features.enableNotifications then "true" else "false";
              RVC2API_FEATURES__ENABLE_UPTIMEROBOT = if config.rvc2api.settings.features.enableUptimerobot then "true" else "false";
              RVC2API_FEATURES__ENABLE_PUSHOVER = if config.rvc2api.settings.features.enablePushover then "true" else "false";
              RVC2API_FEATURES__ENABLE_VECTOR_SEARCH = if config.rvc2api.settings.features.enableVectorSearch then "true" else "false";
              RVC2API_FEATURES__ENABLE_API_DOCS = if config.rvc2api.settings.features.enableApiDocs then "true" else "false";
              RVC2API_FEATURES__ENABLE_METRICS = if config.rvc2api.settings.features.enableMetrics then "true" else "false";

              # Maintenance settings
              RVC2API_MAINTENANCE__CHECK_INTERVAL = toString config.rvc2api.settings.maintenance.checkInterval;
              RVC2API_MAINTENANCE__NOTIFICATION_THRESHOLD_DAYS = toString config.rvc2api.settings.maintenance.notificationThresholdDays;
              RVC2API_MAINTENANCE__DATABASE_PATH = lib.mkIf (config.rvc2api.settings.maintenance.databasePath != null)
                config.rvc2api.settings.maintenance.databasePath;

              # Notification settings
              RVC2API_NOTIFICATIONS__PUSHOVER_USER_KEY = lib.mkIf (config.rvc2api.settings.notifications.pushoverUserKey != null)
                config.rvc2api.settings.notifications.pushoverUserKey;
              RVC2API_NOTIFICATIONS__PUSHOVER_API_TOKEN = lib.mkIf (config.rvc2api.settings.notifications.pushoverApiToken != null)
                config.rvc2api.settings.notifications.pushoverApiToken;
              RVC2API_NOTIFICATIONS__PUSHOVER_DEVICE = lib.mkIf (config.rvc2api.settings.notifications.pushoverDevice != null)
                config.rvc2api.settings.notifications.pushoverDevice;
              RVC2API_NOTIFICATIONS__PUSHOVER_PRIORITY = lib.mkIf (config.rvc2api.settings.notifications.pushoverPriority != null)
                (toString config.rvc2api.settings.notifications.pushoverPriority);
              RVC2API_NOTIFICATIONS__UPTIMEROBOT_API_KEY = lib.mkIf (config.rvc2api.settings.notifications.uptimerobotApiKey != null)
                config.rvc2api.settings.notifications.uptimerobotApiKey;

              # File paths
              RVC2API_RVC_SPEC_PATH = lib.mkIf (config.rvc2api.settings.rvcSpecPath != null)
                config.rvc2api.settings.rvcSpecPath;
              RVC2API_RVC_COACH_MAPPING_PATH = lib.mkIf (config.rvc2api.settings.rvcCoachMappingPath != null)
                config.rvc2api.settings.rvcCoachMappingPath;
              RVC2API_STATIC_DIR = config.rvc2api.settings.staticDir;
              RVC2API_USER_COACH_INFO_PATH = lib.mkIf (config.rvc2api.settings.userCoachInfoPath != null)
                config.rvc2api.settings.userCoachInfoPath;

              # Controller settings
              RVC2API_CONTROLLER_SOURCE_ADDR = config.rvc2api.settings.controllerSourceAddr;

              # GitHub update checker
              RVC2API_GITHUB_UPDATE_REPO = lib.mkIf (config.rvc2api.settings.githubUpdateRepo != null)
                config.rvc2api.settings.githubUpdateRepo;

              # Legacy environment variables (for backward compatibility)
              # Server settings
              RVC2API_HOST = config.rvc2api.settings.host; # Maps to server.host in new config
              RVC2API_PORT = toString config.rvc2api.settings.port; # Maps to server.port in new config
              DEBUG = if config.rvc2api.settings.server.debug then "true" else "false";
              RVC2API_ROOT_PATH = config.rvc2api.settings.server.rootPath;

              # CORS legacy
              CORS_ORIGINS = lib.concatStringsSep "," config.rvc2api.settings.cors.allowedOrigins;

              # Logging legacy
              LOG_LEVEL = config.rvc2api.settings.logging.level;

              # CAN bus legacy
              CAN_CHANNELS = lib.concatStringsSep "," config.rvc2api.settings.canbus.channels;
              CAN_BUSTYPE = config.rvc2api.settings.canbus.bustype;
              CAN_BITRATE = toString config.rvc2api.settings.canbus.bitrate;

              # Legacy Pushover settings (maintain backward compatibility)
              ENABLE_PUSHOVER = if (config.rvc2api.settings.pushover.enable || config.rvc2api.settings.features.enablePushover) then "1" else "0";
              PUSHOVER_API_TOKEN = if config.rvc2api.settings.pushover.apiToken != ""
                then config.rvc2api.settings.pushover.apiToken
                else (lib.mkIf (config.rvc2api.settings.notifications.pushoverApiToken != null) config.rvc2api.settings.notifications.pushoverApiToken);
              PUSHOVER_USER_KEY = if config.rvc2api.settings.pushover.userKey != ""
                then config.rvc2api.settings.pushover.userKey
                else (lib.mkIf (config.rvc2api.settings.notifications.pushoverUserKey != null) config.rvc2api.settings.notifications.pushoverUserKey);
              PUSHOVER_DEVICE = lib.mkIf (config.rvc2api.settings.pushover.device != null || config.rvc2api.settings.notifications.pushoverDevice != null)
                (if config.rvc2api.settings.pushover.device != null
                 then config.rvc2api.settings.pushover.device
                 else config.rvc2api.settings.notifications.pushoverDevice);
              PUSHOVER_PRIORITY = lib.mkIf (config.rvc2api.settings.pushover.priority != null || config.rvc2api.settings.notifications.pushoverPriority != null)
                (toString (if config.rvc2api.settings.pushover.priority != null
                          then config.rvc2api.settings.pushover.priority
                          else config.rvc2api.settings.notifications.pushoverPriority));

              # Legacy UptimeRobot settings
              ENABLE_UPTIMEROBOT = if (config.rvc2api.settings.uptimerobot.enable || config.rvc2api.settings.features.enableUptimerobot) then "1" else "0";
              UPTIMEROBOT_API_KEY = if config.rvc2api.settings.uptimerobot.apiKey != ""
                then config.rvc2api.settings.uptimerobot.apiKey
                else (lib.mkIf (config.rvc2api.settings.notifications.uptimerobotApiKey != null) config.rvc2api.settings.notifications.uptimerobotApiKey);

              # Controller legacy
              CONTROLLER_SOURCE_ADDR = config.rvc2api.settings.controllerSourceAddr;

              # GitHub legacy
              GITHUB_UPDATE_REPO = lib.mkIf (config.rvc2api.settings.githubUpdateRepo != null)
                config.rvc2api.settings.githubUpdateRepo;

              # Model selector (used by RVC integration if RVC_COACH_MAPPING_PATH isn't set)
              RVC_COACH_MODEL = lib.mkIf (config.rvc2api.settings.modelSelector != null)
                config.rvc2api.settings.modelSelector;

              # RVC spec path
              RVC_SPEC_PATH = lib.mkIf (config.rvc2api.settings.rvcSpecPath != null)
                config.rvc2api.settings.rvcSpecPath;

              # Device mapping path - complex logic to select the right path
              RVC_COACH_MAPPING_PATH =
                if config.rvc2api.settings.deviceMappingPath != null then
                  config.rvc2api.settings.deviceMappingPath
                else if config.rvc2api.settings.modelSelector != null then
                  "${config.rvc2api.package}/lib/python3.12/site-packages/backend/integrations/rvc/config/" +
                  config.rvc2api.settings.modelSelector + ".yml"
                else
                  "${config.rvc2api.package}/lib/python3.12/site-packages/backend/integrations/rvc/config/coach_mapping.default.yml";
            };
          };
        };
      };
    };
}
