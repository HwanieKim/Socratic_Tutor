#!/usr/bin/env python3
"""
Gemini 2.5 Flash API Test

This script tests the Gemini 2.5 Flash model configuration
and verifies it's working correctly with the updated settings.
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from llama_index.llms.google_genai import GoogleGenAI
from src.core import config

def test_gemini_25_flash():
    """Test Gemini 2.5 Flash model"""
    print("Testing Gemini 2.5 Flash Configuration...")
    
    # Load environment variables
    load_dotenv()
    
    # Check if API key is available
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("GOOGLE_API_KEY not found in environment variables")
        print("Please set your Google API key in the .env file:")
        print("GOOGLE_API_KEY=your_api_key_here")
        return False
    
    print("API Key found: " + api_key[:10] + "..." + api_key[-4:])
    print("Model: " + config.GEMINI_MODEL_NAME)
    
    try:
        # Initialize Gemini 2.5 Flash
        llm = GoogleGenAI(
            model_name=config.GEMINI_MODEL_NAME,
            api_key=api_key,
            temperature=0.1
        )
        
        # Test simple completion
        print("\n🔄 Testing simple completion...")
        test_prompt = "What is sustainable design? Answer in one sentence."
        response = llm.complete(test_prompt)
        
        print(f"✅ Response: {response.text}")
        
        # Test conversation capabilities
        print("\n🔄 Testing conversation capabilities...")
        conversation_prompt = ("You are a helpful tutor. "
                              "Explain the concept of lifecycle assessment "
                              "in simple terms for a student.")
        response2 = llm.complete(conversation_prompt)
        
        print(f"✅ Conversation Response: {response2.text}")
        
        print("\n🎉 Gemini 2.5 Flash is working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing Gemini 2.5 Flash: {str(e)}")
        if "429" in str(e):
            print("💡 This is a rate limit error. Wait a moment and try again.")
        elif "403" in str(e):
            print("💡 This might be an API key authentication issue.")
        elif "400" in str(e):
            print("💡 This might be a model name or parameter issue.")
        return False

def test_tutor_engine_with_gemini25():
    """Test the TutorEngine with Gemini 2.5 Flash"""
    print("\n🧪 Testing TutorEngine with Gemini 2.5 Flash...")
    
    try:
        from src.core.tutor_engine import TutorEngine
        
        # Initialize engine
        engine = TutorEngine()
        print("✅ TutorEngine initialized successfully")
        
        # Test a simple question
        test_question = "What is sustainable design?"
        print(f"\n🔄 Testing question: '{test_question}'")
        
        response = engine.get_guidance(test_question)
        print(f"✅ Response received: {response[:100]}...")
        
        # Test a follow-up
        followup_question = "Can you tell me more about the principles?"
        print(f"\n🔄 Testing follow-up: '{followup_question}'")
        
        followup_response = engine.get_guidance(followup_question)
        print(f"✅ Follow-up response: {followup_response[:100]}...")
        
        print("\n🎉 TutorEngine with Gemini 2.5 Flash is working!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing TutorEngine: {str(e)}")
        return False

def show_model_info():
    """Show information about Gemini 2.5 Flash"""
    print("\n📋 Gemini 2.5 Flash Model Information:")
    print("-" * 50)
    print("Model Name: gemini-2.5-flash")
    print("Provider: Google AI")
    print("Capabilities: Text generation, conversation, reasoning")
    print("Optimizations: Fast inference, efficient for production")
    print("Token Limit: Up to 1M tokens context")
    print("Temperature Range: 0.0 (deterministic) to 1.0 (creative)")
    print("Best Use Cases: Real-time applications, chatbots, Q&A systems")
    print("-" * 50)

def main():
    """Run all tests"""
    print("RAG Tutor - Gemini 2.5 Flash Integration Test")
    print("=" * 50)
    
    show_model_info()
    
    # Test basic API
    api_test_passed = test_gemini_25_flash()
    
    if api_test_passed:
        # Test full engine
        engine_test_passed = test_tutor_engine_with_gemini25()
        
        if engine_test_passed:
            print("\n🎉 ALL TESTS PASSED!")
            print("Gemini 2.5 Flash is ready for production use.")
        else:
            print("\n⚠️ API works but TutorEngine has issues.")
    else:
        print("\n❌ API test failed. Please check your configuration.")

if __name__ == "__main__":
    main()
