#!/usr/bin/env python3
"""
Quick launcher for the production UI
Run this from the project root directory
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

if __name__ == "__main__":
    from ui.gradio_ui_production import main
    main()
