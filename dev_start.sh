#!/bin/bash

# CoachIQ Development Startup Script
# This script sets up the development environment and starts the server

echo "🚀 Starting CoachIQ Development Server..."

# Set development environment variables
export COACHIQ_ENVIRONMENT=development
export COACHIQ_DEBUG=true

# CAN Configuration for development (virtual CAN)
export COACHIQ_CAN__BUSTYPE=virtual
export COACHIQ_CAN__INTERFACES=virtual0
export COACHIQ_CAN__INTERFACE_MAPPINGS='{"house": "virtual0", "chassis": "virtual0"}'
export COACHIQ_CAN__BITRATE=500000

# Coach Configuration (uncomment to test specific coach)
# export COACHIQ_RVC__COACH_MODEL=2021_Entegra_Aspire_44R

# Server Configuration for development
export COACHIQ_SERVER__HOST=127.0.0.1
export COACHIQ_SERVER__PORT=8000
export COACHIQ_SERVER__RELOAD=true
export COACHIQ_SERVER__DEBUG=true

# Logging Configuration
export COACHIQ_LOGGING__LEVEL=DEBUG

# Persistence Configuration for development
export COACHIQ_PERSISTENCE__ENABLED=true
export COACHIQ_PERSISTENCE__DATA_DIR=backend/data

# CORS Configuration (allow frontend development)
export COACHIQ_CORS__ALLOW_ORIGINS="http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173"

# Feature Flags (enable useful development features)
export COACHIQ_FEATURES__ENABLE_VECTOR_SEARCH=true
export COACHIQ_FEATURES__ENABLE_API_DOCS=true
export COACHIQ_FEATURES__ENABLE_METRICS=true

echo "📡 CAN Configuration:"
echo "  - Bustype: virtual (cross-platform)"
echo "  - Interfaces: virtual0"
echo "  - Interface mapping: house→virtual0, chassis→virtual0"
echo ""

echo "🔧 Server Configuration:"
echo "  - Host: 127.0.0.1:8000"
echo "  - Auto-reload: enabled"
echo "  - Debug mode: enabled"
echo "  - Logging: DEBUG level"
echo ""

echo "📚 Available endpoints:"
echo "  - API docs: http://127.0.0.1:8000/docs"
echo "  - ReDoc: http://127.0.0.1:8000/redoc"
echo "  - Health: http://127.0.0.1:8000/healthz"
echo "  - Metrics: http://127.0.0.1:8000/metrics"
echo ""

# Start the development server
echo "🏃‍♂️ Starting server with auto-reload..."
poetry run python run_server.py --reload --debug
