#!/usr/bin/env python3
"""
Edge Case Testing for RAG Tutor System

This script tests various edge cases and scenarios to ensure robustness:
1. Ambiguous follow-up questions
2. Context-less follow-ups
3. Information not in documents
4. Long multi-turn conversations
5. Conversation reset scenarios
6. Empty/nonsensical queries
"""

import time
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.tutor_engine import TutorEngine

def print_separator(title):
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

def test_conversation_turn(engine, question, turn_num, description=""):
    print(f"\n--- Turn {turn_num}: {description} ---")
    print(f"Question: {question}")
    response = engine.get_guidance(question)
    print(f"Response: {response}")
    return response

def test_ambiguous_followups():
    """Test Case 1: Ambiguous or contextless follow-up questions"""
    print_separator("TEST 1: AMBIGUOUS FOLLOW-UP QUESTIONS")
    
    engine = TutorEngine()
    
    # Start with a clear question
    test_conversation_turn(engine, 
        "What is sustainable design?", 
        1, "Clear initial question")
    
    # Follow with ambiguous questions
    test_conversation_turn(engine, 
        "What about that?", 
        2, "Ambiguous follow-up")
    
    test_conversation_turn(engine, 
        "Can you explain more?", 
        3, "Vague follow-up")
    
    test_conversation_turn(engine, 
        "How does it work?", 
        4, "Contextless 'it' reference")
    
    engine.reset()

def test_information_not_in_docs():
    """Test Case 2: Questions about information not in documents"""
    print_separator("TEST 2: INFORMATION NOT IN DOCUMENTS")
    
    engine = TutorEngine()
    
    # Questions about topics likely not in sustainable design docs
    test_conversation_turn(engine, 
        "How do I bake a chocolate cake?", 
        1, "Completely unrelated topic")
    
    test_conversation_turn(engine, 
        "What is the capital of Mars?", 
        2, "Nonsensical question")
    
    test_conversation_turn(engine, 
        "Explain quantum mechanics in sustainable design", 
        3, "Mixing unrelated complex topics")
    
    engine.reset()

def test_empty_and_nonsensical():
    """Test Case 3: Empty and nonsensical queries"""
    print_separator("TEST 3: EMPTY AND NONSENSICAL QUERIES")
    
    engine = TutorEngine()
    
    test_conversation_turn(engine, 
        "", 
        1, "Empty string")
    
    test_conversation_turn(engine, 
        "asdfghjkl qwerty", 
        2, "Random characters")
    
    test_conversation_turn(engine, 
        "?" * 50, 
        3, "Multiple question marks")
    
    test_conversation_turn(engine, 
        "What what what when where why how?", 
        4, "Incoherent question words")
    
    engine.reset()

def test_long_conversation():
    """Test Case 4: Long multi-turn conversation to test memory"""
    print_separator("TEST 4: LONG MULTI-TURN CONVERSATION")
    
    engine = TutorEngine()
    
    # Start a topic and keep building on it
    questions = [
        "What are the principles of sustainable design?",
        "Can you tell me more about the first principle?",
        "How does this apply to buildings?",
        "What about materials selection?",
        "Are there specific examples?",
        "How do we measure sustainability?",
        "What tools are available?",
        "Can you compare different approaches?",
        "What are the challenges?",
        "How do we overcome them?",
        "What's the future of sustainable design?",
        "Can you summarize everything we discussed?"
    ]
    
    for i, question in enumerate(questions, 1):
        test_conversation_turn(engine, question, i, f"Long conversation turn {i}")
        # Small delay to simulate realistic conversation pace
        time.sleep(0.5)
    
    engine.reset()

def test_conversation_reset_scenarios():
    """Test Case 5: Conversation reset scenarios"""
    print_separator("TEST 5: CONVERSATION RESET SCENARIOS")
    
    engine = TutorEngine()
    
    # Build up some conversation context
    test_conversation_turn(engine, 
        "What is lifecycle assessment?", 
        1, "Initial context building")
    
    test_conversation_turn(engine, 
        "How is it used in design?", 
        2, "Follow-up with context")
    
    # Reset and ask a follow-up that should now be treated as first question
    print("\n--- RESETTING CONVERSATION ---")
    engine.reset()
    
    test_conversation_turn(engine, 
        "What about the environmental impact?", 
        1, "After reset - should treat as first question")
    
    test_conversation_turn(engine, 
        "Can you give examples?", 
        2, "New follow-up after reset")

def test_rapid_context_switching():
    """Test Case 6: Rapid context switching between topics"""
    print_separator("TEST 6: RAPID CONTEXT SWITCHING")
    
    engine = TutorEngine()
    
    topics = [
        "Tell me about sustainable materials",
        "What about energy efficiency in buildings?", 
        "How does water conservation work?",
        "What are renewable energy sources?",
        "Back to materials - which are best?",
        "Energy efficiency - what are the key metrics?",
        "Water systems - any specific technologies?"
    ]
    
    for i, topic in enumerate(topics, 1):
        test_conversation_turn(engine, topic, i, f"Topic switch {i}")
    
    engine.reset()

def test_memory_and_context_limits():
    """Test Case 7: Push memory and context limits"""
    print_separator("TEST 7: MEMORY AND CONTEXT LIMITS")
    
    engine = TutorEngine()
    
    # Very long first question
    long_question = ("Can you explain in detail how sustainable design principles "
                    "integrate with environmental impact assessment methodologies "
                    "while considering economic feasibility and social equity factors "
                    "in the context of urban planning and architecture for developing "
                    "countries with limited resources and infrastructure constraints "
                    "and how this relates to circular economy principles?")
    
    test_conversation_turn(engine, long_question, 1, "Very long complex question")
    
    # Follow with short questions to test context retention
    short_followups = [
        "What about costs?",
        "And implementation?", 
        "Any examples?",
        "Challenges?",
        "Solutions?"
    ]
    
    for i, followup in enumerate(short_followups, 2):
        test_conversation_turn(engine, followup, i, f"Short follow-up {i-1}")

def run_all_tests():
    """Run all edge case tests"""
    print("Starting comprehensive edge case testing...")
    print("This may take several minutes due to LLM response times.")
    
    try:
        test_ambiguous_followups()
        test_information_not_in_docs()
        test_empty_and_nonsensical()
        test_long_conversation()
        test_conversation_reset_scenarios()
        test_rapid_context_switching()
        test_memory_and_context_limits()
        
        print_separator("TESTING COMPLETE")
        print("All edge case tests completed successfully!")
        print("Review the outputs above to assess system robustness.")
        
    except Exception as e:
        print(f"\nTEST FAILED with error: {e}")
        print("This indicates a robustness issue that needs addressing.")

if __name__ == "__main__":
    run_all_tests()
