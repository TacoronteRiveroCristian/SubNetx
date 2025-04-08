#!/usr/bin/env python3
"""
Host Metrics CLI Tool.

A simple command-line tool to collect metrics from a target host.
"""

import sys
import os

# Ensure the current directory is in the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the main function and execute it
from main import main

if __name__ == "__main__":
    main()
