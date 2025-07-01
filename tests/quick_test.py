#!/usr/bin/env python3
"""
Simple demo test for the RAG-based sustainable design tutor
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.tutor_engine import TutorEngine

def demo_test():
    """Simple demo test to verify the tutor is working"""
    print("Testing Sustainable Design Tutor Demo...")
    
    engine = TutorEngine()
    
    # Test basic functionality
    print("\nTesting basic question:")
    response = engine.get_guidance("What is sustainable design?")
    print(f"Response received: {len(response)} characters")
    
    # Test follow-up
    print("\nTesting follow-up question:")
    response = engine.get_guidance("Can you give me an example?")
    print(f"Response received: {len(response)} characters")
    
    print("\nDemo test completed successfully!")
    print("To run the full application, use: python main.py")

if __name__ == "__main__":
    demo_test()
