#!/usr/bin/env fish

# Helper script for managing documentation versions with mike
# Specifically designed for fish shell compatibility

function show_help
    echo "Documentation Versioning Helper Script"
    echo ""
    echo "Usage:"
    echo "  ./docs_version.fish [command]"
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
    echo "  ./docs_version.fish serve     # Start versioned docs server"
    echo "  ./docs_version.fish deploy    # Deploy version from pyproject.toml"
end

function ensure_dependencies
    if not command -v poetry >/dev/null
        echo "Error: Poetry is not installed. Please install it first."
        echo "See: https://python-poetry.org/docs/#installation"
        return 1
    end

    # Check if mike is installed in the poetry environment
    if not poetry run pip list | grep -q mike
        echo "Error: 'mike' is not installed in the poetry environment."
        echo "Installing mike..."
        poetry add --group dev mike
    end
end

if not ensure_dependencies
    exit 1
end

# Process command
switch "$argv[1]"
    case "serve"
        echo "Starting versioned documentation server..."
        poetry run mike serve

    case "list"
        echo "Listing available documentation versions..."
        poetry run mike list

    case "deploy"
        # Extract version from pyproject.toml
        set current_version (grep -m 1 "^version" pyproject.toml | cut -d= -f2 | tr -d ' "')
        if test -n "$current_version"
            echo "Deploying documentation version $current_version..."
            poetry run mike deploy $current_version --push
        else
            echo "Error: Could not extract version from pyproject.toml"
            exit 1
        end

    case "deploy-dev"
        echo "Deploying 'dev' documentation version..."
        poetry run mike deploy dev --push

    case "set-default"
        # Extract version from pyproject.toml
        set current_version (grep -m 1 "^version" pyproject.toml | cut -d= -f2 | tr -d ' "')
        if test -n "$current_version"
            echo "Setting version $current_version as default..."
            poetry run mike set-default $current_version --push
        else
            echo "Error: Could not extract version from pyproject.toml"
            exit 1
        end

    case "help" ""
        show_help

    case "*"
        echo "Unknown command: $argv[1]"
        show_help
        exit 1
end
