#!/usr/bin/env python3
"""
TutorEngine - Main Orchestrator (Refactored)

Simplified orchestrator that coordinates all the specialized modules.
Follows SOAR pattern: State, Operator, And, Result
"""

import os
from dotenv import load_dotenv

from llama_index.core import Settings, StorageContext, load_index_from_storage
from llama_index.embeddings.voyageai import VoyageEmbedding
from llama_index.llms.google_genai import GoogleGenAI

from . import config
from .models import ReasoningTriplet, AnswerEvaluation
from .intent_classifier import IntentClassifier
from .rag_retriever import RAGRetriever
from .answer_evaluator import AnswerEvaluator
from .dialogue_generator import DialogueGenerator
from .scaffolding_system import ScaffoldingSystem
from .memory_manager import MemoryManager


class TutorEngine:
    """
    Main orchestrator for the Socratic tutoring system
    
    Coordinates specialized modules to provide intelligent tutoring
    following the SOAR pattern (State, Operator, And, Result)
    """
    
    def __init__(self):
        """Initialize the tutor engine and all component modules"""
        load_dotenv()
        
        # Check if index exists
        if not os.path.exists(config.PERSISTENCE_DIR):
            raise FileNotFoundError(
                f"Index not found at {config.PERSISTENCE_DIR}. "
                "Please create the index first using the create_index function."
            )
        
        # Configure global LlamaIndex settings
        self._configure_global_settings()
        
        # Load the vector index
        self.index = self._load_index()
        
        # Initialize specialized modules
        self.memory_manager = MemoryManager(token_limit=3000)
        self.intent_classifier = IntentClassifier()
        self.rag_retriever = RAGRetriever(self.index)
        self.answer_evaluator = AnswerEvaluator()
        self.dialogue_generator = DialogueGenerator()
        self.scaffolding_system = ScaffoldingSystem()
        
        print("✅ TutorEngine initialized successfully with modular architecture")
    
    def _configure_global_settings(self):
        """Configure global LlamaIndex settings"""
        try:
            # Set global LLM (for reasoning tasks)
            Settings.llm = GoogleGenAI(
                model_name=config.GEMINI_REASONING_MODEL_NAME,
                api_key=os.getenv("GOOGLE_API_KEY"),
                temperature=0.2
            )
            
            # Set global embedding model
            Settings.embed_model = VoyageEmbedding(
                model_name="voyage-multimodal-3",
                voyage_api_key=os.getenv("VOYAGE_API_KEY"),
                truncation=True
            )
            
        except Exception as e:
            print(f"Error configuring global settings: {e}")
            raise
    
    def _load_index(self):
        """Load the vector index from storage"""
        try:
            storage_context = StorageContext.from_defaults(persist_dir=config.PERSISTENCE_DIR)
            index = load_index_from_storage(storage_context)
            return index
            
        except Exception as e:
            print(f"Error loading index: {e}")
            raise
    
    def get_guidance(self, user_question: str) -> str:
        """
        Main entry point for getting tutoring guidance
        
        This is the central orchestrator that coordinates all modules
        following the SOAR pattern.
        
        Args:
            user_question: Student's question or response
            
        Returns:
            str: Tutor's response
        """
        try:
            # Input validation (from original implementation)
            if not user_question or not user_question.strip():
                return "I'd be happy to help! Please ask me a question."
            
            # Sanitize and validate input
            user_question = user_question.strip()
            if len(user_question) > 1000:  # Limit very long questions
                return "Your question is quite long. Could you please break it down into smaller, more specific questions?"
            
            # Add user message to memory
            self.memory_manager.add_user_message(user_question)
            
            # Stage 0: Intent Classification (State → Operator)
            intent = self.intent_classifier.classify_intent(
                user_question, 
                self.memory_manager.memory
            )
            print(f"DEBUG: Classified intent (Stage 0) as: {intent}")
            
            # Route to appropriate pipeline (And)
            if intent == "new_question":
                print("DEBUG: Executing pipeline: new_question")
                response = self._pipeline_new_question(user_question)
            else:  # follow_up
                print("DEBUG: Executing pipeline: follow_up")
                response = self._pipeline_follow_up(user_question)
            
            # Add response to memory and return (Result)
            self.memory_manager.add_assistant_message(response)
            return response
            
        except Exception as e:
            error_msg = str(e).lower()
            # Handle specific error types more gracefully (from original implementation)
            if ("429" in error_msg or "quota" in error_msg or "rate" in error_msg 
                or "503" in error_msg or "unavailable" in error_msg or "overloaded" in error_msg):
                error_response = "I'm experiencing high demand right now, which may cause delays. Please wait a moment and try your question again."
            elif "network" in error_msg or "connection" in error_msg:
                error_response = "I'm having trouble connecting. Please check your internet connection and try again."
            else:
                print(f"--- UNEXPECTED ERROR IN ROUTER --- \n{e}\n---------------")
                error_response = "An unexpected error occurred. Please try again."
                
            self.memory_manager.add_assistant_message(error_response)
            return error_response
    
    def _pipeline_new_question(self, user_question: str) -> str:
        """
        Pipeline for handling new questions
        
        Args:
            user_question: New question from student
            
        Returns:
            str: Tutor response
        """
        try:
            # Reset stuck count for new question
            self.memory_manager.reset_stuck_count()
            
            # Stage 1: RAG retrieval and expert reasoning
            triplet, source_nodes = self.rag_retriever.perform_rag_search(
                user_question, 
                self.memory_manager.memory
            )
            
            # Validate knowledge sufficiency
            if not self.rag_retriever.validate_knowledge_sufficiency(triplet):
                self.memory_manager.clear_topic_cache()
                return "I apologize, but I don't have sufficient information about this topic in my knowledge base. Could you try asking about something else, or provide more context?"
            
            # Cache the context for follow-up questions
            self.memory_manager.cache_topic_context(triplet, source_nodes)
            
            # Stage 2: Generate Socratic dialogue
            response = self.dialogue_generator.generate_socratic_dialogue(
                triplet, 
                source_nodes, 
                self.memory_manager.memory,
                answer_evaluation=None
            )
            
            return response
            
        except Exception as e:
            print(f"New question pipeline error: {e}")
            return "I'm having trouble processing your question right now. Could you try rephrasing it?"
    
    def _pipeline_follow_up(self, user_question: str) -> str:
        """
        Pipeline for handling follow-up responses
        
        Args:
            user_question: Follow-up response from student
            
        Returns:
            str: Tutor response
        """
        try:
            # Check if we have cached context
            triplet, source_nodes = self.memory_manager.get_cached_context()
            
            if not self.memory_manager.has_cached_context():
                # No cached context, treat as new question
                return self._pipeline_new_question(user_question)
            
            # Stage 0b: Classify follow-up type
            follow_up_type = self.intent_classifier.classify_follow_up_type(
                user_question, 
                self.memory_manager.memory
            )
            print(f"DEBUG: Classified follow-up type (Stage 0b) as: {follow_up_type}")
            
            if follow_up_type == "answer":
                print("DEBUG: Follow-up type is an answer. Evaluating.")
                # Student is attempting to answer
                return self._handle_student_answer(user_question, triplet, source_nodes)
            else:
                print("DEBUG: Follow-up type is a meta_question. Providing scaffolded help.")
                # Student needs help (meta_question)
                return self._handle_meta_question(triplet)
                
        except Exception as e:
            print(f"Follow-up pipeline error: {e}")
            return "Let's continue our discussion. What would you like to explore about this topic?"
    
    def _handle_student_answer(self, student_answer: str, triplet: ReasoningTriplet, source_nodes: list) -> str:
        """
        Handle when student provides an answer attempt
        
        Args:
            student_answer: Student's answer
            triplet: Cached expert reasoning
            source_nodes: Cached source nodes
            
        Returns:
            str: Tutor response with evaluation
        """
        try:
            # Reset stuck count since student provided an answer
            self.memory_manager.reset_stuck_count()
            
            # Stage 1b: Evaluate student's answer
            evaluation = self.answer_evaluator.evaluate_student_answer(student_answer, triplet)
            print(f"DEBUG: Answer evaluation (Stage 1b): {evaluation.evaluation}")
            
            # Stage 2: Generate response based on evaluation
            response = self.dialogue_generator.generate_socratic_dialogue(
                triplet, 
                source_nodes, 
                self.memory_manager.memory,
                answer_evaluation=evaluation
            )
            
            # Enhance with encouragement
            response = self.dialogue_generator.enhance_response_with_encouragement(response, evaluation)
            
            return response
            
        except Exception as e:
            print(f"Student answer handling error: {e}")
            return "That's an interesting response! Let's explore it further. What led you to that thinking?"
    
    def _handle_meta_question(self, triplet: ReasoningTriplet) -> str:
        """
        Handle when student asks for help or expresses confusion
        
        Args:
            triplet: Cached expert reasoning
            
        Returns:
            str: Scaffolded help response
        """
        try:
            # Increment stuck count for scaffolding
            stuck_count = self.memory_manager.increment_stuck_count()
            print(f"DEBUG: Scaffolding Level {stuck_count}: Student stuck count incremented")
            
            # Get scaffolded help based on stuck count
            scaffold_evaluation = self.scaffolding_system.provide_scaffolded_help(stuck_count, triplet)
            print(f"DEBUG: Scaffolding evaluation type: {scaffold_evaluation.evaluation}")
            
            # Use dialogue generator to create the final response with scaffolding
            source_nodes = self.memory_manager.current_topic_source_nodes or []
            response = self.dialogue_generator.generate_socratic_dialogue(
                triplet, 
                source_nodes, 
                self.memory_manager.memory,
                answer_evaluation=scaffold_evaluation
            )
            
            return response
            
        except Exception as e:
            print(f"Meta question handling error: {e}")
            return "I'm here to help! Let's think about this step by step. What aspect would you like to focus on first?"
    
    def reset(self):
        """Reset the entire tutoring session"""
        try:
            self.memory_manager.reset_session()
            print("✅ Tutoring session reset successfully")
            
        except Exception as e:
            print(f"Error resetting session: {e}")
    
    def get_session_summary(self) -> dict:
        """Get summary of current tutoring session"""
        try:
            return self.memory_manager.get_session_summary()
            
        except Exception as e:
            print(f"Error getting session summary: {e}")
            return {"error": "Unable to generate session summary"}
    
    def get_memory_stats(self) -> dict:
        """Get memory usage statistics"""
        try:
            return self.memory_manager.get_memory_usage_stats()
            
        except Exception as e:
            print(f"Error getting memory stats: {e}")
            return {"error": "Unable to get memory statistics"}


# Legacy method aliases for backward compatibility
def get_guidance(user_question: str) -> str:
    """Legacy function - use TutorEngine class instead"""
    print("Warning: Using legacy function. Consider using TutorEngine class directly.")
    # This would require a global instance - not recommended for production
    pass
