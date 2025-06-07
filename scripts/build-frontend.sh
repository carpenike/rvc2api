#!/usr/bin/env bash
# Build script for the React frontend

set -e  # Exit on error

# Determine script location
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

# Display banner
echo "🏗️ rvc2api Frontend Build Tool"
echo "================================"

# Check if we're in a Nix development shell
if [ -n "$IN_NIX_SHELL" ]; then
  echo "✓ Running in Nix development shell"
else
  echo "⚠️ Not running in a Nix shell. Some features may not work correctly."
  echo "   Consider running 'nix develop' first."
fi

# Check for Node.js
if ! command -v node &> /dev/null; then
  echo "❌ Error: Node.js not found. Please install Node.js or use a Nix shell."
  exit 1
fi

# Check for npm
if ! command -v npm &> /dev/null; then
  echo "❌ Error: npm not found. Please install npm or use a Nix shell."
  exit 1
fi

# Check if the frontend directory exists
if [ ! -d "$FRONTEND_DIR" ]; then
  echo "❌ Error: Frontend directory not found at $FRONTEND_DIR"
  exit 1
fi

# Default action
ACTION="build"

# Parse arguments
while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    --dev)
      ACTION="dev"
      shift
      ;;
    --install)
      ACTION="install"
      shift
      ;;
    --lint)
      ACTION="lint"
      shift
      ;;
    --clean)
      ACTION="clean"
      shift
      ;;
    --help)
      echo "Usage: $0 [options]"
      echo ""
      echo "Options:"
      echo "  --dev      Start development server"
      echo "  --install  Install dependencies only"
      echo "  --lint     Run linting checks"
      echo "  --clean    Remove build artifacts and node_modules"
      echo "  --help     Display this help message"
      exit 0
      ;;
    *)
      echo "❌ Unknown option: $key"
      echo "Run '$0 --help' for usage information."
      exit 1
      ;;
  esac
done

# Change to the frontend directory
cd "$FRONTEND_DIR"

# Perform the requested action
case $ACTION in
  "build")
    echo "📦 Installing dependencies..."
    npm ci

    echo "🏗️ Building frontend for production..."
    npm run build

    echo "✅ Frontend built successfully!"
    echo "   Output directory: $FRONTEND_DIR/dist"
    ;;

  "dev")
    echo "🚀 Starting development server..."
    npm run dev
    ;;

  "install")
    echo "📦 Installing dependencies..."
    npm ci
    echo "✅ Dependencies installed successfully!"
    ;;

  "lint")
    echo "🔍 Running lint checks..."
    npm run lint
    echo "✅ Lint checks completed!"
    ;;

  "clean")
    echo "🧹 Cleaning up build artifacts and dependencies..."
    if [ -d "dist" ]; then
      rm -rf dist
    fi
    if [ -d "node_modules" ]; then
      rm -rf node_modules
    fi
    echo "✅ Cleanup complete!"
    ;;
esac
