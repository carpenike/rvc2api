#!/usr/bin/env python3
"""
Simple entry point to run the rvc2api server.

This script ensures proper module resolution by adding the necessary
paths to PYTHONPATH before importing the main module.
"""
import sys
from pathlib import Path

from core_daemon.main import main

# Add the src directory to the path
src_dir = str(Path(__file__).parent / "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

if __name__ == "__main__":
    main()
