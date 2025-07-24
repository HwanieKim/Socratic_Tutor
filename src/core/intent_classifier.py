#!/usr/bin/env python3
"""
Intent Classification Module

Handles Stage 0 and Stage 0b classification logic:
- Stage 0: new_question vs follow_up
- Stage 0b: answer vs meta_question
"""

import os
from llama_index.core.llms import ChatMessage, MessageRole
from llama_index.llms.google_genai import GoogleGenAI
from . import config
from .prompts_template import INTENT_CLASSIFIER_PROMPT, FOLLOW_UP_TYPE_CLASSIFIER_PROMPT


class IntentClassifier:
    """Handles all intent classification logic"""
    
    def __init__(self):
        self.llm = GoogleGenAI(
            model_name=config.GEMINI_MODEL_NAME,
            api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.2
        )
    
    def classify_intent(self, user_input: str, memory) -> str:
        """
        Stage 0: Classify user intent as 'new_question' or 'follow_up'
        
        Args:
            user_input: Current user message
            memory: ChatMemoryBuffer with conversation history
            
        Returns:
            str: "new_question" or "follow_up"
        """
        try:
            # Get recent conversation history
            recent_messages = memory.get_all()
            if len(recent_messages) < 2:
                return "new_question"
            
            # Format conversation history for prompt
            history_messages = []
            for msg in recent_messages[-6:]:  # Last 6 messages for context
                role = "Student" if msg.role == MessageRole.USER else "Tutor"
                history_messages.append(f"{role}: {msg.content}")
            
            conversation_history_str = "\n".join(history_messages)
            
            # Create classification prompt
            prompt = INTENT_CLASSIFIER_PROMPT.format(
                conversation_history=conversation_history_str,
                current_input=user_input
            )
            
            # Get LLM response
            response = self.llm.complete(prompt)
            classification = response.text.strip().lower()
            
            # Extract classification result
            if "new_question" in classification:
                return "new_question"
            elif "follow_up" in classification:
                return "follow_up"
            else:
                # Default to new_question if unclear
                return "new_question"
                
        except Exception as e:
            print(f"Intent classification error: {e}")
            return "new_question"  # Safe default
    
    def classify_follow_up_type(self, user_input: str, memory) -> str:
        """
        Stage 0b: Classify follow-up type as 'answer' or 'meta_question'
        
        Args:
            user_input: Student's follow-up response
            memory: ChatMemoryBuffer with conversation history
            
        Returns:
            str: "answer" or "meta_question"
        """
        try:
            # Get the last tutor question from memory
            recent_messages = memory.get_all()
            
            # Find the most recent tutor message (should be a question)
            tutor_question = "No previous question found."
            for msg in reversed(recent_messages):
                if msg.role == MessageRole.ASSISTANT:
                    tutor_question = msg.content
                    break
            
            # Create classification prompt
            prompt = FOLLOW_UP_TYPE_CLASSIFIER_PROMPT.format(
                tutor_question=tutor_question,
                student_response=user_input
            )
            
            # Get LLM response
            response = self.llm.complete(prompt)
            classification = response.text.strip().lower()
            
            # Extract classification result
            if "answer" in classification and "meta" not in classification:
                return "answer"
            elif "meta_question" in classification:
                return "meta_question"
            else:
                # Analyze input characteristics as fallback
                return self._fallback_classification(user_input)
                
        except Exception as e:
            print(f"Follow-up classification error: {e}")
            return self._fallback_classification(user_input)
    
    def _fallback_classification(self, user_input: str) -> str:
        """
        Fallback classification based on input characteristics
        
        Args:
            user_input: Student's input
            
        Returns:
            str: "answer" or "meta_question"
        """
        # Simple heuristics for classification
        meta_indicators = [
            "don't know", "not sure", "confused", "what do you mean",
            "can you explain", "help", "hint", "stuck", "lost",
            "unclear", "don't understand", "more detail"
        ]
        
        user_lower = user_input.lower()
        
        # Check for meta-question indicators
        for indicator in meta_indicators:
            if indicator in user_lower:
                return "meta_question"
        
        # Check for very short responses (likely confusion)
        if len(user_input.strip()) < 10:
            words = user_input.strip().split()
            if len(words) <= 2:
                return "meta_question"
        
        # Default to answer attempt
        return "answer"
