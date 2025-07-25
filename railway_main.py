#!/usr/bin/env python3
"""
Railway Deployment Entry Point

This is the main entry point for Railway deployment.
It launches the Railway-optimized Gradio UI with multi-user support.
"""

import sys
import os
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def main():
    """Main entry point for Railway deployment"""
    print("🚀 Starting AI Tutor for Railway...")
    
    # Import and run Railway UI
    from ui.gradio_ui_railway import main as railway_main
    railway_main()

if __name__ == "__main__":
    main()
