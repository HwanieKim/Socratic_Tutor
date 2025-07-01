#!/usr/bin/env python3
"""
Integration Example: Using Enhanced Production System

This example shows how to integrate the new intelligent topic filtering
system with any knowledge base, making it adaptable to different domains.
"""

import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from src.core.tutor_engine import TutorEngine
from src.core.production_enhancements import ProductionTutorEngine
from llama_index.core import load_index_from_storage, StorageContext
import src.core.config as config

def create_enhanced_tutor():
    """
    Create an enhanced tutor with intelligent topic filtering
    """
    print("Creating Enhanced Tutor System...")
    
    # 1. Load the base tutor engine
    base_engine = TutorEngine()
    
    # 2. Get the knowledge base index for semantic filtering
    storage_context = StorageContext.from_defaults(persist_dir=config.PERSISTENCE_DIR)
    knowledge_base_index = load_index_from_storage(storage_context)
    
    # 3. Create enhanced production engine with knowledge base
    enhanced_engine = ProductionTutorEngine(
        base_engine=base_engine,
        knowledge_base_index=knowledge_base_index
    )
    
    print("✅ Enhanced tutor system created successfully!")
    return enhanced_engine

def test_enhanced_filtering():
    """
    Test the enhanced filtering with various question types
    """
    print("\n" + "="*50)
    print("Testing Enhanced Topic Filtering")
    print("="*50)
    
    # Create enhanced tutor
    tutor = create_enhanced_tutor()
    
    # Test questions that should work with any knowledge base
    test_questions = [
        "What is the main concept?",                    # General academic
        "How do I bake a cake?",                       # Clearly irrelevant
        "Can you explain more about this?",            # Follow-up
        "What are the key principles?",                # Academic
        "What's the weather today?",                   # Irrelevant
        "Tell me about the methodology.",              # Academic
        "How does this work?",                         # Academic
        "What sports do you like?",                    # Irrelevant
    ]
    
    for question in test_questions:
        print(f"\nQ: {question}")
        
        # Get response from enhanced engine
        response = tutor.get_guidance(question)
        
        # Check if it was filtered or processed
        if "knowledge base" in response.lower() or "subject matter" in response.lower():
            print(f"❌ FILTERED: {response}")
        else:
            print(f"✅ PROCESSED: {response[:100]}...")
    
    print(f"\n📊 Conversation Metrics: {tutor.get_metrics()}")

def demo_domain_adaptability():
    """
    Demonstrate how the system adapts to different domains
    """
    print("\n" + "="*50)
    print("Domain Adaptability Demo")
    print("="*50)
    
    print("""
🎯 Key Benefits of the Enhanced System:

1. **Semantic Understanding**: Uses vector similarity to determine relevance
   - Understands context and meaning, not just keywords
   - Adapts to any knowledge base content automatically

2. **Follow-up Detection**: Recognizes conversation patterns
   - Short questions like "what about..." are treated as follow-ups
   - Pronouns and references are handled intelligently

3. **Academic Question Recognition**: Identifies learning-oriented questions
   - "What", "How", "Why" questions are generally allowed
   - Educational patterns are recognized across domains

4. **Domain Agnostic**: Works with any PDF/document collection
   - No hardcoded keywords for specific subjects
   - Automatically learns from the loaded knowledge base

5. **Fallback Mechanisms**: Graceful degradation
   - If semantic search fails, uses pattern-based backup
   - Errs on the side of being helpful rather than restrictive

📚 Usage for Different Domains:
- Medical textbooks → Medical Q&A tutor
- Computer science papers → Programming tutor  
- History documents → History tutor
- Legal documents → Legal research assistant
- Any domain → Intelligent domain-specific tutor
    """)

if __name__ == "__main__":
    print("🚀 Enhanced RAG Tutor Integration Demo")
    print("="*50)
    
    try:
        # Test the enhanced filtering system
        test_enhanced_filtering()
        
        # Show domain adaptability info
        demo_domain_adaptability()
        
        print("\n✅ Demo completed successfully!")
        print("\n💡 The system is now ready for multi-domain deployment!")
        
    except Exception as e:
        print(f"❌ Error during demo: {e}")
        print("Make sure the knowledge base is properly set up.")
