#!/usr/bin/env python3
"""
RAG-based Sustainable Design Tutor - Main Entry Point

This is the main entry point for running the production version
of the RAG-based Sustainable Design Tutor system.
"""

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def main():
    """Main entry point for the application"""
    print("RAG-based Sustainable Design Tutor")
    print("=" * 50)
    print("Starting the production version...")
    
    try:
        # Import and run the production UI
        from ui.gradio_ui_production import main as ui_main
        ui_main()
    except ImportError as e:
        print(f"Import error: {e}")
        print("Make sure all dependencies are installed.")
        return 1
    except Exception as e:
        print(f"Error starting application: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
