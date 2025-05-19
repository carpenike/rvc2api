#!/usr/bin/env bash

# Helper script for managing documentation versions with mike
# Standard bash script for cross-platform compatibility

# Better error handling
set -e          # Exit on error
set -o pipefail # Exit on pipe failure

function show_help() {
    echo "Documentation Versioning Helper Script"
    echo ""
    echo "Usage:"
    echo "  ./docs_version.sh [command]"
    echo ""
    echo "Commands:"
    echo "  serve         Start mike server with versioned documentation"
    echo "  list          List all currently deployed versions"
    echo "  deploy        Deploy current version from pyproject.toml"
    echo "  deploy-dev    Deploy current state as 'dev' version"
    echo "  set-default   Set version from pyproject.toml as default"
    echo "  help          Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./docs_version.sh serve     # Start versioned docs server"
    echo "  ./docs_version.sh deploy    # Deploy version from pyproject.toml"
}

function ensure_dependencies() {
    # Redirect stderr for this function
    exec 2>/dev/null

    if ! command -v poetry &> /dev/null; then
        echo "Error: Poetry is not installed. Please install it first."
        echo "See: https://python-poetry.org/docs/#installation"
        return 1
    fi

    # Check if mike is importable in Python (better check than pip list)
    if ! poetry run python -c "import mike" 2>/dev/null; then
        echo "Error: 'mike' is not installed in the poetry environment."
        echo "Installing mike..."
        poetry add --group dev mike 2>/dev/null || true
    fi
}

# Get the current version from pyproject.toml
function get_version() {
    # Extract version from pyproject.toml using grep and cut
    version=$(grep -m 1 "^version" pyproject.toml | cut -d= -f2 | tr -d ' "')
    echo "$version"
}

if ! ensure_dependencies; then
    exit 1
fi

# Process command
case "$1" in
    "serve")
        echo "Starting versioned documentation server..."
        poetry run mike serve
        ;;

    "list")
        echo "Listing available documentation versions..."
        poetry run mike list
        ;;

    "deploy")
        current_version=$(get_version)
        if [ -n "$current_version" ]; then
            echo "Deploying documentation version $current_version..."
            poetry run mike deploy --push --update-aliases latest "$current_version"
        else
            echo "Error: Could not extract version from pyproject.toml"
            exit 1
        fi
        ;;

    "deploy-dev")
        echo "Deploying 'dev' documentation version..."
        poetry run mike deploy --push dev
        ;;

    "set-default")
        current_version=$(get_version)
        if [ -n "$current_version" ]; then
            echo "Setting version $current_version as default..."
            poetry run mike set-default --push latest
        else
            echo "Error: Could not extract version from pyproject.toml"
            exit 1
        fi
        ;;

    "help"|"")
        show_help
        ;;

    *)
        echo "Unknown command: $1"
        show_help
        exit 1
        ;;
esac
