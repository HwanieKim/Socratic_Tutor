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
from .prompts_template import  get_intent_classifier_prompt,get_follow_up_type_classifier_prompt


class IntentClassifier:
    """Handles all intent classification logic"""
    
    def __init__(self):
        self.llm = GoogleGenAI(
            model_name=config.GEMINI_MODEL_NAME,
            api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.2
        )

    def classify_intent(self, user_input: str, memory, language: str = "en") -> str:
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
            prompt_template = get_intent_classifier_prompt(language)
            prompt = prompt_template.format(
                conversation_history=conversation_history_str,
                user_input=user_input
            )
            
            # Get LLM response
            response = self.llm.complete(prompt)
            
            # 강화된 파싱 사용
            return self._parse_intent_response(response.text)
            
        except Exception as e:
            print(f"Intent classification error: {e}")
            return "new_question"  # Safe default

    def classify_follow_up_type(self, user_input: str, memory, language: str = "en") -> str:
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
            prompt_template = get_follow_up_type_classifier_prompt(language)
            prompt = prompt_template.format(
                tutor_question=tutor_question,
                student_response=user_input
            )
            
            # Get LLM response
            response = self.llm.complete(prompt)
            
            # 강화된 파싱 사용
            return self._parse_follow_up_type_response(response.text)
            
        except Exception as e:
            print(f"Follow-up classification error: {e}")
            return self._fallback_classification(user_input, language)

    def _fallback_classification(self, user_input: str, language: str = "en") -> str:
        """
        Fallback classification based on input characteristics
        
        Args:
            user_input: Student's input
            
        Returns:
            str: "answer" or "meta_question"
        """
        # Simple heuristics for classification
        meta_indicators = {
            "en": [
                "don't know", "not sure", "confused", "what do you mean",
                "can you explain", "help", "hint", "stuck", "lost",
                "unclear", "don't understand", "more detail"
            ],
            "it": [
                "non so", "non sono sicuro", "confuso", "cosa intendi",
                "puoi spiegare", "aiuto", "suggerimento", "bloccato", "perso",
                "poco chiaro", "non capisco", "più dettagli", "più informazioni", "spiegazione",
                "chiarimento", "aiutami", "aiuto per capire", "domanda"
            ]
        }
        indicators = meta_indicators.get(language, meta_indicators["en"])
        user_lower = user_input.lower()
        
        # Check for meta-question indicators
        for indicator in indicators:
            if indicator in user_lower:
                return "meta_question"
        
        # Check for very short responses (likely confusion)
        if len(user_input.strip()) < 10:
            words = user_input.strip().split()
            if len(words) <= 2:
                return "meta_question"
        
        # Default to answer attempt
        return "answer"
    
    def _parse_intent_response(self, response_text: str) -> str:
        """Enhanced parsing for intent classification with fallback strategies"""
        response_lower = response_text.lower().strip()
        
        # 1차: 정확한 영어 키워드 매칭
        if "new_question" in response_lower:
            return "new_question"
        elif "follow_up" in response_lower:
            return "follow_up"
        
        # 2차: 변형 케이스 처리
        new_question_variants = ["new question", "newquestion", "new-question", "new_topic", "different question"]
        follow_up_variants = ["follow up", "followup", "follow-up", "continuation", "continue", "same topic"]
        
        if any(variant in response_lower for variant in new_question_variants):
            return "new_question"
        elif any(variant in response_lower for variant in follow_up_variants):
            return "follow_up"
        
        # 3차: 이탈리아어 대비책 (혹시 모르는 상황)
        italian_mappings = {
            "nuova_domanda": "new_question",
            "nuova domanda": "new_question", 
            "domanda nuova": "new_question",
            "seguito": "follow_up",
            "continuazione": "follow_up"
        }
        
        for italian_key, english_value in italian_mappings.items():
            if italian_key in response_lower:
                print(f"WARNING: Found Italian keyword '{italian_key}', mapping to '{english_value}'")
                return english_value
        
        # 최종 폴백
        print(f"WARNING: Could not parse intent response: '{response_text}', defaulting to 'new_question'")
        return "new_question"

    def _parse_follow_up_type_response(self, response_text: str) -> str:
        """Enhanced parsing for follow-up type classification"""
        response_lower = response_text.lower().strip()
        
        # 1차: 정확한 키워드
        if "answer" in response_lower and "meta" not in response_lower:
            return "answer"
        elif "meta_question" in response_lower:
            return "meta_question"
        
        # 2차: 변형 처리
        answer_variants = ["response", "reply", "attempt", "trying to answer"]
        meta_variants = ["help", "confused", "clarify", "explain", "meta question", "meta-question"]
        
        if any(variant in response_lower for variant in answer_variants):
            return "answer"
        elif any(variant in response_lower for variant in meta_variants):
            return "meta_question"
        
        # 3차: 이탈리아어 대비책
        italian_mappings = {
            "risposta": "answer",
            "tentativo": "answer",
            "meta_domanda": "meta_question",
            "domanda_meta": "meta_question",
            "aiuto": "meta_question",
            "confuso": "meta_question"
        }
        
        for italian_key, english_value in italian_mappings.items():
            if italian_key in response_lower:
                print(f"WARNING: Found Italian keyword '{italian_key}', mapping to '{english_value}'")
                return english_value
        
        # 최종 폴백
        print(f"WARNING: Could not parse follow-up type: '{response_text}', defaulting to 'meta_question'")
        return "meta_question"
