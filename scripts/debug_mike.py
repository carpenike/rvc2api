#!/usr/bin/env python3
import importlib.metadata
import inspect
import sys

# Get installed mike version
try:
    mike_version = importlib.metadata.version("mike")
    print(f"Installed mike version: {mike_version}")
except importlib.metadata.PackageNotFoundError:
    print("Mike package is not installed")
    sys.exit(1)

# Try to import mike and diagnose the issue
try:
    import mike

    print(f"Mike module imported successfully: {mike}")

    # Try to access the problematic attribute
    from mike import git_utils

    # Print all attributes of git_utils to help diagnose
    print("\nGit utils attributes:")
    for attr_name in dir(git_utils):
        if not attr_name.startswith("__"):
            attr = getattr(git_utils, attr_name)
            if callable(attr):
                print(f"  {attr_name}: {inspect.signature(attr)}")
            else:
                print(f"  {attr_name}: {type(attr)}")

    # Check if there's a template loader or environment function
    from mike import templates

    print("\nTemplate attributes:")
    for attr_name in dir(templates):
        if not attr_name.startswith("__"):
            attr = getattr(templates, attr_name)
            if callable(attr):
                print(f"  {attr_name}: {inspect.signature(attr)}")
            else:
                print(f"  {attr_name}: {type(attr)}")

except ImportError as e:
    print(f"Failed to import mike: {e}")
except Exception as e:
    print(f"Error while examining mike: {e}")
