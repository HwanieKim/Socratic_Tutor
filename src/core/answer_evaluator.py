#!/usr/bin/env python3
"""
Answer Evaluator Module

Handles Stage 1b logic:
- Student answer evaluation
- Comparison with expert answers
- AnswerEvaluation generation
"""

import os
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.core.output_parsers import PydanticOutputParser

from . import config
from .models import AnswerEvaluation, ReasoningTriplet
from .prompts_template import ANSWER_EVALUATION_PROMPT, get_answer_evaluation_prompt


class AnswerEvaluator:
    """Handles student answer evaluation logic"""
    
    def __init__(self):
        self.llm = GoogleGenAI(
            model_name=config.GEMINI_MODEL_NAME,
            api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.3
        )
        self.pydantic_parser = PydanticOutputParser(AnswerEvaluation)
    
    def evaluate_student_answer(
        self, 
        student_answer: str, 
        expert_triplet: ReasoningTriplet,
        tutor_last_message: str = "",
        conversation_context: str = "",
        language: str = "en"
    ) -> AnswerEvaluation:
        """
        Stage 1b: Evaluate student's answer against expert knowledge in context
        
        Args:
            student_answer: The student's response
            expert_triplet: Cached expert reasoning and answer
            tutor_last_message: The tutor's last question/prompt
            conversation_context: Recent conversation history
            
        Returns:
            AnswerEvaluation: Structured evaluation with feedback
        """
        try:
            if not expert_triplet:
                return AnswerEvaluation(
                    evaluation="error",
                    feedback="No expert context available for comparison."
                )
            
            # Create evaluation prompt with full context
            prompt_template = get_answer_evaluation_prompt(language)
            prompt = prompt_template.format(
                original_question=expert_triplet.question,
                expert_reasoning_chain=expert_triplet.reasoning_chain,
                expert_answer=expert_triplet.answer,
                tutor_last_message=tutor_last_message,
                student_answer=student_answer,
                conversation_context=conversation_context,
                format_instructions=self.pydantic_parser.get_format_string()
            )
            
            # Get LLM evaluation
            response = self.llm.complete(prompt)
            
            try:
                evaluation = self.pydantic_parser.parse(response.text)
                return evaluation
            except Exception as parse_error:
                print(f"Evaluation parsing failed: {parse_error}")
                return self._fallback_evaluation(student_answer, expert_triplet, language)
                
        except Exception as e:
            print(f"Answer evaluation error: {e}")
            return AnswerEvaluation(
                evaluation="error",
                feedback=f"Error during evaluation: {str(e)}"
            )
    
    def _create_fallback_evaluation(self, student_answer: str, language: str = "en") -> AnswerEvaluation:
        """Create fallback evaluation when all else fails"""
        fallback_messages = {
        "en": "I see your response. Let me help you think through this step by step.",
        "it": "Vedo la tua risposta. Lascia che ti aiuti a ragionare passo dopo passo.",
        "es": "Veo tu respuesta. Déjame ayudarte a pensar esto paso a paso."
    }
    
        feedback = fallback_messages.get(language, fallback_messages["en"])
    
        return AnswerEvaluation(
            evaluation="needs_guidance",
            feedback=feedback,
            suggestions=[]
        )
    def _extract_suggestions(self, response_text: str, language: str = "en") -> list:
        """
        extract suggestions from LLM response text
        """

        suggestions = []
        lines = response_text.split('\n')

        suggestions_keywords = {
            "en": ["suggestion", "consider", "try", "think about", "perhaps"],
            "it": ["suggerimento", "considera", "prova", "pensa a", "forse", "magari", "potresti"]
        }

        keywords = suggestions_keywords.get(language, suggestions_keywords["en"])
        for line in lines:
            line = line.strip()
            if line.startswith('- ') or line.startswith('• '):
                suggestions.append(line[2:])
            elif any(keyword in line.lower() for keyword in keywords):
                suggestions.append(line)

        return suggestions[:4]  # Limit to top 4 suggestions

    def _parse_evaluation_response(self,response_text: str, language:str = "en") -> AnswerEvaluation:
        try:    
            evaluation_keywords = {
                "en": {
                    "correct": ["correct", "right", "accurate", "good"],
                    "partial": ["partial", "somewhat", "close", "nearly"],
                    "incorrect": ["incorrect", "wrong", "inaccurate", "not quite"]
                },
                "it": {
                    "correct": ["corretto", "giusto", "accurato", "bene"],
                    "partial": ["parziale", "quasi", "vicino", "non del tutto"],
                    "incorrect": ["sbagliato", "errato", "non accurato", "non giusto"]
                }
            }
            keywords = evaluation_keywords.get(language, evaluation_keywords["en"])
            response_lower = response_text.lower()

            if any(keyword in response_lower for keyword in keywords["correct"]):
                evaluation ="correct"
            elif any(keyword in response_lower for keyword in keywords["partial"]):
                evaluation ="partially_correct"
            elif any(keyword in response_lower for keyword in keywords["incorrect"]):
                evaluation ="incorrect"
            else: 
                evaluation = "needs_guidance"
            return AnswerEvaluation(
                evaluation = evaluation,
                feedback= response_text,
                suggestions = self._extract_suggestions(response_text, language)
            )
        except Exception as e:
            print (f"Error parsing evaluation response: {e}")
            return self._create_fallback_evaluation("",language)
        

    def _fallback_evaluation(self, student_answer: str, expert_triplet: ReasoningTriplet, language: str = "en") -> AnswerEvaluation:
        """
        Fallback evaluation when structured parsing fails
        
        Args:
            student_answer: Student's response
            expert_triplet: Expert knowledge
            
        Returns:
            AnswerEvaluation: Basic evaluation
        """
        try:
            # Simple keyword-based evaluation
            student_lower = student_answer.lower()
            expert_answer_lower = expert_triplet.answer.lower()
            
            # Extract key terms from expert answer
            expert_words = set(expert_answer_lower.split())
            student_words = set(student_lower.split())
            
            # Calculate overlap
            common_words = expert_words.intersection(student_words)
            overlap_ratio = len(common_words) / len(expert_words) if expert_words else 0
            
            feedback_messages = {
                "en":{
                    "correct": "Good job! You've captured the key concepts.",
                    "partially_correct": "You're on the right track, but let's explore this further.",
                    "incorrect": "Let's think about this differently. What else might be relevant here?"
                },
                "it": {
                    "correct": "Ottimo lavoro! Hai catturato i concetti chiave.",
                    "partially_correct": "Sei sulla strada giusta, ma esploriamo ulteriormente.",
                    "incorrect": "Pensiamo a questo in modo diverso. Cosa potrebbe essere rilevante qui?"
            }}
            messages = feedback_messages.get(language, feedback_messages["en"])
            # Determine evaluation based on overlap
            if overlap_ratio > 0.6:
                evaluation = "correct"
                feedback = messages["correct"]
            elif overlap_ratio > 0.3:
                evaluation = "partially_correct"
                feedback = messages["partially_correct"]
            else:
                evaluation = "incorrect"
                feedback = messages["incorrect"]

            return AnswerEvaluation(
                evaluation=evaluation,
                feedback=feedback
            )
            
        except Exception as e:
            print(f"Fallback evaluation error: {e}")
            error_messages = {
            "en": "Unable to evaluate response properly. Let's continue with the discussion.",
            "it": "Impossibile valutare correttamente la risposta. Continuiamo con la discussione."
        }
            error_msg = error_messages.get(language, error_messages["en"])
            return AnswerEvaluation(
                evaluation="error",
                feedback=error_msg
            )
    
    def classify_answer_quality(self, evaluation: AnswerEvaluation) -> str:
        """
        Classify the quality of the answer for scaffolding decisions
        
        Args:
            evaluation: The AnswerEvaluation object
            
        Returns:
            str: Quality classification ('high', 'medium', 'low', 'error')
        """
        if evaluation.evaluation == "correct":
            return "high"
        elif evaluation.evaluation == "partially_correct":
            return "medium"
        elif evaluation.evaluation == "incorrect":
            return "low"
        else:
            return "error"
    
    def generate_feedback_summary(self, evaluations: list) -> dict:
        """
        Generate a summary of multiple evaluations for analytics
        
        Args:
            evaluations: List of AnswerEvaluation objects
            
        Returns:
            dict: Summary statistics
        """
        if not evaluations:
            return {"total": 0, "correct": 0, "partial": 0, "incorrect": 0, "accuracy": 0.0}
        
        correct_count = sum(1 for e in evaluations if e.evaluation == "correct")
        partial_count = sum(1 for e in evaluations if e.evaluation == "partially_correct")
        incorrect_count = sum(1 for e in evaluations if e.evaluation == "incorrect")
        total = len(evaluations)
        
        accuracy = (correct_count + 0.5 * partial_count) / total if total > 0 else 0.0
        
        return {
            "total": total,
            "correct": correct_count,
            "partial": partial_count,
            "incorrect": incorrect_count,
            "accuracy": round(accuracy, 2)
        }
