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
from .prompts_template import ANSWER_EVALUATION_PROMPT


class AnswerEvaluator:
    """Handles student answer evaluation logic"""
    
    def __init__(self):
        self.llm = GoogleGenAI(
            model_name=config.GEMINI_MODEL_NAME,
            api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.3
        )
        self.pydantic_parser = PydanticOutputParser(AnswerEvaluation)
    
    def evaluate_student_answer(self, student_answer: str, expert_triplet: ReasoningTriplet) -> AnswerEvaluation:
        """
        Stage 1b: Evaluate student's answer against expert knowledge
        
        Args:
            student_answer: The student's response
            expert_triplet: Cached expert reasoning and answer
            
        Returns:
            AnswerEvaluation: Structured evaluation with feedback
        """
        try:
            if not expert_triplet:
                return AnswerEvaluation(
                    evaluation="error",
                    feedback="No expert context available for comparison."
                )
            
            # Create evaluation prompt
            prompt = ANSWER_EVALUATION_PROMPT.format(
                expert_question=expert_triplet.question,
                expert_reasoning=expert_triplet.reasoning_chain,
                expert_answer=expert_triplet.answer,
                student_answer=student_answer,
                format_instructions=self.pydantic_parser.format
            )
            
            # Get LLM evaluation
            response = self.llm.complete(prompt)
            
            try:
                evaluation = self.pydantic_parser.parse(response.text)
                return evaluation
            except Exception as parse_error:
                print(f"Evaluation parsing failed: {parse_error}")
                return self._fallback_evaluation(student_answer, expert_triplet)
                
        except Exception as e:
            print(f"Answer evaluation error: {e}")
            return AnswerEvaluation(
                evaluation="error",
                feedback=f"Error during evaluation: {str(e)}"
            )
    
    def _fallback_evaluation(self, student_answer: str, expert_triplet: ReasoningTriplet) -> AnswerEvaluation:
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
            
            # Determine evaluation based on overlap
            if overlap_ratio > 0.6:
                evaluation = "correct"
                feedback = "Good answer! You've captured the key concepts."
            elif overlap_ratio > 0.3:
                evaluation = "partially_correct"
                feedback = "You're on the right track, but let's explore this further."
            else:
                evaluation = "incorrect"
                feedback = "Let's think about this differently. What else might be relevant here?"
            
            return AnswerEvaluation(
                evaluation=evaluation,
                feedback=feedback
            )
            
        except Exception as e:
            print(f"Fallback evaluation error: {e}")
            return AnswerEvaluation(
                evaluation="error",
                feedback="Unable to evaluate response properly. Let's continue with the discussion."
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
