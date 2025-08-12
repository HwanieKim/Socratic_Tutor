#!/usr/bin/env python3
"""
Answer Evaluator Module

Handles Stage 1b logic:
- Student answer evaluation
- Comparison with expert answers
- AnswerEvaluation generation
"""

import json
import os
import re
import traceback
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.core.output_parsers import PydanticOutputParser

from . import config
from .models import  ReasoningTriplet,MultidimensionalScores,EnhancedAnswerEvaluation
from .prompts_template import get_enhanced_evaluation_prompt


class AnswerEvaluator:
    """Handles student answer evaluation logic"""
    
    def __init__(self):
        """
        Initialize the AnswerEvaluator with LLM and parser components.
        
        Sets up Google GenAI model and Pydantic parser for structured evaluation output.
        """
        self.llm = GoogleGenAI(
            model_name=config.GEMINI_MODEL_NAME,
            api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.2
        )
        self.enhanced_parser = PydanticOutputParser(EnhancedAnswerEvaluation)
    
   
    
                            
    def evaluate_student_answer_enhanced(
            self,
            student_answer: str,
            expert_triplet: ReasoningTriplet,
            tutor_last_message: str = "",
            conversation_context: str = "", 
            language: str = "en"
    ) -> EnhancedAnswerEvaluation:
        """
        Enhanced evaluation with weighted multidimensional assessment
        
        Args:
            student_answer: The student's response
            expert_triplet: Cached expert reasoning and answer
            tutor_last_message: The tutor's last question/prompt
            conversation_context: Recent conversation history
            language: Language code for evaluation
            
        Returns:
            EnhancedAnswerEvaluation: Comprehensive weighted evaluation
        """
        try:
            if not expert_triplet:
                return self._create_error_evaluation("no_expert_context", language)
            
            print(f"[DEBUG] Evaluating student answer with enhanced evaluation logic: {student_answer[:50]}...")
            prompt_template = get_enhanced_evaluation_prompt(language)
            formatted_prompt = prompt_template.format(
                original_question=expert_triplet.question,
                expert_reasoning_chain=expert_triplet.reasoning_chain,
                expert_answer=expert_triplet.answer,
                tutor_last_message=tutor_last_message,
                student_answer=student_answer,
                conversation_context=conversation_context,
                format_instructions=self.enhanced_parser.get_format_string()
            )

            # Get LLM evaluation
            response = self.llm.complete(formatted_prompt)

            try:
                evaluation = self.enhanced_parser.parse(response.text)
                return evaluation
            
            except Exception as parse_error:
                print(f"Enhanced evaluation parsing failed: {parse_error}")
                return self._parse_enhanced_evaluation_fallback(response.text, language)

        except Exception as e:
            print(f"Enhanced evaluation error: {e}")
            traceback.print_exc()
            return self._create_fallback_enhanced_evaluation("no_expert_context")


    
    
    def _parse_enhanced_evaluation_fallback(self, response_text: str, language:str ) ->EnhancedAnswerEvaluation:
        """
        Fallback parsing for enhanced evaluation response when structured parsing fails.
        
        Args:
            response_text: Raw LLM response text to parse
            language: Language code for localization
            
        Returns:
            EnhancedAnswerEvaluation: Parsed evaluation or fallback with default values
        """
        try:
            # Attempt to parse JSON-like structure
            json_match = re.search(r"```json\s*(\{.*?\})\s*```|(\{.*?\})", response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1) if json_match.group(1) else json_match.group(2)
                data = json.loads(json_str)

                return EnhancedAnswerEvaluation(
                    binary_evaluation=self._validate_binary_evaluation(data.get("binary_evaluation", "unclear")),
                    multidimensional_scores=MultidimensionalScores(
                        conceptual_accuracy=self._validate_score(data.get("multidimensional_scores", {}).get("conceptual_accuracy", 0.5)),
                        reasoning_coherence=self._validate_score(data.get("multidimensional_scores", {}).get("reasoning_coherence", 0.5)),
                        use_of_evidence_and_rules=self._validate_score(data.get("multidimensional_scores", {}).get("use_of_evidence_and_rules", 0.5)),
                        conceptual_integration=self._validate_score(data.get("multidimensional_scores", {}).get("conceptual_integration", 0.5)),
                        clarity_of_expression=self._validate_score(data.get("multidimensional_scores", {}).get("clarity_of_expression", 0.5))
                    ),
                    reasoning_quality=self._validate_reasoning_quality(data.get("reasoning_quality", "fair")),
                    misconceptions=data.get("misconceptions", []),
                    strengths=data.get("strengths", []),
                    feedback=data.get("feedback", "evaluation incomplete"),
                    reasoning_analysis=data.get("reasoning_analysis", "Enhanced evaluation incomplete")
                )

        except (json.JSONDecodeError, AttributeError) as e:
            print(f"Enhanced evaluation fallback parsing error: {e}")
        
        # If parsing fails, return a default fallback evaluation
        return self._create_fallback_enhanced_evaluation("", language)

    def _create_error_evaluation(self, reason: str) -> EnhancedAnswerEvaluation:
        """
        Create an error evaluation when expert context is missing or errors occur.
        
        Args:
            reason: Description of the error that occurred
            
        Returns:
            EnhancedAnswerEvaluation: Error evaluation with zero scores
        """
        return EnhancedAnswerEvaluation(
            binary_evaluation="error",
            multidimensional_scores=MultidimensionalScores(
                conceptual_accuracy=0.0,
                reasoning_coherence=0.0,
                use_of_evidence_and_rules=0.0,
                conceptual_integration=0.0,
                clarity_of_expression=0.0
            ),
            reasoning_quality="none",
            misconceptions=[],
            strengths=[],
            feedback=f"error occurred: {reason}",
            reasoning_analysis="error occurred"
        )

    def _parse_enhanced_evaluation_response(self, response_text: str, language: str = "en") -> EnhancedAnswerEvaluation:
        """
        Parse LLM response text into EnhancedAnswerEvaluation structure.
        
        Args:
            response_text: Raw response text from LLM
            language: Language code for error handling
            
        Returns:
            EnhancedAnswerEvaluation: Parsed evaluation or fallback
        """
        import json
        try:
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1

            if json_start >=0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                data = json.loads(json_str)
                return EnhancedAnswerEvaluation(
                    binary_evaluation=self._validate_binary_evaluation(data.get("binary_evaluation", "")),
                    multidimensional_scores=MultidimensionalScores(
                        conceptual_accuracy=self._validate_score(data.get("multidimensional_scores", {}).get("conceptual_accuracy", 0.5)),
                        reasoning_coherence=self._validate_score(data.get("multidimensional_scores", {}).get("reasoning_coherence", 0.5)),
                        use_of_evidence_and_rules=self._validate_score(data.get("multidimensional_scores", {}).get("use_of_evidence_and_rules", 0.5)),
                        conceptual_integration=self._validate_score(data.get("multidimensional_scores", {}).get("conceptual_integration", 0.5)),
                        clarity_of_expression=self._validate_score(data.get("multidimensional_scores", {}).get("clarity_of_expression", 0.5))
                    ),
                    reasoning_quality=self._validate_reasoning_quality(data.get("reasoning_quality", "")),
                    misconceptions=data.get("misconceptions", []),
                    strengths=data.get("strengths", []),
                    feedback=data.get("feedback", "evaluation incomplete"),
                    reasoning_analysis=data.get("reasoning_analysis", "Enhanced evaluation incomplete")
                )
        except Exception as e:
            print(f"Fallback parsing error: {e}")

        return self._create_fallback_enhanced_evaluation("", language)
            
    def _validate_binary_evaluation(self, binary_evaluation: str) -> str:
        """
        Validate binary evaluation value against allowed options.
        
        Args:
            binary_evaluation: Binary evaluation string to validate
            
        Returns:
            str: Valid binary evaluation or "error" if invalid
        """
        valid_values = [
            "correct", "partially_correct", "incorrect_but_related",
            "incorrect", "unclear", "error"
        ]
        return binary_evaluation if binary_evaluation in valid_values else "error"
    

    def _validate_score(self,score) -> float:
        """
        Validate and normalize score values to 0.0-1.0 range.
        
        Args:
            score: Score value to validate (any numeric type)
            
        Returns:
            float: Normalized score between 0.0 and 1.0, or 0.0 if invalid
        """
        try:
            score_float = float(score)
            return max(0.0, min(score_float, 1.0))
        except (ValueError, TypeError):
            return 0.0  # Default to 0 if conversion fails
        
    def _validate_reasoning_quality(self, reasoning_quality: str) -> str:
        """
        Validate reasoning quality value against allowed options.
        
        Args:
            reasoning_quality: Reasoning quality string to validate
            
        Returns:
            str: Valid reasoning quality or "none" if invalid
        """
        valid_qualities = ["excellent", "good", "fair", "poor", "none"]
        return reasoning_quality if reasoning_quality in valid_qualities else "none"
    
    
    def _create_fallback_enhanced_evaluation(self, reason: str, language: str) -> EnhancedAnswerEvaluation:
        """
        Create fallback enhanced evaluation when all parsing methods fail.
        
        Args:
            reason: Reason for fallback evaluation
            language: Language code for localized feedback
            
        Returns:
            EnhancedAnswerEvaluation: Safe fallback evaluation with default values
        """
        print("[DEBUG] Creating fallback enhanced evaluation")
        fallback_messages = {
            "en": "The answer has been evaluated, but the evaluation could not be processed correctly. Please review the answer.",
            "it": "La risposta è stata valutata, ma la valutazione non è stata elaborata correttamente. Si prega di rivedere la risposta."
        }
        feedback = fallback_messages.get(language, fallback_messages["en"])
        return EnhancedAnswerEvaluation(
            binary_evaluation="unclear",
            multidimensional_scores=MultidimensionalScores(
                conceptual_accuracy=0.5,
                reasoning_coherence=0.5,
                use_of_evidence_and_rules=0.5,
                conceptual_integration=0.5,
                clarity_of_expression=0.5
            ),
            reasoning_quality="fair",
            misconceptions=[],
            strengths=[],
            feedback=f"{feedback}, Reason: {reason}",
            reasoning_analysis="Fallback evaluation used due to processing error"
        )
    
    
    def generate_enhanced_feedback_summary(self, enhanced_evaluations:list) -> dict:
        """
        Generate a summary of multiple enhanced evaluations for analytics
        
        Args:
            evaluations: List of EnhancedAnswerEvaluation objects
            
        Returns:
            dict: Summary statistics
        """
        if not enhanced_evaluations:
            return {"total": 0, "average_overall_score":0.0, "weighted_metrics": {}}

        total = len(enhanced_evaluations)

        # calculate averages
        overall_scores = [e.overall_score for e in enhanced_evaluations]
        average_overall_score = sum(overall_scores) / total if total > 0 else 0.0

        # calculate weighted metrics
        weighted_metrics = {
            "conceptual_accuracy": sum(e.multidimensional_scores.conceptual_accuracy for e in enhanced_evaluations) / total,
            "reasoning_coherence": sum(e.multidimensional_scores.reasoning_coherence for e in enhanced_evaluations) / total,
            "use_of_evidence_and_rules": sum(e.multidimensional_scores.use_of_evidence_and_rules for e in enhanced_evaluations) / total,
            "conceptual_integration": sum(e.multidimensional_scores.conceptual_integration for e in enhanced_evaluations) / total,
            "clarity_of_expression": sum(e.multidimensional_scores.clarity_of_expression for e in enhanced_evaluations) / total,
        }

        binary_counts = {}
        for e in enhanced_evaluations:
            binary_counts[e.binary_evaluation] = binary_counts.get(e.binary_evaluation, 0) + 1
        return {
            "total": total,
            "average_overall_score": round(average_overall_score, 3),
            "score_range": {
                "min": round(min(overall_scores), 3),
                "max": round(max(overall_scores), 3)
            },
            "weighted_metrics": {k: round(v, 3) for k, v in weighted_metrics.items()},
            "binary_distribution": binary_counts,
            "performance_trend": "improving" if len(overall_scores) >= 2 and overall_scores[-1] > overall_scores[-2] else "stable"
        }
       