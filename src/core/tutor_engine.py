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
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.llms import ChatMessage, MessageRole
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.google_genai import GoogleGenAI

from . import config 
from .models import ReasoningTriplet
from .prompts_template import JSON_CONTEXT_PROMPT, TUTOR_TEMPLATE

class TutorEngine:
    def __init__(self):
        load_dotenv()
        if not os.path.exists(config.PERSISTENCE_DIR):
            raise FileNotFoundError(f"Index not found at {config.PERSISTENCE_DIR}.")
        
        # Set the LLM and Embed Model in the global Settings.
        # All subsequent LlamaIndex components will now use these by default.
        # This is the single source of truth.
        Settings.llm = GoogleGenAI(
            model_name=config.GEMINI_MODEL_NAME, 
            api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.1  # Lower temperature for more consistent responses
        )
        Settings.embed_model = HuggingFaceEmbedding(model_name=config.EMBED_MODEL_NAME)
        
        # This allows using a different model/config for the conversational part.
        self.llm_tutor = GoogleGenAI(
            model_name=config.GEMINI_MODEL_NAME, 
            api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.3  # Slightly higher temperature for more natural conversation
        )

        # --- Component Setup  ---
        storage_context = StorageContext.from_defaults(persist_dir=config.PERSISTENCE_DIR)
    

        index = load_index_from_storage(storage_context)
        self.memory = ChatMemoryBuffer.from_defaults(token_limit=3000)
        
        # For now, we'll skip the condenser and just use the original question
        # This is more reliable for the tutor use case
        self.use_condenser = False

        # --- Engine 2: JSON Generation Specialist (Also simplified) ---
        self.pydantic_parser = PydanticOutputParser(ReasoningTriplet)
        json_prompt_template = JSON_CONTEXT_PROMPT.partial_format(
            format_instructions=self.pydantic_parser.get_format_string()
        )
        # This engine will also inherit the correct LLM from Settings.
        self.json_generator_engine = RetrieverQueryEngine.from_args(
            retriever=index.as_retriever(similarity_top_k=3),
            text_qa_template=json_prompt_template,
            response_mode="compact" 
        )

    def _stage1_internal_monologue(self, user_question: str) -> tuple[ReasoningTriplet, list]:
        """
        🧠 Stage 1: Expert Reasoning Model
        
        Role: Acts as a domain expert who analyzes the question using the knowledge base
        
        Process:
        1. Retrieves relevant context from vector database (similarity search)
        2. Combines question + context + conversation history
        3. Expert LLM generates structured reasoning (ReasoningTriplet):
           - question: The question being analyzed
           - reasoning_chain: Expert's step-by-step thinking process
           - answer: Expert's conclusion based on evidence
        
        Output: ReasoningTriplet + source_nodes (for citations)
        
        This stage captures the EXPERT KNOWLEDGE that will guide the tutoring process.
        """
        if self.use_condenser:
            condensed_response = self.condenser_engine.chat(user_question)
            standalone_question = condensed_response.response
            
            # FIX: If condenser returns None or empty string, fall back to original question
            if not standalone_question or str(standalone_question).strip().lower() in ['none', '']:
                standalone_question = user_question
                print(f"DEBUG: Condenser returned invalid response, using original question: {user_question}")
        else:
            # Use the original question directly but with conversation context
            standalone_question = user_question
            
            # ADD CONVERSATION CONTEXT: Include recent conversation for better continuity
            recent_messages = self.memory.get_all()
            if len(recent_messages) > 0:
                # Create context from recent conversation
                context_messages = []
                for msg in recent_messages[-4:]:  # Last 4 messages (2 turns)
                    if msg.role == MessageRole.USER:
                        context_messages.append(f"Previous question: {msg.content}")
                    elif msg.role == MessageRole.ASSISTANT:
                        context_messages.append(f"Previous response: {msg.content}")
                
                if context_messages:
                    conversation_context = "\n".join(context_messages)
                    standalone_question = f"Given this conversation context:\n{conversation_context}\n\nCurrent question: {user_question}"
            
            # Manually add the user question to memory for conversation continuity
            self.memory.put(ChatMessage(role=MessageRole.USER, content=user_question))

        response_obj = self.json_generator_engine.query(standalone_question)
        
        raw_llm_output = str(response_obj)
        internal_triplet = self.pydantic_parser.parse(raw_llm_output)
        
        source_nodes = response_obj.source_nodes
        
        if internal_triplet:
            internal_triplet.question = standalone_question

        return internal_triplet, source_nodes

    def _stage2_socratic_dialogue(self, triplet: ReasoningTriplet, source_nodes: list) -> str:
        """
        🎓 Stage 2: Unified Intent Classification + Socratic Tutoring

        Combines intent classification and Socratic response generation in one LLM call,
        using full context awareness.
        """
        # Prepare reasoning step
        first_reasoning_step = triplet.reasoning_chain.split('\n')[0].strip() if triplet.reasoning_chain else ""

        # Prepare source information and context snippet
        source_info = "N/A"
        context_snippet = "No specific context snippet found."
        if source_nodes:
            top_node = source_nodes[0]
            context_snippet = top_node.node.get_content()
            md = top_node.node.metadata
            source_info = f"Source: {md.get('file_name', 'N/A')}, Page: {md.get('page_label', 'N/A')}"

        # Build conversation history snippet
        recent = self.memory.get_all()
        conversation_context = "This is the start of our conversation."
        last_user_message_content = ""
        if recent:
            parts = []
            for msg in recent[-4:]:
                role = "Student" if msg.role == MessageRole.USER else "Tutor"
                parts.append(f"{role}: {msg.content}")
            conversation_context = "\n".join(parts)
            
            # The last message added in stage 1 is the user's current question
            if recent[-1].role == MessageRole.USER:
                last_user_message_content = recent[-1].content

        # Create unified prompt
        tutor_prompt = TUTOR_TEMPLATE.format(
            context_snippet=context_snippet,
            source_info=source_info,
            reasoning_step=first_reasoning_step,
            conversation_context=conversation_context,
            user_input=last_user_message_content
        )
        try:
            res = self.llm_tutor.complete(tutor_prompt)
            text = res.text
            # Extract actual response after 'Your response:' delimiter
            actual = text.split('Your response:')[-1].strip()
            # Log intent for debugging
            intent = "unknown"
            for line in text.split('\n'):
                if line.startswith('Intent:'):
                    intent = line.split('Intent:')[1].strip()
                    break
            print(f"DEBUG: Classified intent as: {intent}")
            # Add to memory
            self.memory.put(ChatMessage(role=MessageRole.ASSISTANT, content=actual))
            return actual
        except Exception as e:
            print(f"Error in unified tutoring: {e}")
            return "I encountered an issue while generating a response. Could you please rephrase your question?"

    def get_guidance(self, user_question: str) -> str:
        """
        🧠 2-Stage Reasoning Pipeline for AI Tutoring:
        
        The core philosophy: Expert Reasoning Model → Socratic Tutor Model
        
        Stage 1 (Expert): Analyzes question + knowledge base → Creates ReasoningTriplet
        - question: Original user question  
        - reasoning_chain: Expert's step-by-step thinking process
        - answer: Expert's conclusion
        
        Stage 2 (Tutor): Uses Expert's reasoning → Guides student with Socratic questions
        - Takes Expert's reasoning_chain as input
        - Generates guiding questions instead of direct answers
        - Helps student discover the path to the answer
        
        This design ensures:
        - Expert knowledge is captured in reasoning_chain
        - Students learn through guided discovery
        - Answers are grounded in knowledge base
        - Natural topic relevance (no hardcoded filters)
        """
        # Input validation
        if not user_question or not user_question.strip():
            return "I'd be happy to help! Please ask me a question."
        
        # Sanitize and validate input
        user_question = user_question.strip()
        if len(user_question) > 1000:  # Limit very long questions
            return "Your question is quite long. Could you please break it down into smaller, more specific questions?"
        
        try:
            # 🧠 Stage 1: Expert Reasoning Model creates ReasoningTriplet
            internal_triplet, source_nodes = self._stage1_internal_monologue(user_question)
            
            # Check if the Expert found sufficient information in knowledge base
            if (internal_triplet and 
                internal_triplet.answer and 
                ("insufficient information" in internal_triplet.answer.lower() or
                 "no specific context" in internal_triplet.answer.lower())):
                return ("I don't have enough information about that topic in my knowledge base. "
                       "Could you please ask about something related to the materials we're studying?")
            
            # 🎓 Stage 2: Tutor Model guides student using Expert's reasoning
            guidance = self._stage2_socratic_dialogue(internal_triplet, source_nodes)
            return guidance
            
        except (ValidationError, ValueError) as e:
            print(f"--- FAILED TO PARSE LLM RESPONSE --- \n{e}\n---------------")
            return "I'm having a little trouble structuring my thoughts on that one. Could you try asking in a different way?"
        except Exception as e:
            error_msg = str(e).lower()
            # Handle specific error types more gracefully
            if "429" in error_msg or "quota" in error_msg or "rate" in error_msg:
                return "I'm experiencing high demand right now. Please wait a moment and try again."
            elif "network" in error_msg or "connection" in error_msg:
                return "I'm having trouble connecting. Please check your internet connection and try again."
            else:
                print(f"--- UNEXPECTED ERROR --- \n{e}\n---------------")
                return "An unexpected error occurred. Please try again."

    def reset(self):
        """Reset conversation memory."""
        self.memory.reset()