#!/usr/bin/env python3
"""
TutorEngine - Main Orchestrator (Refactored)

Simplified orchestrator that coordinates all the specialized modules.
Follows SOAR pattern: State, Operator, And, Result
Supports Railway deployment with database and session management.
"""

import os
import uuid
import shutil
from typing import List, Dict, Optional
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
from .database_manager import DatabaseManager


class TutorEngine:
    """
    Main orchestrator for the Socratic tutoring system
    
    Coordinates specialized modules to provide intelligent tutoring
    following the SOAR pattern (State, Operator, And, Result)
    Supports multi-user sessions with database integration.
    """
    
    def __init__(self, session_id: str = None):
        """Initialize the tutor engine and all component modules
        
        Args:
            session_id: Unique session identifier. If None, generates a new one.
        """
        load_dotenv()
        
        # Session management
        self.session_id = session_id or str(uuid.uuid4())
        self.db_manager = DatabaseManager()
        
        # Create or get user
        self.user = self.db_manager.create_or_get_user(self.session_id)
        
        # Check for existing user index first
        self._try_load_user_index()
        
        # If no user index, try to load default index
        if not hasattr(self, 'index') or self.index is None:
            self._try_load_default_index()
        
        # Configure global LlamaIndex settings
        self._configure_global_settings()
        
        # Initialize specialized modules only if we have an index
        if hasattr(self, 'index') and self.index is not None:
            self._initialize_modules()
        else:
            print("⚠️ No index available. Upload documents and create index to start tutoring.")
    
    def _try_load_user_index(self):
        """Try to load user-specific index"""
        try:
            active_index = self.db_manager.get_active_index(self.session_id)
            if active_index and os.path.exists(active_index['index_path']):
                self.index = self._load_index_from_path(active_index['index_path'])
                print(f"✅ Loaded user index with {active_index['document_count']} documents")
            else:
                self.index = None
        except Exception as e:
            print(f"Could not load user index: {e}")
            self.index = None
    
    def _try_load_default_index(self):
        """Try to load default index as fallback"""
        try:
            if os.path.exists(config.PERSISTENCE_DIR):
                self.index = self._load_index_from_path(config.PERSISTENCE_DIR)
                print("✅ Loaded default index")
            else:
                self.index = None
                print("ℹ️ No default index found")
        except Exception as e:
            print(f"Could not load default index: {e}")
            self.index = None
    
    def _initialize_modules(self):
        """Initialize specialized modules"""
        self.memory_manager = MemoryManager(token_limit=3000)
        self.intent_classifier = IntentClassifier()
        self.rag_retriever = RAGRetriever(self.index)
        self.answer_evaluator = AnswerEvaluator()
        self.dialogue_generator = DialogueGenerator()
        self.scaffolding_system = ScaffoldingSystem()
        print("✅ TutorEngine modules initialized successfully")
    
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
    
    def _load_index_from_path(self, index_path: str):
        """Load index from specific path"""
        try:
            storage_context = StorageContext.from_defaults(persist_dir=index_path)
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
            
            # Get tutor's last message and conversation context for evaluation
            recent_messages = self.memory_manager.get_conversation_history(last_n=6)
            tutor_last_message = ""
            conversation_context = self.memory_manager.format_conversation_context(last_n=6)
            
            # Find the tutor's last message
            for msg in reversed(recent_messages[:-1]):  # Exclude the current student message
                if msg.role.value == "assistant":  # Tutor's message
                    tutor_last_message = msg.content
                    break
            
            # Stage 1b: Evaluate student's answer with full context
            evaluation = self.answer_evaluator.evaluate_student_answer(
                student_answer, 
                triplet,
                tutor_last_message,
                conversation_context
            )
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
            
            # Get scaffolding decision based on stuck count
            scaffolding_decision = self.scaffolding_system.decide_scaffolding(stuck_count, triplet)
            print(f"DEBUG: Scaffolding decision type: {scaffolding_decision.scaffold_type} (level {scaffolding_decision.stuck_level})")
            
            # Use dialogue generator to create the final response with scaffolding
            source_nodes = self.memory_manager.current_topic_source_nodes or []
            response = self.dialogue_generator.generate_socratic_dialogue(
                triplet, 
                source_nodes, 
                self.memory_manager.memory,
                scaffolding_decision=scaffolding_decision
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
    
    # Railway deployment methods for file upload and index management
    
    def upload_documents(self, uploaded_files) -> str:
        """Upload documents to Railway Volume and save metadata to database
        
        Args:
            uploaded_files: List of uploaded file objects from Gradio
            
        Returns:
            str: Upload status message
        """
        try:
            if not uploaded_files:
                return "❌ No files provided"
            
            saved_files = []
            user_upload_dir = os.path.join(config.USER_UPLOADS_DIR, self.session_id)
            os.makedirs(user_upload_dir, exist_ok=True)
            
            for file in uploaded_files:
                if file is None:
                    continue
                
                # Calculate file hash for deduplication
                file_hash = self.db_manager.calculate_file_hash(file.name)
                original_filename = os.path.basename(file.name)
                
                # Create unique filename
                file_extension = os.path.splitext(original_filename)[1]
                unique_filename = f"{file_hash}_{original_filename}"
                save_path = os.path.join(user_upload_dir, unique_filename)
                
                # Copy file to permanent location
                shutil.copy2(file.name, save_path)
                
                # Save metadata to database
                file_info = {
                    'original_filename': original_filename,
                    'display_name': original_filename,
                    'file_hash': file_hash,
                    'file_path': save_path,
                    'file_size': os.path.getsize(save_path)
                }
                
                doc_id = self.db_manager.save_uploaded_document(self.session_id, file_info)
                if doc_id > 0:
                    saved_files.append(original_filename)
            
            if saved_files:
                return f"✅ Successfully uploaded {len(saved_files)} documents:\n" + "\n".join([f"• {name}" for name in saved_files])
            else:
                return "❌ No documents were saved successfully"
                
        except Exception as e:
            return f"❌ Upload failed: {str(e)}"
    
    def create_user_index(self) -> str:
        """Create user-specific index from uploaded documents
        
        Returns:
            str: Index creation status message
        """
        try:
            # Get uploaded documents from database
            documents = self.db_manager.get_user_documents(self.session_id)
            uploaded_docs = [doc for doc in documents if doc['status'] == 'uploaded']
            
            if not uploaded_docs:
                return "❌ No uploaded documents found. Please upload PDF files first."
            
            # Prepare file paths for index creation
            file_paths = [doc['file_path'] for doc in uploaded_docs]
            
            # Create user-specific index directory
            user_index_dir = os.path.join(config.USER_INDEXES_DIR, self.session_id)
            
            # Import and run index creation
            from .persistence import create_index_from_files
            import asyncio
            
            print(f"Creating index from {len(file_paths)} documents...")
            asyncio.run(create_index_from_files(file_paths, user_index_dir))
            
            # Update database to mark documents as indexed
            self.db_manager.mark_documents_indexed(self.session_id, user_index_dir)
            
            # Reload the engine with new index
            self.index = self._load_index_from_path(user_index_dir)
            self._initialize_modules()
            
            return f"✅ Index created successfully!\n• Processed {len(file_paths)} documents\n• Engine ready for tutoring"
            
        except Exception as e:
            return f"❌ Index creation failed: {str(e)}"
    
    def get_user_documents(self) -> List[Dict]:
        """Get list of user's uploaded documents
        
        Returns:
            List[Dict]: List of document metadata
        """
        try:
            return self.db_manager.get_user_documents(self.session_id)
        except Exception as e:
            print(f"Error getting user documents: {e}")
            return []
    
    def get_session_info(self) -> Dict:
        """Get session information including upload/index status
        
        Returns:
            Dict: Session information
        """
        try:
            documents = self.get_user_documents()
            active_index = self.db_manager.get_active_index(self.session_id)
            
            return {
                'session_id': self.session_id,
                'user_created': self.user.get('created_at'),
                'documents_count': len(documents),
                'indexed_documents': len([d for d in documents if d['indexed']]),
                'has_active_index': active_index is not None,
                'engine_ready': hasattr(self, 'index') and self.index is not None,
                'documents': documents
            }
        except Exception as e:
            print(f"Error getting session info: {e}")
            return {'error': str(e)}
    
    def save_conversation(self, user_message: str, tutor_response: str, context_used: str = ""):
        """Save conversation to database for history tracking
        
        Args:
            user_message: User's message
            tutor_response: Tutor's response
            context_used: Context information used in response
        """
        try:
            self.db_manager.save_conversation(
                self.session_id, 
                user_message, 
                tutor_response, 
                context_used
            )
        except Exception as e:
            print(f"Failed to save conversation: {e}")
    
    def is_ready_for_tutoring(self) -> bool:
        """Check if engine is ready for tutoring
        
        Returns:
            bool: True if engine has index and modules initialized
        """
        return hasattr(self, 'index') and self.index is not None and hasattr(self, 'rag_retriever')


# Legacy method aliases for backward compatibility
def get_guidance(user_question: str) -> str:
    """Legacy function - use TutorEngine class instead"""
    print("Warning: Using legacy function. Consider using TutorEngine class directly.")
    # This would require a global instance - not recommended for production
    pass
