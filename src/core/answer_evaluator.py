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
        Fallback parsing for enhanced evaluation response
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
        Create an error evaluation when expert context is missing
        
        Args:
            error_type: Type of error encountered
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
        valid_values = [
            "correct", "partially_correct", "incorrect_but_related",
            "incorrect", "unclear", "error"
        ]
        return binary_evaluation if binary_evaluation in valid_values else "error"
    

    def _validate_score(self,score) -> float:
        """control the score value"""
        try:
            score_float = float(score)
            return max(0.0, min(score_float, 1.0))
        except (ValueError, TypeError):
            return 0.0  # Default to 0 if conversion fails
        
    def _validate_reasoning_quality(self, reasoning_quality: str) -> str:
        valid_qualities = ["excellent", "good", "fair", "poor", "none"]
        return reasoning_quality if reasoning_quality in valid_qualities else "none"
    
    
    def _create_fallback_enhanced_evaluation(self, reason: str, language: str) -> EnhancedAnswerEvaluation:
        """Enhanced evaluation 최종 fallback"""
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
    







    # def _extract_suggestions(self, response_text: str, language: str = "en") -> list:
    #     """
    #     extract suggestions from LLM response text
    #     """

    #     suggestions = []
    #     lines = response_text.split('\n')

    #     suggestions_keywords = {
    #         "en": ["suggestion", "consider", "try", "think about", "perhaps"],
    #         "it": ["suggerimento", "considera", "prova", "pensa a", "forse", "magari", "potresti"]
    #     }

    #     keywords = suggestions_keywords.get(language, suggestions_keywords["en"])
    #     for line in lines:
    #         line = line.strip()
    #         if line.startswith('- ') or line.startswith('• '):
    #             suggestions.append(line[2:])
    #         elif any(keyword in line.lower() for keyword in keywords):
    #             suggestions.append(line)

    #     return suggestions[:4]  # Limit to top 4 suggestions
    
    
# #old fallback evaluation method
#     def _create_fallback_evaluation(self, student_answer: str, language: str = "en") -> AnswerEvaluation:
#         """Create fallback evaluation when all else fails"""
#         fallback_messages = {
#         "en": "I see your response. Let me help you think through this step by step.",
#         "it": "Vedo la tua risposta. Lascia che ti aiuti a ragionare passo dopo passo.",
#         "es": "Veo tu respuesta. Déjame ayudarte a pensar esto paso a paso."
#     }
    
#         feedback = fallback_messages.get(language, fallback_messages["en"])
    
#         return AnswerEvaluation(
#             evaluation="needs_guidance",
#             feedback=feedback,
#             suggestions=[]
#         )
# # old fallback parsing method
    # def _parse_evaluation_response(self,response_text: str, language:str = "en") -> AnswerEvaluation:
    #     try:    
    #         evaluation_keywords = {
    #             "en": {
    #                 "correct": ["correct", "right", "accurate", "good"],
    #                 "partial": ["partial", "somewhat", "close", "nearly"],
    #                 "incorrect": ["incorrect", "wrong", "inaccurate", "not quite"]
    #             },
    #             "it": {
    #                 "correct": ["corretto", "giusto", "accurato", "bene"],
    #                 "partial": ["parziale", "quasi", "vicino", "non del tutto"],
    #                 "incorrect": ["sbagliato", "errato", "non accurato", "non giusto"]
    #             }
    #         }
    #         keywords = evaluation_keywords.get(language, evaluation_keywords["en"])
    #         response_lower = response_text.lower()

    #         if any(keyword in response_lower for keyword in keywords["correct"]):
    #             evaluation ="correct"
    #         elif any(keyword in response_lower for keyword in keywords["partial"]):
    #             evaluation ="partially_correct"
    #         elif any(keyword in response_lower for keyword in keywords["incorrect"]):
    #             evaluation ="incorrect"
    #         else: 
    #             evaluation = "needs_guidance"
    #         return AnswerEvaluation(
    #             evaluation = evaluation,
    #             feedback= response_text,
    #             suggestions = self._extract_suggestions(response_text, language)
    #         )
        # except Exception as e:
        #     print (f"Error parsing evaluation response: {e}")
        #     return self._create_fallback_evaluation("",language)

# def _fallback_evaluation(self, student_answer: str, expert_triplet: ReasoningTriplet, language: str = "en") -> AnswerEvaluation:
#         """
#         Fallback evaluation when structured parsing fails
        
#         Args:
#             student_answer: Student's response
#             expert_triplet: Expert knowledge
            
#         Returns:
#             AnswerEvaluation: Basic evaluation
#         """
#         try:
#             # Simple keyword-based evaluation
#             student_lower = student_answer.lower()
#             expert_answer_lower = expert_triplet.answer.lower()
            
#             # Extract key terms from expert answer
#             expert_words = set(expert_answer_lower.split())
#             student_words = set(student_lower.split())
            
#             # Calculate overlap
#             common_words = expert_words.intersection(student_words)
#             overlap_ratio = len(common_words) / len(expert_words) if expert_words else 0
            
#             feedback_messages = {
#                 "en":{
#                     "correct": "Good job! You've captured the key concepts.",
#                     "partially_correct": "You're on the right track, but let's explore this further.",
#                     "incorrect": "Let's think about this differently. What else might be relevant here?"
#                 },
#                 "it": {
#                     "correct": "Ottimo lavoro! Hai catturato i concetti chiave.",
#                     "partially_correct": "Sei sulla strada giusta, ma esploriamo ulteriormente.",
#                     "incorrect": "Pensiamo a questo in modo diverso. Cosa potrebbe essere rilevante qui?"
#             }}
#             messages = feedback_messages.get(language, feedback_messages["en"])
#             # Determine evaluation based on overlap
#             if overlap_ratio > 0.6:
#                 evaluation = "correct"
#                 feedback = messages["correct"]
#             elif overlap_ratio > 0.3:
#                 evaluation = "partially_correct"
#                 feedback = messages["partially_correct"]
#             else:
#                 evaluation = "incorrect"
#                 feedback = messages["incorrect"]

#             return AnswerEvaluation(
#                 evaluation=evaluation,
#                 feedback=feedback
#             )
            
#         except Exception as e:
#             print(f"Fallback evaluation error: {e}")
#             error_messages = {
#             "en": "Unable to evaluate response properly. Let's continue with the discussion.",
#             "it": "Impossibile valutare correttamente la risposta. Continuiamo con la discussione."
#         }
#             error_msg = error_messages.get(language, error_messages["en"])
#             return AnswerEvaluation(
#                 evaluation="error",
#                 feedback=error_msg
#             )
# def classify_answer_quality(self, evaluation: AnswerEvaluation) -> str:
    #     """
    #     Classify the quality of the answer for scaffolding decisions
        
    #     Args:
    #         evaluation: The AnswerEvaluation object
            
    #     Returns:
    #         str: Quality classification ('high', 'medium', 'low', 'error')
    #     """
    #     if evaluation.evaluation == "correct":
    #         return "high"
    #     elif evaluation.evaluation == "partially_correct":
    #         return "medium"
    #     elif evaluation.evaluation == "incorrect":
    #         return "low"
    #     else:
    #         return "error"
    
# def generate_feedback_summary(self, evaluations: list) -> dict:
    #     """
    #     Generate a summary of multiple evaluations for analytics
        
    #     Args:
    #         evaluations: List of AnswerEvaluation objects
            
    #     Returns:
    #         dict: Summary statistics
    #     """
    #     if not evaluations:
    #         return {"total": 0, "correct": 0, "partial": 0, "incorrect": 0, "accuracy": 0.0}
        
    #     correct_count = sum(1 for e in evaluations if e.evaluation == "correct")
    #     partial_count = sum(1 for e in evaluations if e.evaluation == "partially_correct")
    #     incorrect_count = sum(1 for e in evaluations if e.evaluation == "incorrect")
    #     total = len(evaluations)
        
    #     accuracy = (correct_count + 0.5 * partial_count) / total if total > 0 else 0.0
        
    #     return {
    #         "total": total,
    #         "correct": correct_count,
    #         "partial": partial_count,
    #         "incorrect": incorrect_count,
    #         "accuracy": round(accuracy, 2)
    #     }
 # #backward compatibility with old AnswerEvaluation
    # # This method is used in the old answer_evaluator.py 04-08-2025
    # def evaluate_student_answer(
        
    #     self, 
    #     student_answer: str, 
    #     expert_triplet: ReasoningTriplet,
    #     tutor_last_message: str = "",
    #     conversation_context: str = "",
    #     language: str = "en"
    # ) -> AnswerEvaluation:
    #     """
    #     Stage 1b: Evaluate student's answer against expert knowledge in context
        
    #     Args:
    #         student_answer: The student's response
    #         expert_triplet: Cached expert reasoning and answer
    #         tutor_last_message: The tutor's last question/prompt
    #         conversation_context: Recent conversation history
            
    #     Returns:
    #         AnswerEvaluation: Structured evaluation with feedback
    #     """
    #     try:
    #         if not expert_triplet:
    #             return AnswerEvaluation(
    #                 evaluation="error",
    #                 feedback="No expert context available for comparison."
    #             )
    #         # Create evaluation prompt with full context
    #         prompt_template = get_answer_evaluation_prompt(language)
    #         prompt = prompt_template.format(
    #             original_question=expert_triplet.question,
    #             expert_reasoning_chain=expert_triplet.reasoning_chain,
    #             expert_answer=expert_triplet.answer,
    #             tutor_last_message=tutor_last_message,
    #             student_answer=student_answer,
    #             conversation_context=conversation_context,
    #             format_instructions=self.pydantic_parser.get_format_string()
    #         )
            
    #         # Get LLM evaluation
    #         response = self.llm.complete(prompt)
            
    #         try:
    #             evaluation = self.pydantic_parser.parse(response.text)
    #             return evaluation
    #         except Exception as parse_error:
    #             print(f"Evaluation parsing failed: {parse_error}")
    #             return self._fallback_evaluation(student_answer, expert_triplet, language)
                
    #     except Exception as e:
    #         print(f"Answer evaluation error: {e}")
    #         return AnswerEvaluation(
    #             evaluation="error",
    #             feedback=f"Error during evaluation: {str(e)}"
    #         )