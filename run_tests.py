#!/usr/bin/env python3
"""
Simple test runner for the RAG-based sustainable design tutor demo
"""

import sys
import os
import subprocess

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def run_demo_test():
    """Run the simple demo test"""
    print("Running Sustainable Design Tutor Demo Test")
    print("=" * 50)
    
    try:
        test_path = os.path.join(project_root, 'tests', 'quick_test.py')
        result = subprocess.run([sys.executable, test_path], 
                              capture_output=True, text=True, cwd=project_root)
        
        if result.returncode == 0:
            print("Demo test PASSED")
            print(result.stdout)
            return True
        else:
            print("Demo test FAILED")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
        
    except Exception as e:
        print(f"Error running demo test: {e}")
        return False

def main():
    """Run the demo test"""
    success = run_demo_test()
    
    print("\n" + "="*50)
    if success:
        print("Demo test completed successfully!")
        print("To run the full application: python main.py")
        return 0
    else:
        print("⚠️ Demo test failed.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
