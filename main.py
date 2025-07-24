#!/usr/bin/env python3
"""
PolyGlot Socratic Tutor - Main Entry Point

A Socratic tutoring system that guides students through document-based learning
using AI-powered questioning and progressive scaffolding.
"""

import sys
import os

# Add src to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

def main():
    """Main entry point for the PolyGlot Socratic Tutor"""
    print("🎓 Starting PolyGlot Socratic Tutor...")
    print("📚 An AI-powered Socratic learning assistant")
    print("=" * 50)
    
    try:
        # Import and run the production UI
        from ui.gradio_ui_production import main as ui_main
        ui_main()
    except KeyboardInterrupt:
        print("\n👋 Goodbye! Thanks for using PolyGlot Socratic Tutor!")
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        print("📝 Please check your environment setup and try again.")
        sys.exit(1)

if __name__ == "__main__":
    main()
