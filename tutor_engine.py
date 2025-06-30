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

import config 
from models import ReasoningTriplet
from prompts_template import JSON_CONTEXT_PROMPT, TUTOR_PROMPT_TEMPLATE, TUTOR_FOLLOWUP_TEMPLATE

class TutorEngine:
    def __init__(self):
        load_dotenv()
        if not os.path.exists(config.PERSISTENCE_DIR):
            raise FileNotFoundError(f"Index not found at {config.PERSISTENCE_DIR}.")
        
        # --- THE FIX: STEP 2 ---
        # Set the LLM and Embed Model in the global Settings.
        # All subsequent LlamaIndex components will now use these by default.
        # This is the single source of truth.
        Settings.llm = GoogleGenAI(model_name=config.GEMINI_MODEL_NAME, api_key=os.getenv("GOOGLE_API_KEY"))
        Settings.embed_model = HuggingFaceEmbedding(model_name=config.EMBED_MODEL_NAME)
        # --- END STEP 2 ---

        # We can still define a specialized tutor LLM if we want.
        # This allows using a different model/config for the conversational part.
        self.llm_tutor = GoogleGenAI(model_name=config.GEMINI_MODEL_NAME, api_key=os.getenv("GOOGLE_API_KEY"))

        # --- Component Setup (Now much cleaner and more reliable) ---
        storage_context = StorageContext.from_defaults(persist_dir=config.PERSISTENCE_DIR)
        # We no longer need to pass `embed_model`. It uses the global Setting.
        index = load_index_from_storage(storage_context)
        # Since the CondenseQuestionChatEngine is having issues, let's use a simpler approach
        # For a tutor system, most questions are standalone and don't need complex condensation
        self.memory = ChatMemoryBuffer.from_defaults(token_limit=3000)
        
        # For now, we'll skip the condenser and just use the original question
        # This is more reliable for the tutor use case
        self.use_condenser = False
        
        # Track conversation turns for different response styles
        self.conversation_turn = 0

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
        Generate internal reasoning about the user's question using retrieved context.
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
        This method uses our specialized `llm_tutor` for the conversational part.
        Uses different templates based on conversation turn.
        """
        if not triplet or not triplet.reasoning_chain:
            return "I'm having trouble reasoning through that. Could you please rephrase your question?"

        first_reasoning_step = triplet.reasoning_chain.split('\n')[0].strip()
        
        source_info = "N/A"
        context_snippet = "No specific context snippet found."
        if source_nodes:
            top_node = source_nodes[0]
            context_snippet = top_node.node.get_content()
            metadata = top_node.node.metadata
            source_info = f"Source: {metadata.get('file_name', 'N/A')}, Page: {metadata.get('page_label', 'N/A')}"
        
        # Increment conversation turn
        self.conversation_turn += 1
        
        # Choose template based on conversation turn
        if self.conversation_turn == 1:
            # First turn: Use detailed template with source citation
            tutor_prompt = TUTOR_PROMPT_TEMPLATE.format(
                context_snippet=context_snippet,
                source_info=source_info,
                reasoning_step=first_reasoning_step
            )
        else:
            # Subsequent turns: Use follow-up template with page suggestion
            tutor_prompt = TUTOR_FOLLOWUP_TEMPLATE.format(
                source_info=source_info,
                reasoning_step=first_reasoning_step
            )
        
        # Using our specialized tutor LLM for the final friendly response
        tutor_response = self.llm_tutor.complete(tutor_prompt)
        
        # Manually add the AI's final response to memory to complete the turn
        self.memory.put(ChatMessage(role=MessageRole.ASSISTANT, content=tutor_response.text))
        
        return tutor_response.text

    def get_guidance(self, user_question: str) -> str:
        """This method remains unchanged."""
        try:
            internal_triplet, source_nodes = self._stage1_internal_monologue(user_question)
            guidance = self._stage2_socratic_dialogue(internal_triplet, source_nodes)
            return guidance
        except (ValidationError, ValueError) as e:
            print(f"--- FAILED TO PARSE LLM RESPONSE --- \n{e}\n---------------")
            return "I'm having a little trouble structuring my thoughts on that one. Could you try asking in a different way?"
        except Exception as e:
            print(f"--- UNEXPECTED ERROR --- \n{e}\n---------------")
            return "An unexpected error occurred. Please try again."

    def reset(self):
        """Reset conversation memory and turn counter."""
        self.memory.reset()
        self.conversation_turn = 0