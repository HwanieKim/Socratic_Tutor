#!/usr/bin/env python3
"""
TutorEngine - Main Orchestrator (Refactored)

Simplified orchestrator that coordinates all the specialized modules.
Follows SOAR pattern: State, Operator, And, Result
Supports Railway deployment with database and session management.
"""

import json
import os
import trace
import traceback
import uuid
import shutil
import hashlib
import asyncio
from typing import AsyncGenerator, Generator, List, Dict, Optional
from dotenv import load_dotenv

from llama_index.core import Settings, StorageContext, load_index_from_storage
from llama_index.embeddings.voyageai import VoyageEmbedding
from llama_index.llms.google_genai import GoogleGenAI

from . import config
from .i18n import get_ui_text
from .models import MultidimensionalScores, ReasoningTriplet, EnhancedAnswerEvaluation, SessionLearningProfile, LearningLevel
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
    
    def __init__(self, session_id: str = None, language: str = "en"):
        """Initialize the tutor engine and all component modules
        
        Args:
            session_id: Unique session identifier. If None, generates a new one.
            language: Language code for i18n messages (default: "en")
        """
        load_dotenv()
        
        # Session management
        self.session_id = session_id or str(uuid.uuid4())
        self.language = language
        self.db_manager = DatabaseManager()
        
        self.learning_profile = SessionLearningProfile()

        self.index: Optional[StorageContext] = None
        self._is_engine_ready = False
        self._lock = asyncio.Lock()
     
        # # Configure global LlamaIndex settings
        # self._configure_global_settings()

        print(f"✅ TutorEngine for session {self.session_id} initialized (lightweight). Engine will load on first use.")
    
    async def initialize_engine(self):
        """
        Initialize and warm up the tutor engine asynchronously.
        
        Loads indexes, configures settings, and prepares all modules for tutoring.
        Should be called before first use for optimal performance.
        """
        await self._ensure_engine_ready()
        if self._is_engine_ready:
            print("✅ Engine warm-up successful. Ready for requests.")
        else:
            print("⚠️ Engine ready. waiting for an index to be loaded.")
            
            
    async def _ensure_engine_ready(self):
        """
        Ensure the engine is fully ready for tutoring requests.
        
        Performs lazy initialization including index loading, module setup,
        and configuration. Thread-safe with async lock.
        """
        async with self._lock:
            if self._is_engine_ready:
                return
            print("Engine not ready. Performing first-time setup...")


            try:
                self._configure_global_settings()
            
                active_index = self.db_manager.get_active_index(self.session_id)
                if active_index and os.path.exists(active_index['index_path']):
                    self.index = await self._load_index_from_path_async(active_index['index_path'])
                    print(f"✅ Loaded user index with {active_index['document_count']} documents")
                elif os.path.exists(config.PERSISTENCE_DIR):
                    self.index = await self._load_index_from_path_async(config.PERSISTENCE_DIR)
                    print("✅ Loaded default index as fallback")
                else:
                    self.index = None
                    print("⚠️ No user or default index found.")
 
                # initialize modules iff index is successfully loaded
                if self.index is not None:
                    self._initialize_modules()
                    self._is_engine_ready = True
                    print("✅ Engine is now fully loaded and ready.")
                else:
                    print("⚠️ Engine setup failed: No index available.")
                    self._is_engine_ready = False 

            except Exception as e:
                print(f"❌ Critical error during engine setup: {e}")
                traceback.print_exc()
                self._is_engine_ready = False
                
    # def _try_load_user_index(self):
    #     """Try to load user-specific index"""
    #     try:
    #         active_index = self.db_manager.get_active_index(self.session_id)
    #         if active_index and os.path.exists(active_index['index_path']):
    #             self.index = self._load_index_from_path_sync(active_index['index_path'])
    #             print(f"✅ Loaded user index with {active_index['document_count']} documents")
    #         else:
    #             self.index = None
    #     except Exception as e:
    #         print(f"Could not load user index: {e}")
    #         self.index = None
    
    # def _try_load_default_index(self):
    #     """Try to load default index as fallback"""
    #     try:
    #         if os.path.exists(config.PERSISTENCE_DIR):
    #             self.index = self._load_index_from_path_sync(config.PERSISTENCE_DIR)
    #             print("✅ Loaded default index")
    #         else:
    #             self.index = None
    #             print("ℹ️ No default index found")
    #     except Exception as e:
    #         print(f"Could not load default index: {e}")
    #         self.index = None
    
    def _initialize_modules(self):
        """
        Initialize all specialized tutoring modules.
        
        Creates instances of memory manager, intent classifier, RAG retriever,
        answer evaluator, dialogue generator, and scaffolding system.
        """
        self.memory_manager = MemoryManager(token_limit=3000)
        self.intent_classifier = IntentClassifier()
        self.rag_retriever = RAGRetriever(self.index)
        self.answer_evaluator = AnswerEvaluator()
        self.dialogue_generator = DialogueGenerator()
        self.scaffolding_system = ScaffoldingSystem()
        print("✅ TutorEngine modules initialized successfully", flush=True)
    
    def _configure_global_settings(self):
        """
        Configure global LlamaIndex settings for LLM and embedding models.
        
        Sets up Google GenAI for reasoning tasks and Voyage AI for embeddings.
        
        Raises:
            Exception: If API keys are missing or configuration fails
        """
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

                
        
    def _load_index_from_path_sync(self,index_path:str):
        """
        Synchronously load vector index from specified path.
        
        Args:
            index_path: Filesystem path to the stored index
            
        Returns:
            VectorStoreIndex: Loaded index object
            
        Raises:
            Exception: If index loading fails or path is invalid
        """
        print(f"Starting to load index from path: {index_path}", flush=True)
        try:

            self._configure_global_settings()
            storage_context = StorageContext.from_defaults(persist_dir=index_path)
            return load_index_from_storage(storage_context)
        except Exception as e:
            print(f"Error loading index from path {index_path}: {e}")
            traceback.print_exc()
            raise

    async def _load_index_from_path_async(self, index_path: str):
        """
        Asynchronously load vector index from specified path.
        
        Executes slow I/O operations in a separate thread to avoid blocking
        the main event loop.
        
        Args:
            index_path: Filesystem path to the stored index
            
        Returns:
            VectorStoreIndex: Loaded index object
            
        Raises:
            Exception: If index loading fails or path is invalid
        """
        print(f"Starting to load index from path: {index_path}")
        
        loop = asyncio.get_running_loop()

        try:
            index = await loop.run_in_executor(
                None,  # Use default executor
                self._load_index_from_path_sync,
                index_path
            )
            print(f"Index loaded successfully from {index_path}", flush=True)
            return index
        except Exception as e:
            print(f"Error loading index from path {index_path}: {e}")
            traceback.print_exc()
            raise

    async def get_guidance(self, user_question: str, language: str = "en") -> dict:
        """
        Main entry point for getting tutoring guidance following SOAR pattern.
        
        This is the central orchestrator that coordinates all modules:
        State → Operator → And → Result
        
        Args:
            user_question: Student's question or response
            language: Language code for internationalization
            
        Returns:
            dict: Response containing type and content/key for UI handling
        """

        # Check if tutoring can start (both steps completed)
        if not self.can_start_tutoring():
            status = self.get_tutoring_status()
            
            if not status['step1_upload_complete']:
                return {"type": "ui_text","key": "engine_upload_documents_first"}
            elif not status['step2_index_complete']:
                return {"type": "ui_text","key": "engine_create_index_first"}
            else:
                return {"type": "ui_text","key": "engine_system_not_ready"}

        await self._ensure_engine_ready()

        if not self._is_engine_ready:
            return {"type": "ui_text","key": "engine_index_not_loaded"}
        try:
            # Input validation (from original implementation)
            if not user_question or not user_question.strip():
                return {"type": "ui_text","key": "engine_happy_to_help"}

            # Sanitize and validate input
            user_question = user_question.strip()
            if len(user_question) > 1000:  # Limit very long questions
                return {"type": "ui_text","key": "engine_question_too_long"}

            # Add user message to memory
            self.memory_manager.add_user_message(user_question)
            
            # Stage 0: Intent Classification (State → Operator)
            intent = self.intent_classifier.classify_intent(
                user_question, 
                self.memory_manager.memory,
                language
            )
            print(f"DEBUG: Classified intent (Stage 0) as: {intent}", flush=True)
            
            # Route to appropriate pipeline (And)
            if intent == "new_question":
                print("DEBUG: Executing pipeline: new_question", flush=True)
                response = self._pipeline_new_question(user_question, language)
            else:  # follow_up
                print("DEBUG: Executing pipeline: follow_up", flush=True)
                response = self._pipeline_follow_up(user_question, language)

            # Add response to memory and return (Result)
            self.memory_manager.add_assistant_message(response)
            return {"type": "response", "content": response}

        except Exception as e:
            error_msg = str(e).lower()
            # Handle specific error types more gracefully (from original implementation)
            if ("429" in error_msg or "quota" in error_msg or "rate" in error_msg 
                or "503" in error_msg or "unavailable" in error_msg or "overloaded" in error_msg):
                error_key = "engine_high_demand"
            elif "network" in error_msg or "connection" in error_msg:
                error_key = "engine_connection_error"
            else:
                print(f"--- UNEXPECTED ERROR IN ROUTER --- \n{e}\n---------------")
                error_key = "engine_unexpected_error"

            error_response = get_ui_text(error_key, self.language)
            self.memory_manager.add_assistant_message(error_response)
            return {"type": "response", "content": error_response}

    def _pipeline_new_question(self, user_question: str, language: str = "en") -> str:
        """
        Pipeline for handling new questions from students.
        
        Performs RAG retrieval, generates expert reasoning, validates knowledge
        sufficiency, and creates initial Socratic dialogue response.
        
        Args:
            user_question: New question from student
            language: Language code for response generation
            
        Returns:
            str: Generated Socratic tutor response
        """
        try:
            # Reset stuck count for new question
            self.memory_manager.reset_stuck_count()
            
            # Stage 1: RAG retrieval and expert reasoning
            triplet, source_nodes = self.rag_retriever.perform_rag_search(
                user_question, 
                self.memory_manager.memory,
                language
            )
            
            # Validate knowledge sufficiency
            if not self.rag_retriever.validate_knowledge_sufficiency(triplet,language):
                self.memory_manager.clear_topic_cache()
                return get_ui_text("engine_insufficient_knowledge", language)
            
            # Cache the context for follow-up questions
            self.memory_manager.cache_topic_context(triplet, source_nodes)
            mock_multidim = MultidimensionalScores(
                conceptual_accuracy= 0.5,
                reasoning_coherence=0.5,
                use_of_evidence_and_rules=0.5,
                conceptual_integration=0.5,
                clarity_of_expression=0.5
            )
            mock_eval = EnhancedAnswerEvaluation(
                binary_evaluation="unclear",
                multidimensional_scores=mock_multidim,
                reasoning_quality= "none",
                misconceptions= [],
                strengths= [],
                feedback= "Starting new topic - no prior evaluation",
                reasoning_analysis= "New question - no prior context"
            )
            # Stage 2: Generate Socratic dialogue
            response = self.dialogue_generator.generate_adaptive_socratic_dialogue(
                triplet, 
                source_nodes, 
                self.memory_manager.memory,
                answer_evaluation=mock_eval,
                learning_profile=self.learning_profile,
                adaptive_strategy="general_guidance",
                language=language
            )
            
            return response
            
        except Exception as e:
            print(f"New question pipeline error: {e}")
            return get_ui_text("engine_processing_error", self.language)

    def _pipeline_follow_up(self, user_question: str, language: str = "en") -> str:
        """
        Pipeline for handling follow-up responses from students.
        
        Classifies follow-up type (answer vs meta_question) and routes to
        appropriate handling logic with cached context.
        
        Args:
            user_question: Follow-up response from student
            language: Language code for response generation
            
        Returns:
            str: Contextually appropriate tutor response
        """
        try:
            # Check if we have cached context
            triplet, source_nodes = self.memory_manager.get_cached_context()
            
            if not self.memory_manager.has_cached_context():
                # No cached context, treat as new question
                return self._pipeline_new_question(user_question, language)

            # Stage 0b: Classify follow-up type
            follow_up_type = self.intent_classifier.classify_follow_up_type(
                user_question, 
                self.memory_manager.memory,
                language
            )
            print(f"DEBUG: Classified follow-up type (Stage 0b) as: {follow_up_type}")
            
            if follow_up_type == "answer":
                print("DEBUG: Follow-up type is an answer. Evaluating.")
                # Student is attempting to answer
                return self._handle_student_answer(user_question, triplet, source_nodes, language)
            else:
                print("DEBUG: Follow-up type is a meta_question. Providing scaffolded help.")
                # Student needs help (meta_question)
                return self._handle_meta_question(triplet, language)

        except Exception as e:
            print(f"Follow-up pipeline error: {e}")
            return get_ui_text("engine_follow_up_no_context", language)

    def _handle_student_answer(self, student_answer: str, triplet: ReasoningTriplet, source_nodes: list, language: str) -> str:
        """
        Handle when student provides an answer attempt.
        
        Evaluates student's answer against expert reasoning, updates learning
        profile, determines adaptive strategy, and generates appropriate response.
        
        Args:
            student_answer: Student's answer attempt
            triplet: Cached expert reasoning triplet
            source_nodes: Cached source document nodes
            language: Language code for evaluation and response
            
        Returns:
            str: Tutor response with evaluation and guidance
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
                if hasattr(msg, 'role') and hasattr(msg.role, 'value') and msg.role.value == "assistant":
                    tutor_last_message = msg.content
                    break
            
            # Stage 1b: Evaluate student's answer with full context
            evaluation = self.answer_evaluator.evaluate_student_answer_enhanced(
                student_answer, 
                triplet,
                tutor_last_message,
                conversation_context,
                language
            )
            print(f"DEBUG: Answer evaluation (Stage 1b): {evaluation.binary_evaluation} (Overall : {evaluation.overall_score:.3f})")

            self.learning_profile.add_evaluation_score(evaluation)
            adaptive_strategy = self._determine_adaptive_strategy(evaluation)

            # Stage 2: Generate response based on evaluation
            response = self.dialogue_generator.generate_adaptive_socratic_dialogue(
                triplet, 
                source_nodes, 
                self.memory_manager.memory,
                answer_evaluation=evaluation,
                learning_profile=self.learning_profile,
                adaptive_strategy=adaptive_strategy,
                language=language
            )
            # # Enhance with encouragement
            # response = self.dialogue_generator.enhance_response_with_encouragement(response, evaluation, language)

            return response
            
        except Exception as e:
            print(f"Student answer handling error: {e}")
            traceback.print_exc()
            return get_ui_text("engine_interesting_response", language)


    def _determine_adaptive_strategy(self, evaluation: EnhancedAnswerEvaluation) -> str:
        """
        Determine adaptive tutoring strategy based on evaluation and learning level.
        
        Selects appropriate pedagogical strategy considering student's current
        learning level, evaluation scores, and performance patterns.
        
        Args:
            evaluation: Enhanced answer evaluation with multidimensional scores
            
        Returns:
            str: Selected adaptive strategy identifier
        """
        current_level= self.learning_profile.current_level
        overall_score = evaluation.overall_score
        binary_evaluation = evaluation.binary_evaluation

        print(f"[DEBUG] 🎯 Determining adaptive strategy:")
        print(f"  - Level: {current_level.value}")
        print(f"  - Score: {overall_score:.3f}")
        print(f"  - Binary: {binary_evaluation}")

        if current_level == LearningLevel.L0_PRE_CONCEPTUAL:
            if overall_score >= 0.6:
                strategy = "encouragement_basic"
            else:
                strategy = "foundation_building"

        elif current_level == LearningLevel.L1_FAMILIARIZATION:
            if binary_evaluation in ["correct", "partially_correct"]:
                strategy = "conceptual_reinforcement"
            else:
                strategy = "guided_exploration"

        elif current_level == LearningLevel.L2_STRUCTURED_COMPREHENSION:
            if overall_score >= 0.7:
                strategy = "connection_building"
            else:
                strategy = "procedure_refinement"
        
        elif current_level == LearningLevel.L3_PROCEDURAL_FLUENCY:
            if binary_evaluation == "correct":
                strategy = "advanced_application"
            else:
                strategy = "procedural_reinforcement"
                
        elif current_level == LearningLevel.L4_CONCEPTUAL_TRANSFER:
            if overall_score >= 0.8:
                strategy = "independent_exploration"
            else:
                strategy = "transfer_facilitation"
        
        else:
            strategy = "general_guidance"

        print(f"[DEBUG] 🎯 Selected adaptive strategy: {strategy}")
        return strategy 

    def get_learning_insights(self)->Dict:
        """
        Get comprehensive learning analytics and insights for current session.
        
        Combines learning profile data with session information to provide
        detailed performance analytics and progression tracking.
        
        Returns:
            Dict: Comprehensive learning insights including level, performance,
                 trends, and session statistics
        """
        try:
            insights = self.learning_profile.get_performance_insights()

            if self.learning_profile.recent_scores_history:
                latest_score = self.learning_profile.recent_scores_history[-1]
                insights.update({
                    "latest_score": latest_score,
                    "score_range":{
                        "min": min(self.learning_profile.recent_scores_history),
                        "max": max(self.learning_profile.recent_scores_history)
                    }
                })
            session_info = self.get_session_info()
            insights.update({
                "session_id": self.session_id,
                "documents_indexed": session_info.get("documents_indexed", 0),
                "engine_ready": self._is_engine_ready
            }
            )
            return insights
        except Exception as e:
            print(f"Error getting learning insights: {e}")
            return {
                "current_level": "unknown",
                "error": str(e)
            }
    def _handle_meta_question(self, triplet: ReasoningTriplet, language: str = "en") -> str:
        """
        Handle when student asks for help or expresses confusion.
        
        Increments stuck count, determines appropriate scaffolding strategy
        based on learning level, and generates helpful guidance.
        
        Args:
            triplet: Cached expert reasoning triplet for context
            language: Language code for response generation
            
        Returns:
            str: Scaffolded help response tailored to student's needs
        """
        try:
            # Increment stuck count for scaffolding
            stuck_count = self.memory_manager.increment_stuck_count()
            print(f"DEBUG: Scaffolding Level {stuck_count}: Student stuck count incremented")
            
            # Get scaffolding decision based on stuck count
            scaffolding_decision = self.scaffolding_system.decide_scaffolding_strategy(
                learning_level=self.learning_profile.current_level,
                stuck_count=stuck_count,
                triplet=triplet,

            )
            print(f"DEBUG: Scaffolding decision type: {scaffolding_decision.scaffold_strategy} (level {scaffolding_decision.stuck_count})")
            
            # Use dialogue generator to create the final response with scaffolding
            source_nodes = self.memory_manager.current_topic_source_nodes or []
            response = self.dialogue_generator.generate_scaffolding_response(
                triplet, 
                source_nodes, 
                self.memory_manager.memory,
                scaffolding_decision=scaffolding_decision,
                language=language
            )
            
            return response
            
        except Exception as e:
            print(f"Meta question handling error: {e}")
            traceback.print_exc()
            return get_ui_text("engine_step_by_step", language)
    
    def reset(self):
        """
        Reset the entire tutoring session to initial state.
        
        Clears conversation memory, resets learning profile to default level,
        and prepares for fresh tutoring session.
        """
        try:
            self.memory_manager.reset_session()
            self.learning_profile = SessionLearningProfile()  # Reset learning profile
            print("✅ Tutoring session reset successfully")
            
        except Exception as e:
            print(f"Error resetting session: {e}")
    
    def get_session_summary(self) -> dict:
        """
        Get comprehensive summary of current tutoring session.
        
        Combines memory statistics, learning insights, and adaptive features
        to provide complete session overview for analytics.
        
        Returns:
            dict: Session summary including memory stats, learning profile,
                 and adaptive tutoring metrics
        """
        try:
            memory_summary = self.memory_manager.get_session_summary()
            learning_insights = self.get_learning_insights()
            return {
                **memory_summary,
                "learning_profile": learning_insights,
                "adaptive_features":{
                    "level_adjustments": len(self.learning_profile.level_adjustments_history),
                    "performance_trend": learning_insights.get("performance_trend", "unknown"),
                    "current_strategy": getattr(self, '_last_adaptive_strategy', 'general_guidance'),
                }
            }
        except Exception as e:
            print(f"Error getting session summary: {e}")
            return {"error": "Unable to generate session summary"}
    
    def get_memory_stats(self) -> dict:
        """
        Get detailed memory usage statistics for current session.
        
        Returns:
            dict: Memory usage metrics including token counts, message counts,
                 and memory efficiency statistics
        """
        try:
            return self.memory_manager.get_memory_usage_stats()
            
        except Exception as e:
            print(f"Error getting memory stats: {e}")
            return {"error": "Unable to get memory statistics"}
    
    # Railway deployment methods for file upload and index management
    
    def upload_files(self, uploaded_files) -> str:
        """
        Upload files to Railway Volume and save metadata to database.
        
        Handles file deduplication using hash-based naming, saves files to
        user-specific directories, and stores metadata for indexing.

        Args:
            uploaded_files: List of uploaded file objects from Gradio interface
            
        Returns:
            str: Upload status message key for i18n translation
        """
        try:
            if not uploaded_files:
                return "engine_no_files"

            saved_files = 0
            user_upload_dir = os.path.join(config.USER_UPLOADS_DIR, self.session_id)
            os.makedirs(user_upload_dir, exist_ok=True)
            
            for file in uploaded_files:
                if file is None:
                    continue
                
                # Calculate file hash for deduplication
                file_hash = self.db_manager.calculate_file_hash(file.name)
                original_filename = os.path.basename(file.name)
                
                # Create unique filename
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
                    saved_files += 1
            
            if saved_files > 0:
                return "engine_upload_success_simple"
            else:
                return "engine_no_new_docs"

        except Exception as e:
            print(f"❌ Error during file upload: {e}") # 로그 추가
            traceback.print_exc()
            return "engine_upload_failed_simple"
    
    async def create_user_index(self) -> AsyncGenerator[str, None]:
        """
        Create user-specific vector index from uploaded documents.
        
        Processes uploaded PDFs through LlamaParse, creates multimodal vector
        index, updates database records, and reinitializes engine modules.
        
        Yields:
            dict: Progress updates with i18n keys and parameters for UI display
        """
        try:
            # Get uploaded documents from database
            documents = self.db_manager.get_user_documents(self.session_id)
            doc_to_index = [doc for doc in documents if not doc['indexed']]
            
            if not doc_to_index:
                yield {"key": "engine_no_new_docs", "params": {}}
                return
            
            # Prepare file paths for index creation
            file_paths = [doc['file_path'] for doc in doc_to_index]
            file_hashes = [doc['file_hash'] for doc in doc_to_index]
            
            # Import and run index creation
            from .persistence import create_index_from_files
          
            
            # Create user-specific index directory
            user_index_dir = os.path.join(config.USER_INDEXES_DIR, str(uuid.uuid4()))
            
            yield {
                "key": "engine_index_creation_start",
                "params": {
                    "count": len(file_paths)
                }
            }

            await create_index_from_files(file_paths, user_index_dir)

            yield {"key": "engine_index_updating_db", "params": {}}
            # Update database to mark documents as indexed
            self.db_manager.mark_documents_indexed(self.session_id, user_index_dir, file_hashes)

            yield {"key": "engine_index_reloading", "params": {}}
            # Reload the engine with new index
            self.index = await self._load_index_from_path_async(user_index_dir)

            yield {"key": "engine_index_initializing_modules", "params": {}}
            self._initialize_modules()
            self._is_engine_ready = True

            yield {
                "key": "engine_index_creation_success",
                "params": {
                    "count": len(file_paths)
                }
            }

        except Exception as e:
            yield {
                "key": "engine_index_creation_failed",
                "params": {
                    "error": str(e)
                }
            }
    def get_user_documents(self) -> List[Dict]:
        """
        Get list of user's uploaded documents with metadata.
        
        Returns:
            List[Dict]: List of document metadata including filenames,
                       hash values, file sizes, and indexing status
        """
        try:
            return self.db_manager.get_user_documents(self.session_id)
        except Exception as e:
            print(f"Error getting user documents: {e}")
            return []
    
    def get_session_info(self) -> Dict:
        """
        Get comprehensive session information including setup status.
        
        Returns:
            Dict: Session information including document counts, index status,
                 engine readiness, and document metadata for UI display
        """
        try:
            documents = self.get_user_documents()
            active_index = self.db_manager.get_active_index(self.session_id)
            
            return {
                'session_id': self.session_id,
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
        """
        Save conversation turn to database for history tracking and analytics.
        
        Args:
            user_message: Student's input message
            tutor_response: Generated tutor response
            context_used: Context information used in generating response
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
        """
        Check if engine is fully ready for tutoring interactions.
        
        Returns:
            bool: True if engine has loaded index and initialized all modules
        """
        return self.index is not None and self._is_engine_ready
    
    def get_tutoring_status(self) -> Dict[str, any]:
        """
        Get detailed status of tutoring readiness, prioritizing engine state.
        
        Provides comprehensive status including upload completion, index creation,
        engine readiness, and learning profile information for UI display.
        
        Returns:
            Dict[str, any]: Detailed status information including step completion,
                           document counts, engine state, and learning metrics
        """
        try:
            # The primary indicator of readiness is a fully loaded engine.
            if self._is_engine_ready and self.index is not None:
                active_index_info = self.db_manager.get_active_index(self.session_id)
                doc_count = active_index_info.get('document_count', 0) if active_index_info else 0
                
                return {
                    'step1_upload_complete': True,
                    'step2_index_complete': True,
                    'ready_for_tutoring': True,
                    'documents_count': doc_count,
                    'indexed_count': doc_count,
                    'engine_ready': True,
                    'has_index': True,
                    'learning_level': self.learning_profile.current_level.value,
                    'total_interactions': self.learning_profile.total_interactions,
                    'recent_performance': self.learning_profile.recent_scores_history[-1] if self.learning_profile.recent_scores_history else None
                }

            # Fallback to DB check if engine isn't ready yet
            documents = self.get_user_documents()
            has_documents = len(documents) > 0
            indexed_doc_count = len([d for d in documents if d['indexed']])
            has_indexed_docs = indexed_doc_count > 0
            
            return {
                'step1_upload_complete': has_documents,
                'step2_index_complete': has_indexed_docs,
                'ready_for_tutoring': False, # Engine is not ready at this point
                'documents_count': len(documents),
                'indexed_count': indexed_doc_count,
                'engine_ready': False,
                'has_index': False,
                'learning_level': self.learning_profile.current_level.value,
                'total_interactions': self.learning_profile.total_interactions
            }
        except Exception as e:
            print(f"Error getting tutoring status: {e}")
            return {
                'step1_upload_complete': False,
                'step2_index_complete': False,
                'ready_for_tutoring': False,
                'documents_count': 0,
                'indexed_count': 0,
                'engine_ready': False,
                'has_index': False,
                'error': str(e)
            }

    def can_start_tutoring(self) -> bool:
        """
        Check if tutoring can start (both upload and indexing steps completed).
        
        Returns:
            bool: True if both document upload and index creation are complete
        """
        status = self.get_tutoring_status()
        return status['step1_upload_complete'] and status['step2_index_complete']

    def find_matching_index(self, file_hashes: list[str]) -> Optional[Dict]:
        """
        Find the best matching existing index for given file hashes.
        
        Searches for exact matches first, then looks for superset matches
        to enable index reuse and avoid redundant processing.
        
        Args:
            file_hashes: List of file hash identifiers to match against
            
        Returns:
            Optional[Dict]: Metadata of best matching index, or None if not found
        """
        if not file_hashes:
            return None

        current_hashes = set(file_hashes)

        matching_indexes = self.db_manager.find_indexes_by_file_hash(list(current_hashes))
        if not matching_indexes:
            return None
        

        best_match = None
        smallest_superset_size = float('inf')

        for index_info in matching_indexes:
            
            try:
                index_hashes = set(json.loads(index_info['file_hashes']))
            except (json.JSONDecodeError, TypeError):
                index_hashes = set(index_info['file_hashes'])  # Fallback for legacy format

            # exact match
            if current_hashes == index_hashes:
                print(f"Exact match found: {index_info['index_path']}")
                return index_info
            
            # superset match
            if index_hashes.issuperset(current_hashes):
                if len(index_hashes) < smallest_superset_size:
                    smallest_superset_size = len(index_hashes)
                    best_match = index_info

        if best_match:
            print(f"Best matching index found: {best_match['index_path']}")
            
        return best_match


    async def load_existing_index(self, index_id: int) -> dict:
        """
        Load an existing index by ID and prepare engine for tutoring.
        
        Loads specified index into memory, initializes all dependent modules,
        sets engine as ready, and updates database to mark index as active.
        
        Args:
            index_id: Database ID of the index to load
            
        Returns:
            dict: Load status with i18n key and parameters for UI feedback
        """
        try:
            index_info = self.db_manager.get_index_by_id(index_id)
            if not index_info:
                return {"key": "engine_index_not_found", "params":{}}

            index_path = index_info['index_path']
            if not os.path.exists(index_path):
                return {"key": "engine_index_path_missing", "params": {}}

            # Load the index into memory
            self.index = await self._load_index_from_path_async(index_path)
            
            # Initialize all modules that depend on the index
            self._initialize_modules()
            
            # Set the engine as ready
            self._is_engine_ready = True
            
            # Update database to make this index active for the current session
            self.db_manager.set_active_index(self.session_id, index_id)
            
            print(f"✅ Successfully loaded index ID {index_id} and set as active for session {self.session_id}")
            
            doc_count = index_info.get('document_count', 'N/A')
            return {
                "key":"engine_load_success",
                "params":{"count": doc_count}
            }
            
        except Exception as e:
            self._is_engine_ready = False
            print(f"❌ Failed to load existing index: {e}")
            traceback.print_exc()
            return {"key": "engine_load_failed", "params": {"error": str(e)}}

