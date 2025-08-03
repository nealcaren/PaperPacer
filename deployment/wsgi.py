#!/usr/bin/env python3
"""
WSGI entry point for production deployment
"""

import os
import sys
# Add parent directory to path so we can import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app

if __name__ == "__main__":
    app.run()