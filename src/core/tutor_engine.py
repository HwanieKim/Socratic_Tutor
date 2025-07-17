# tutor_engine.py (Definitive High-Level API Version)

import os
from dotenv import load_dotenv
from pydantic import ValidationError

# --- THE FIX: STEP 1 ---
# Import the global Settings object from LlamaIndex
from llama_index.core import (
    Settings,
    StorageContext,
    load_index_from_storage
)
# --- END STEP 1 ---

from llama_index.core.output_parsers import PydanticOutputParser
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.retrievers import VectorIndexRetriever, QueryFusionRetriever
from llama_index.retrievers.bm25 import BM25Retriever
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.llms import ChatMessage, MessageRole
from llama_index.embeddings.voyageai import VoyageEmbedding
from llama_index.llms.google_genai import GoogleGenAI

from . import config 
from .models import ReasoningTriplet, AnswerEvaluation
from .prompts_template import (
    JSON_CONTEXT_PROMPT, 
    TUTOR_TEMPLATE, 
    INTENT_CLASSIFIER_PROMPT, 
    ANSWER_EVALUATION_PROMPT,
    FOLLOW_UP_TYPE_CLASSIFIER_PROMPT
)

class TutorEngine:
    def __init__(self):
        load_dotenv()
        if not os.path.exists(config.PERSISTENCE_DIR):
            raise FileNotFoundError(f"Index not found at {config.PERSISTENCE_DIR}.")
        
        # Set the LLM and Embed Model in the global Settings.
        # All subsequent LlamaIndex components will now use these by default.
        # This is the single source of truth.
        Settings.llm = GoogleGenAI(
            model_name=config.GEMINI_REASONING_MODEL_NAME, 
            api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.2  # Lower temperature for more consistent responses
        )
        Settings.embed_model = VoyageEmbedding(
            model_name="voyage-multimodal-3",
            voyage_api_key=os.getenv("VOYAGE_API_KEY"),
            truncation=True
            )
        
        # This allows using a different model/config for the conversational part.
        self.llm_tutor = GoogleGenAI(
            model_name=config.GEMINI_MODEL_NAME, 
            api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.4  # Slightly higher temperature for more natural conversation
        )

        # --- Context Caching ---
        # Cache the reasoning context for the current topic to avoid re-running RAG
        # on every follow-up question. This is reset when a new topic is detected.
        self.current_topic_triplet = None
        self.current_topic_source_nodes = None

        # --- Component Setup  ---
        storage_context = StorageContext.from_defaults(persist_dir=config.PERSISTENCE_DIR)
        
        # Load the index from storage
        index = load_index_from_storage(storage_context)
        self.memory = ChatMemoryBuffer.from_defaults(token_limit=3000)
        
        # For now, we'll skip the condenser and just use the original question
        # This is more reliable for the tutor use case
        self.use_condenser = False

        # --- Engine 2: JSON Generation Specialist (Also simplified) ---
        self.pydantic_parser = PydanticOutputParser(ReasoningTriplet)

        #  The JSON prompt template is now a single, robust version.
        json_prompt_template = JSON_CONTEXT_PROMPT.partial_format(
            format_instructions=self.pydantic_parser.get_format_string()
        )

        # --- Fusion Retriever configuration ---
        #  Vector Retriever (semantic similarity search)
        vector_retriever = VectorIndexRetriever(
            index=index,
            similarity_top_k=7 
        )

        # BM25 Retriever (keyword based search)
        all_nodes = list(index.docstore.docs.values())
        bm25_retriever = BM25Retriever.from_defaults(
            nodes=all_nodes, 
            similarity_top_k=7 
        )
        
        hybrid_retriever = QueryFusionRetriever(
            retrievers=[vector_retriever, bm25_retriever],
            similarity_top_k=5,
            num_queries=1,
            mode="reciprocal_rerank"
        )
       
        # This engine will also inherit the correct LLM from Settings.
        self.json_generator_engine = RetrieverQueryEngine.from_args(
            retriever=hybrid_retriever,
            text_qa_template=json_prompt_template,
            response_mode="compact" 
        )
        
        # ---  Pydantic Parsers for Structured Output ---
        self.eval_parser = PydanticOutputParser(AnswerEvaluation)
        
        self.stuck_count  = 0

    def _stage1_internal_monologue(self, user_question: str) -> tuple[ReasoningTriplet, list]:
        """
        Stage 1: Expert Reasoning Model
        
        Role: Acts as a domain expert who analyzes the question using the knowledge base
        
        Process:
        1. Retrieves relevant context from vector database (similarity search + keyword search)
        2. Combines question + context + conversation history
        3. Expert LLM generates structured reasoning (ReasoningTriplet):
           - question: The question being analyzed
           - reasoning_chain: Expert's step-by-step thinking process
           - answer: Expert's conclusion based on evidence
        
        Output: ReasoningTriplet + source_nodes (for citations)
        
        This stage captures the EXPERT KNOWLEDGE that will guide the tutoring process.
        """
        # [FIX] The conversation history for the expert model should not include
        # the user's latest message, as that is what is being analyzed.
        recent_messages = self.memory.get_all()
        
        # The history is everything *before* the last message.
        history_messages = []
        if len(recent_messages) > 1:
            for msg in recent_messages[-5:-1]: # Exclude the last message
                role = "Student" if msg.role == MessageRole.USER else "Tutor"
                history_messages.append(f"{role}: {msg.content}")
        
        conversation_history_str = "\n".join(history_messages)
        
        # We create a detailed query for the LLM that includes the history.
        # This helps the LLM understand the context of the user's question.
        llm_query_str = (
            f"Given this recent conversation history:\n{conversation_history_str}\n\n"
            f"Analyze the student's last message: '{user_question}'\n\n"
            f"Find the relevant information from the knowledge base to answer it."
        )

        # The retriever uses the simple, clean `user_question` for the best search results.
        # The LLM, however, will use the more context-rich `llm_query_str` via the prompt template.
        # The query to the engine should be the full contextual query, not just the user_question.
        # The prompt template within the engine is designed to handle this.
        response_obj = self.json_generator_engine.query(llm_query_str) 
        
        raw_llm_output = str(response_obj)
        internal_triplet = self.pydantic_parser.parse(raw_llm_output)
        
        source_nodes = response_obj.source_nodes
        
        if internal_triplet:
            # We store the original, simple question for clarity if needed later.
            internal_triplet.question = user_question

        return internal_triplet, source_nodes

    def _stage0_intent_classification(self) -> str:
        """
        Stage 0: Lightweight Intent Classification

        Determines if the user input is a new question requiring a RAG search
        or a follow-up to the ongoing conversation.
        """
        recent_messages = self.memory.get_all()
        # Ensure there's a history to classify
        if not recent_messages:
            return "new_question" # Default to new question if no history

        # Format conversation history for the classifier
        parts = []
        for msg in recent_messages[-5:]: # Use last 5 messages for context
            role = "Student" if msg.role == MessageRole.USER else "Tutor"
            parts.append(f"{role}: {msg.content}")
        conversation_context = "\n".join(parts)
        
        # The last message is the one we want to classify
        user_input = recent_messages[-1].content

        prompt = INTENT_CLASSIFIER_PROMPT.format(
            conversation_context=conversation_context,
            user_input=user_input
        )

        try:
            response = self.llm_tutor.complete(prompt)
            # Clean up the response to get only the intent string
            intent = response.text.strip().lower().replace("intent:", "").strip()
            print(f"DEBUG: Classified intent (Stage 0) as: {intent}")
            # Basic validation
            if intent in ["new_question", "follow_up"]:
                return intent
            else:
                return "new_question" # Default to new_question on failure
        except Exception as e:
            print(f"Error in Stage 0 Intent Classification: {e}")
            return "new_question" # Default to new_question on error

    def _stage0b_classify_follow_up_type(self) -> str:
        """
        [NEW] Stage 0b: Classify the *type* of follow-up.

        Distinguishes between a genuine answer and a meta-question (e.g., "I don't know").
        """
        recent_messages = self.memory.get_all()
        if len(recent_messages) < 2: # Need at least a tutor question and a student response
            return "meta_question" # Not enough context, treat as meta

        student_response = recent_messages[-1].content
        tutor_question = ""
        # Find the last message from the assistant (the tutor)
        for msg in reversed(recent_messages[:-1]):
            if msg.role == MessageRole.ASSISTANT:
                tutor_question = msg.content
                break
        
        if not tutor_question:
            return "meta_question" # Could not find the tutor's question

        prompt = FOLLOW_UP_TYPE_CLASSIFIER_PROMPT.format(
            tutor_question=tutor_question,
            student_response=student_response
        )

        try:
            response = self.llm_tutor.complete(prompt)
            follow_up_type = response.text.strip().lower().replace("type:", "").strip()
            print(f"DEBUG: Classified follow-up type (Stage 0b) as: {follow_up_type}")
            if follow_up_type in ["answer", "meta_question"]:
                return follow_up_type
            return "meta_question" # Default on failure
        except Exception as e:
            print(f"Error in Stage 0b Follow-up Classification: {e}")
            return "meta_question"

    def _stage1b_check_answer(self, student_answer: str) -> AnswerEvaluation:
        """
        Stage 1b: Evaluate Student's Answer (for follow-up turns)

        Compares the student's answer against the cached expert answer.
        
        Output: An AnswerEvaluation pydantic object.
        """
        if not self.current_topic_triplet:
            return AnswerEvaluation(
                evaluation="error",
                feedback="No context available."
            )

        # We need the original, simple question and the expert's answer from our cache
        original_question = self.current_topic_triplet.question
        expert_answer = self.current_topic_triplet.answer

        # Format conversation history for the evaluator
        recent_messages = self.memory.get_all()
        parts = []
        for msg in recent_messages[-5:-1]: # History before the student's latest answer
            role = "Student" if msg.role == MessageRole.USER else "Tutor"
            parts.append(f"{role}: {msg.content}")
        conversation_context = "\n".join(parts)

        prompt = ANSWER_EVALUATION_PROMPT.format(
            original_question=original_question,
            expert_answer=expert_answer,
            conversation_context=conversation_context,
            student_answer=student_answer,
            format_instructions=self.eval_parser.get_format_string()
        )

        try:
            response = self.llm_tutor.complete(prompt)
            eval_obj = self.eval_parser.parse(response.text)
            print(f"DEBUG: Answer evaluation (Stage 1b) object: {eval_obj}")
            return eval_obj
        except (ValidationError, ValueError) as e:
            print(f"Error parsing Stage 1b Answer Evaluation: {e}")
            return AnswerEvaluation(
                evaluation="error",
                feedback="Failed to parse evaluation."
            )
        except Exception as e:
            print(f"Error in Stage 1b Answer Evaluation: {e}")
            return AnswerEvaluation(
                evaluation="error",
                feedback="An error occurred during evaluation."
            )

    def _stage2_socratic_dialogue(self, answer_evaluation: AnswerEvaluation = None) -> str:
        """
        Stage 2: Socratic Dialogue Generation

        Generates a Socratic response using the expert context, conversation history,
        and now, a structured AnswerEvaluation object.
        """
        triplet = self.current_topic_triplet
        source_nodes = self.current_topic_source_nodes

        full_reasoning_chain = triplet.reasoning_chain if triplet and triplet.reasoning_chain else "No reasoning provided."

        source_info = "the provided text"
        context_snippet = "No specific context snippet found."
        if source_nodes:
            top_node = source_nodes[0]
            context_snippet = top_node.node.get_content()
            md = top_node.node.metadata
            page_label = md.get('page_label', None)
            # only file_name 
            file_path = md.get('file_name', 'the document')
            file_name = os.path.basename(file_path) if file_path else 'the document'
            
            if page_label:
                source_info = f"at {page_label} of {file_name}"
            else:
                source_info = f"{file_name}"

        if not answer_evaluation:
            answer_evaluation = AnswerEvaluation(
                evaluation="new_question",
                feedback="This is the first turn."
            )

        recent = self.memory.get_all()
        conversation_context = "This is the start of our conversation."
        last_user_message_content = ""
        if recent:
            parts = []
            for msg in recent[-5:-1]: # Use last 5 messages excluding the latest
                role = "Student" if msg.role == MessageRole.USER else "Tutor"
                parts.append(f"{role}: {msg.content}")
            
            if parts:
                conversation_context = "\n".join(parts)
            
            if recent and recent[-1].role == MessageRole.USER:
                last_user_message_content = recent[-1].content

        tutor_prompt = TUTOR_TEMPLATE.format(
            context_snippet=context_snippet,
            source_info=source_info,
            reasoning_step=full_reasoning_chain,
            answer_evaluation_json=answer_evaluation.model_dump_json(),
            conversation_context=conversation_context,
            user_input=last_user_message_content
        )
        try:
            res = self.llm_tutor.complete(tutor_prompt)
            actual = res.text.strip()
            self.memory.put(ChatMessage(role=MessageRole.ASSISTANT, content=actual))
            return actual
        except Exception as e:
            print(f"Error in Socratic dialogue: {e}")
            return "I encountered an issue while generating a response. Could you please rephrase your question?"

    def get_guidance(self, user_question: str) -> str:
        """
        Router, directing the conversation to the appropriate
        sub-pipeline based on the classified intent of the user.
        """
        # Input validation
        if not user_question or not user_question.strip():
            return "I'd be happy to help! Please ask me a question."
        
        # Sanitize and validate input
        user_question = user_question.strip()
        if len(user_question) > 1000:  # Limit very long questions
            return "Your question is quite long. Could you please break it down into smaller, more specific questions?"
        
        # Add user's question to memory FIRST, so stage 0 can see it
        self.memory.put(ChatMessage(role=MessageRole.USER, content=user_question))

        try:
            #  Stage 0: Classify intent to decide the pipeline path
            intent = self._stage0_intent_classification()

            if intent == 'new_question':
                return self._pipeline_new_question(user_question)
            else: # intent == 'follow_up'
                return self._pipeline_follow_up(user_question)
            
        except Exception as e:
            error_msg = str(e).lower()
            # Handle specific error types more gracefully
            if ("429" in error_msg or "quota" in error_msg or "rate" in error_msg 
                or "503" in error_msg or "unavailable" in error_msg or "overloaded" in error_msg):
                return "I'm experiencing high demand right now, which may cause delays. Please wait a moment and try your question again."
            elif "network" in error_msg or "connection" in error_msg:
                return "I'm having trouble connecting. Please check your internet connection and try again."
            else:
                print(f"--- UNEXPECTED ERROR IN ROUTER --- \n{e}\n---------------")
                return "An unexpected error occurred. Please try again."

    def _pipeline_new_question(self, user_question: str) -> str:
        """
        Pipeline for handling entirely new questions.
        """
        print("DEBUG: Executing pipeline: new_question")
        
        self.stuck_count = 0  # Reset stuck count for new questions

        #  Stage 1: Expert Reasoning Model creates ReasoningTriplet
        internal_triplet, source_nodes = self._stage1_internal_monologue(user_question)
        
        # Check if the Expert found sufficient information
        if (not internal_triplet or not internal_triplet.answer or 
            "insufficient information" in internal_triplet.answer.lower()):
            # Clear the cache if the new topic has no information
            self.current_topic_triplet = None
            self.current_topic_source_nodes = None
            self.memory.put(ChatMessage(role=MessageRole.ASSISTANT, content="I can't find that in my knowledge base."))
            return ("I don't have enough information about that topic in my knowledge base. "
                   "Could you please ask about something related to the materials we're studying?")
        
        # Cache the new context
        self.current_topic_triplet = internal_triplet
        self.current_topic_source_nodes = source_nodes
        
        #  Stage 2: Tutor Model guides student (no answer evaluation needed yet)
        return self._stage2_socratic_dialogue()

    def _pipeline_follow_up(self, user_question: str) -> str:
        """
        Pipeline for handling follow-up responses.
        """
        print("DEBUG: Executing pipeline: follow_up")
        if not self.current_topic_triplet:
            print("DEBUG: Follow-up intent with no cached context. Re-routing to new_question pipeline.")
            return self._pipeline_new_question(user_question)

        #  Classify the type of follow-up
        follow_up_type = self._stage0b_classify_follow_up_type()

        if follow_up_type == 'answer':
            self.stuck_count = 0  # Reset meta question count on valid answer
            # Evaluate the student's answer
            print("DEBUG: Follow-up type is an answer. Evaluating.")
            evaluation = self._stage1b_check_answer(user_question)
            # Generate guidance based on the evaluation
            return self._stage2_socratic_dialogue(answer_evaluation=evaluation)
        else:  # follow_up_type == 'meta_question'
            self.stuck_count += 1
            # Generate guidance without evaluation (e.g., give a hint)
            print("DEBUG: Follow-up type is a meta_question. Skipping evaluation.")
            return self._provide_scaffolded_help()

    def _provide_scaffolded_help(self) -> str:
        """
        Provide scaffolded help when the student is stuck.
        
        This method is called when the student asks a meta-question or
        the tutor detects that the student is struggling.
        """
        if self.stuck_count == 1:
            return self._generate_focused_hint()
        elif self.stuck_count == 2:
            return self._generate_analogy_hint()
        else:  # self.stuck_count >= 3:
            # After 3 consecutive meta-questions, we provide a multiple-choice assessment
            return self._generate_multiple_choice_assessment()

    def _generate_focused_hint(self) -> str:
        """[Scaffold Level 1] Generates a focused hint on the next logical step."""
        print("DEBUG: Scaffolding Level 1: Focus & Simplify")
        scaffold_eval = AnswerEvaluation(
            evaluation="scaffold_focus_prompt",
            feedback="Student is stuck for the first time. Provide a focused prompt on the next logical step."
        )
        return self._stage2_socratic_dialogue(answer_evaluation=scaffold_eval)
    def _generate_analogy_hint(self) -> str:
        """[Scaffold Level 2] Generates an analogy hint to help the student connect concepts."""
        print("DEBUG: Scaffolding Level 2: Analogy")
        scaffold_eval = AnswerEvaluation(
            evaluation="scaffold_analogy",
            feedback="Student is stuck for the second time. Provide a helpful analogy to help them understand the core concept."
        )
        return self._stage2_socratic_dialogue(answer_evaluation=scaffold_eval)

    def _generate_multiple_choice_assessment(self) -> str:
        """[Scaffold Level 3] Generates a multiple-choice assessment to gauge understanding."""
        print("DEBUG: Scaffolding Level 3: Multiple Choice Assessment")
        scaffold_eval = AnswerEvaluation(
            evaluation="scaffold_multiple_choice",
            feedback="Student is stuck for the third time. Provide a multiple-choice question to guide them to the correct answer."
        )
        return self._stage2_socratic_dialogue(answer_evaluation=scaffold_eval)

    def reset(self):
        """Reset conversation memory and cached context."""
        self.stuck_count = 0  # Reset stuck count
        self.memory.reset()
        self.current_topic_triplet = None
        self.current_topic_source_nodes = None