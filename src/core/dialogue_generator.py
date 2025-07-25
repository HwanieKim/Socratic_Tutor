#!/usr/bin/env python3
"""
Dialogue Generator Module

Handles Stage 2 logic:
- Socratic dialogue generation
- Context integration
- Response formatting with source attribution
"""

import os
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.core.llms import ChatMessage, MessageRole

from . import config
from .models import AnswerEvaluation, ReasoningTriplet, ScaffoldingDecision
from .prompts_template import TUTOR_TEMPLATE


class DialogueGenerator:
    """Handles Socratic dialogue generation"""
    
    def __init__(self):
        self.llm_tutor = GoogleGenAI(
            model_name=config.GEMINI_MODEL_NAME,
            api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.4
        )
    
    def generate_socratic_dialogue(
        self, 
        triplet: ReasoningTriplet, 
        source_nodes: list, 
        memory,
        answer_evaluation: AnswerEvaluation = None,
        scaffolding_decision: ScaffoldingDecision = None
    ) -> str:
        """
        Stage 2: Generate Socratic dialogue response
        
        Args:
            triplet: Expert reasoning triplet
            source_nodes: Retrieved source documents
            memory: Conversation history
            answer_evaluation: Optional evaluation of student's answer
            scaffolding_decision: Optional scaffolding decision for struggling students
            
        Returns:
            str: Generated tutor response
        """
        try:
            # Extract context and source information
            context_snippet, source_info = self._extract_context_info(source_nodes)
            
            # Get conversation history
            conversation_context = self._format_memory_context(memory)
            
            # Get the user's latest input
            recent_messages = memory.get_all()
            user_input = ""
            if recent_messages and recent_messages[-1].role == MessageRole.USER:
                user_input = recent_messages[-1].content
            
            # Prepare reasoning information
            full_reasoning_chain = triplet.reasoning_chain if triplet else "No specific reasoning available."
            
            # Handle scaffolding decision (overrides answer evaluation for meta questions)
            if scaffolding_decision:
                # Use scaffolding decision metadata to guide LLM generation
                evaluation_data = {
                    "evaluation": "scaffolding_request",
                    "scaffold_type": scaffolding_decision.scaffold_type,
                    "stuck_level": scaffolding_decision.stuck_level,
                    "reason": scaffolding_decision.reason,
                    "feedback": f"Generate {scaffolding_decision.scaffold_type} scaffolding at level {scaffolding_decision.stuck_level}"
                }
                print(f"DEBUG: Dialogue Generator - Using scaffolding: {scaffolding_decision.scaffold_type} (level {scaffolding_decision.stuck_level})")
            elif answer_evaluation:
                # Use provided answer evaluation
                evaluation_data = answer_evaluation.model_dump()
                print(f"DEBUG: Dialogue Generator - Using evaluation: {answer_evaluation.evaluation}")
            else:
                # Default for new questions - no formal evaluation needed
                evaluation_data = {
                    "evaluation": "new_question",
                    "feedback": "This is the first turn."
                }
                print("DEBUG: Dialogue Generator - Using new question mode")
            
            # Create tutor prompt
            tutor_prompt = TUTOR_TEMPLATE.format(
                context_snippet=context_snippet,
                source_info=source_info,
                reasoning_step=full_reasoning_chain,
                conversation_context=conversation_context,
                user_input=user_input,
                answer_evaluation_json=str(evaluation_data)
            )
            
            # Generate response
            response = self.llm_tutor.complete(tutor_prompt)
            return response.text.strip()
            
        except Exception as e:
            print(f"Dialogue generation error: {e}")
            # For new questions, don't use fallback that might trigger scaffolding
            if not answer_evaluation:
                return "I'd like to help you explore this topic. Let's start by thinking about what you already know. What comes to mind when you think about this concept?"
            else:
                return self._fallback_response(triplet, answer_evaluation)
    
    def _extract_context_info(self, source_nodes: list) -> tuple:
        """
        Extract context snippet and source information from retrieved nodes
        
        Args:
            source_nodes: List of retrieved source nodes
            
        Returns:
            tuple: (context_snippet, source_info)
        """
        context_snippet = "No specific context snippet found."
        source_info = "the provided text"
        
        if source_nodes:
            try:
                # Get the top source node
                top_node = source_nodes[0]
                context_snippet = top_node.node.get_content()
                
                # Extract source information from metadata
                metadata = top_node.node.metadata
                file_path = metadata.get('file_name', 'the document')
                page_label = metadata.get('page_label', '')
                
                # Extract only filename without path
                import os
                file_name = os.path.basename(file_path) if file_path else 'the document'
                
                # Format source info with filename only
                if page_label:
                    source_info = f"page {page_label} of {file_name}"
                else:
                    source_info = f"in {file_name}"
                    
                # Truncate context if too long
                if len(context_snippet) > 500:
                    context_snippet = context_snippet[:500] + "..."
                    
            except Exception as e:
                print(f"Error extracting context info: {e}")
        
        return context_snippet, source_info
    
    def _format_memory_context(self, memory) -> str:
        """
        Format conversation history for prompt context
        
        Args:
            memory: ChatMemoryBuffer
            
        Returns:
            str: Formatted conversation history
        """
        try:
            recent_messages = memory.get_all()
            
            if not recent_messages:
                return "This is the start of our conversation."
            
            # Format recent messages (last 6 for context)
            history_parts = []
            for msg in recent_messages[-6:]:
                role = "Student" if msg.role == MessageRole.USER else "Tutor"
                content = msg.content[:200] + "..." if len(msg.content) > 200 else msg.content
                history_parts.append(f"{role}: {content}")
            
            return "\n".join(history_parts)
            
        except Exception as e:
            print(f"Error formatting memory context: {e}")
            return "Previous conversation context unavailable."
    
    def _fallback_response(self, triplet: ReasoningTriplet, answer_evaluation: AnswerEvaluation) -> str:
        """
        Generate fallback response when main generation fails
        
        Args:
            triplet: Expert reasoning triplet
            answer_evaluation: Student answer evaluation
            
        Returns:
            str: Fallback response
        """
        try:
            # Basic response based on available information
            if answer_evaluation:
                if answer_evaluation.evaluation == "correct":
                    return ("Excellent! You've grasped the key concept. "
                           "Let's explore this topic further. What aspects would you like to investigate next?")
                elif answer_evaluation.evaluation == "partially_correct":
                    return ("You're on the right track! Let's build on what you've said. "
                           "Can you think of any other factors that might be relevant here?")
                else:
                    return ("Let's approach this from a different angle. "
                           "What do you think might be the most important factor to consider in this situation?")
            else:
                # New question fallback
                if triplet and triplet.question:
                    return (f"That's an interesting question about this topic. "
                           f"Let's explore it step by step. What do you think might be "
                           f"the first thing we should consider when thinking about this?")
                else:
                    return ("I'd like to help you explore this topic. "
                           "Can you tell me what specific aspect interests you most?")
                    
        except Exception as e:
            print(f"Fallback response error: {e}")
            return ("I'm here to help you learn through guided discovery. "
                   "What would you like to explore about this topic?")
    
    def enhance_response_with_encouragement(self, response: str, evaluation: AnswerEvaluation = None) -> str:
        """
        Add encouraging elements to the response
        
        Args:
            response: Base response
            evaluation: Optional answer evaluation
            
        Returns:
            str: Enhanced response with encouragement
        """
        if not evaluation:
            return response
        
        encouragement_starters = {
            "correct": ["Excellent!", "Great thinking!", "Perfect!", "Well done!"],
            "partially_correct": ["Good start!", "You're on track!", "Nice thinking!", "Good insight!"],
            "incorrect": ["Let's explore this!", "Good effort!", "Let's think differently!", "Interesting perspective!"]
        }
        
        # Add appropriate encouragement
        if evaluation.evaluation in encouragement_starters:
            starters = encouragement_starters[evaluation.evaluation]
            # Simple enhancement - could be made more sophisticated
            if not any(starter in response for starter in starters):
                import random
                starter = random.choice(starters)
                response = f"{starter} {response}"
        
        return response
