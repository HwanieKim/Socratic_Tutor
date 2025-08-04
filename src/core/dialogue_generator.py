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
from .prompts_template import get_tutor_template


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
        scaffolding_decision: ScaffoldingDecision = None,
        language: str = "en"
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
                print(f"DEBUG: Dialogue Generator - Using scaffolding: {scaffolding_decision.scaffold_type} (level {scaffolding_decision.stuck_level})", flush=True)
            elif answer_evaluation:
                # Use provided answer evaluation
                evaluation_data = answer_evaluation.model_dump()
                print(f"DEBUG: Dialogue Generator - Using evaluation: {answer_evaluation.evaluation}", flush=True)
            else:
                # Default for new questions - no formal evaluation needed
                evaluation_data = {
                    "evaluation": "new_question",
                    "feedback": "This is the first turn."
                }
                print("DEBUG: Dialogue Generator - Using new question mode", flush=True)
            
            tutor_template = get_tutor_template(language)
            # Create tutor prompt
            tutor_prompt = tutor_template.format(
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
                return self._get_new_question_fallback(language)
            else:
                return self._fallback_response(triplet, answer_evaluation, language)
    def _get_new_question_fallback(self, language: str) -> str:
        """
        Fallback response for new questions when generation fails
        """
        fallback_messages = {
        "en": "I'd like to help you explore this topic. Let's start by thinking about what you already know. What comes to mind when you think about this concept?",
        "it": "Vorrei aiutarti a esplorare questo argomento. Iniziamo pensando a quello che già sai. Cosa ti viene in mente quando pensi a questo concetto?",
        "es": "Me gustaría ayudarte a explorar este tema. Empecemos pensando en lo que ya sabes. ¿Qué te viene a la mente cuando piensas en este concepto?"
    }
    
        return fallback_messages.get(language, fallback_messages["en"])

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
    
    def _fallback_response(self, triplet: ReasoningTriplet, answer_evaluation: AnswerEvaluation, language:str = "en") -> str:
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
            response_messages = {
            "en": {
                "correct": "Excellent! You've grasped the key concept. Let's explore this topic further. What aspects would you like to investigate next?",
                "partial": "You're on the right track! Let's build on what you've said. Can you think of any other factors that might be relevant here?",
                "incorrect": "Let's approach this from a different angle. What do you think might be the most important factor to consider in this situation?",
                "new_question": "That's an interesting question about this topic. Let's explore it step by step. What do you think might be the first thing we should consider when thinking about this?",
                "default": "I'd like to help you explore this topic. Can you tell me what specific aspect interests you most?"
            },
            "it": {
                "correct": "Eccellente! Hai afferrato il concetto chiave. Esploriamo ulteriormente questo argomento. Quali aspetti vorresti investigare?",
                "partial": "Sei sulla strada giusta! Costruiamo su quello che hai detto. Puoi pensare ad altri fattori che potrebbero essere rilevanti qui?",
                "incorrect": "Approciamoci da un angolo diverso. Cosa pensi che potrebbe essere il fattore più importante da considerare in questa situazione?",
                "new_question": "È una domanda interessante su questo argomento. Esploriamolo passo dopo passo. Cosa pensi potrebbe essere la prima cosa da considerare?",
                "default": "Vorrei aiutarti a esplorare questo argomento. Puoi dirmi quale aspetto specifico ti interessa di più?"
            },
            
        }
            messages = response_messages.get(language, response_messages["en"])
            if answer_evaluation:
                if answer_evaluation.evaluation == "correct":
                    return messages["correct"]
                elif answer_evaluation.evaluation == "partially_correct":
                    return messages["partial"]
                else:
                    return messages["incorrect"]
            else:
                # New question fallback
                if triplet and triplet.question:
                    return messages["new_question"]
                else:
                    return messages["default"]

        except Exception as e:
            print(f"Fallback response error: {e}")
           # 최종 에러 폴백 메시지
            error_fallbacks = {
            "en": "I'm here to help you learn through guided discovery. What would you like to explore about this topic?",
            "it": "Sono qui per aiutarti ad imparare attraverso la scoperta guidata. Cosa vorresti esplorare di questo argomento?",
           }
        
            return error_fallbacks.get(language, error_fallbacks["en"])
    
    
    def enhance_response_with_encouragement(self, response: str, evaluation: AnswerEvaluation = None, language:str = "en") -> str:
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
        "en": {
            "correct": ["Excellent!", "Great thinking!", "Perfect!", "Well done!"],
            "partially_correct": ["Good start!", "You're on track!", "Nice thinking!", "Good insight!"],
            "incorrect": ["Let's explore this!", "Good effort!", "Let's think differently!", "Interesting perspective!"]
        },
        "it": {
            "correct": ["Eccellente!", "Ottimo ragionamento!", "Perfetto!", "Ben fatto!"],
            "partially_correct": ["Buon inizio!", "Sei sulla strada giusta!", "Buon ragionamento!", "Buona intuizione!"],
            "incorrect": ["Esploriamo questo!", "Buon tentativo!", "Pensiamo diversamente!", "Prospettiva interessante!"]
        }}
        starters = encouragement_starters.get(language, encouragement_starters["en"])
    
        # Add appropriate encouragement
        if evaluation.evaluation in starters:
            starter_options = starters[evaluation.evaluation]
        # Check if encouragement already exists
            if not any(starter.lower() in response.lower() for starter in starter_options):
                import random
                starter = random.choice(starter_options)
                response = f"{starter} {response}"
        
        return response
