#!/usr/bin/env python3
"""
RAG Retriever Module

Handles Stage 1 logic:
- Hybrid retrieval (Vector + BM25)
- Expert reasoning and knowledge extraction
- ReasoningTriplet generation
"""

import os
from typing import Tuple, List
from llama_index.core import Settings
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.retrievers import VectorIndexRetriever, QueryFusionRetriever
try:
    from llama_index.retrievers.bm25 import BM25Retriever
except ImportError:
    print("Warning: BM25Retriever not available. Using vector retriever only.")
    BM25Retriever = None
from llama_index.core.output_parsers import PydanticOutputParser
from llama_index.core.llms import ChatMessage, MessageRole
from llama_index.llms.google_genai import GoogleGenAI

from . import config
from .models import ReasoningTriplet
from .prompts_template import JSON_CONTEXT_PROMPT


class RAGRetriever:
    """Handles RAG retrieval and expert reasoning"""
    
    def __init__(self, index):
        self.index = index
        self.llm_reasoning = GoogleGenAI(
            model_name=config.GEMINI_REASONING_MODEL_NAME,
            api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.2
        )
        
        # Setup hybrid retriever
        self._setup_retrievers()
        
        # Setup JSON parser for structured output
        self.pydantic_parser = PydanticOutputParser(ReasoningTriplet)
        self.json_generator_engine = RetrieverQueryEngine.from_args(
            retriever=self.hybrid_retriever,
            llm=self.llm_reasoning,
            text_qa_template=JSON_CONTEXT_PROMPT
        )
    
    def _setup_retrievers(self):
        """Setup hybrid retrieval system"""
        try:
            # Vector retriever
            vector_retriever = VectorIndexRetriever(
                index=self.index,
                similarity_top_k=5,
                embed_model=Settings.embed_model
            )
            
            # BM25 retriever (if available)
            if BM25Retriever:
                bm25_retriever = BM25Retriever.from_defaults(
                    index=self.index,
                    similarity_top_k=5
                )
                
                # Hybrid fusion retriever
                self.hybrid_retriever = QueryFusionRetriever(
                    retrievers=[vector_retriever, bm25_retriever],
                    similarity_top_k=5,
                    num_queries=1,
                    mode="reciprocal_rerank"
                )
            else:
                # Use vector retriever only
                self.hybrid_retriever = vector_retriever
            
        except Exception as e:
            print(f"Error setting up retrievers: {e}")
            # Fallback to basic vector retriever
            self.hybrid_retriever = VectorIndexRetriever(
                index=self.index,
                similarity_top_k=5
            )
    
    def perform_rag_search(self, user_question: str, memory) -> Tuple[ReasoningTriplet, List]:
        """
        Stage 1: Perform RAG search and generate expert reasoning
        
        Args:
            user_question: The user's question
            memory: ChatMemoryBuffer for conversation context
            
        Returns:
            Tuple[ReasoningTriplet, List]: Reasoning triplet and source nodes
        """
        try:
            # Format query with conversation history for better context
            llm_query_str = self._format_query_with_history(user_question, memory)
            
            # Get format instructions for JSON output
            format_instructions = self.pydantic_parser.format
            
            # Query the retrieval engine
            response_obj = self.json_generator_engine.query(llm_query_str)
            source_nodes = response_obj.source_nodes
            
            # Parse the structured response
            raw_llm_output = response_obj.response
            
            try:
                internal_triplet = self.pydantic_parser.parse(raw_llm_output)
            except Exception as parse_error:
                print(f"JSON parsing failed: {parse_error}")
                # Fallback parsing
                internal_triplet = self._fallback_parse(raw_llm_output, user_question)
            
            return internal_triplet, source_nodes
            
        except Exception as e:
            print(f"RAG search error: {e}")
            # Return empty triplet on error
            return ReasoningTriplet(
                question=user_question,
                reasoning_chain="Error occurred during information retrieval.",
                answer="I apologize, but I encountered an error while searching for information. Please try again."
            ), []
    
    def _format_query_with_history(self, user_question: str, memory) -> str:
        """Format query with conversation history for better context"""
        try:
            # Get recent conversation history
            recent_messages = memory.get_all()
            
            if len(recent_messages) <= 1:
                return user_question
            
            # Format recent messages for context
            history_messages = []
            for msg in recent_messages[-4:]:  # Last 4 messages for context
                role = "Student" if msg.role == MessageRole.USER else "Tutor"
                history_messages.append(f"{role}: {msg.content}")
            
            conversation_history_str = "\n".join(history_messages)
            
            # Create contextualized query
            llm_query_str = (
                f"Given this recent conversation history:\n{conversation_history_str}\n\n"
                f"Analyze the student's last message: '{user_question}'\n\n"
                f"If this appears to be a follow-up or continuation, interpret it in the context "
                f"of the ongoing conversation. If it's a new question, treat it independently."
            )
            
            return llm_query_str
            
        except Exception as e:
            print(f"Error formatting query with history: {e}")
            return user_question
    
    def _fallback_parse(self, raw_output: str, user_question: str) -> ReasoningTriplet:
        """Fallback parsing when JSON parsing fails"""
        try:
            # Try to extract key components from raw output
            lines = raw_output.strip().split('\n')
            
            question = user_question
            reasoning_chain = "Based on the available information..."
            answer = "I found relevant information, but need to process it further."
            
            # Simple parsing logic
            for line in lines:
                if 'question' in line.lower() and ':' in line:
                    question = line.split(':', 1)[1].strip().strip('"')
                elif 'reasoning' in line.lower() and ':' in line:
                    reasoning_chain = line.split(':', 1)[1].strip().strip('"')
                elif 'answer' in line.lower() and ':' in line:
                    answer = line.split(':', 1)[1].strip().strip('"')
            
            return ReasoningTriplet(
                question=question,
                reasoning_chain=reasoning_chain,
                answer=answer
            )
            
        except Exception as e:
            print(f"Fallback parsing error: {e}")
            return ReasoningTriplet(
                question=user_question,
                reasoning_chain="Unable to process the information properly.",
                answer="I apologize, but I'm having difficulty processing the information right now."
            )
    
    def validate_knowledge_sufficiency(self, triplet: ReasoningTriplet) -> bool:
        """
        Validate if the retrieved knowledge is sufficient to answer the question
        
        Args:
            triplet: The generated ReasoningTriplet
            
        Returns:
            bool: True if knowledge is sufficient, False otherwise
        """
        # Check for insufficient information indicators
        insufficient_indicators = [
            "insufficient information",
            "not enough information",
            "cannot determine",
            "unable to answer",
            "information not available",
            "context doesn't contain"
        ]
        
        answer_lower = triplet.answer.lower()
        reasoning_lower = triplet.reasoning_chain.lower()
        
        for indicator in insufficient_indicators:
            if indicator in answer_lower or indicator in reasoning_lower:
                return False
        
        # Check for minimum content length
        if len(triplet.answer.strip()) < 20:
            return False
        
        return True
