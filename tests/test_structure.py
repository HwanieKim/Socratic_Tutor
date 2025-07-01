#!/usr/bin/env python3
"""
Simple test for the organized project structure
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """Test that all modules can be imported correctly"""
    print("Testing imports...")
    
    try:
        from src.core.tutor_engine import TutorEngine
        print("PASS - TutorEngine import")
    except ImportError as e:
        print(f"FAIL - TutorEngine import: {e}")
        return False
    
    try:
        from src.core.models import ReasoningTriplet
        print("PASS - ReasoningTriplet import")
    except ImportError as e:
        print(f"FAIL - ReasoningTriplet import: {e}")
        return False
    
    try:
        from src.core import config
        print("PASS - config import")
        print(f"Model: {config.GEMINI_MODEL_NAME}")
    except ImportError as e:
        print(f"FAIL - config import: {e}")
        return False
    
    try:
        from src.core.production_enhancements import ProductionTutorEngine
        print("PASS - ProductionTutorEngine import")
    except ImportError as e:
        print(f"FAIL - ProductionTutorEngine import: {e}")
        return False
    
    return True

def test_basic_functionality():
    """Test basic system functionality"""
    print("\nTesting basic functionality...")
    
    try:
        from src.core.tutor_engine import TutorEngine
        
        # Initialize engine
        engine = TutorEngine()
        print("PASS - Engine initialization")
        
        # Test input validation
        response = engine.get_guidance("")
        if "Please ask me a question" in response:
            print("PASS - Empty input handling")
        else:
            print("FAIL - Empty input handling")
            return False
        
        # Test normal input
        response = engine.get_guidance("What is sustainable design?")
        if len(response) > 0 and "sustainable" in response.lower():
            print("PASS - Normal input processing")
        else:
            print("FAIL - Normal input processing")
            return False
        
        return True
        
    except Exception as e:
        print(f"FAIL - Basic functionality test: {e}")
        return False

def main():
    """Run all tests"""
    print("RAG Tutor - Structure Organization Test")
    print("=" * 50)
    
    import_test = test_imports()
    
    if import_test:
        functionality_test = test_basic_functionality()
        
        if functionality_test:
            print("\nAll tests PASSED!")
            print("Project structure is working correctly.")
            return 0
        else:
            print("\nFunctionality tests FAILED!")
            return 1
    else:
        print("\nImport tests FAILED!")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
