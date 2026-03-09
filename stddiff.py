#!/usr/bin/env python3
import os
import sys

# Ensure the core/cli modules are discoverable when running stddiff.py directly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cli.main import main

if __name__ == "__main__":
    main()
