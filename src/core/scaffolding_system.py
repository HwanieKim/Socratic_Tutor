#!/usr/bin/env python3
"""
Scaffolding System Module

Handles progressive scaffolding support:
- Level 1: Focused hints
- Level 2: Analogical hints  
- Level 3: Multiple choice assessment
- Level 4: Direct explanations
"""

import os
import random
from llama_index.llms.google_genai import GoogleGenAI

from . import config
from .models import AnswerEvaluation, ReasoningTriplet


class ScaffoldingSystem:
    """Handles progressive scaffolding support for struggling students"""
    
    def __init__(self):
        self.llm = GoogleGenAI(
            model_name=config.GEMINI_MODEL_NAME,
            api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.4
        )
    
    def provide_scaffolded_help(self, stuck_count: int, triplet: ReasoningTriplet) -> AnswerEvaluation:
        """
        Provide scaffolded help based on how many times student has been stuck
        
        Args:
            stuck_count: Number of times student has asked for help
            triplet: Expert reasoning triplet for context
            
        Returns:
            AnswerEvaluation: Scaffolded help response
        """
        try:
            if stuck_count <= 1:
                return self.generate_focused_hint(triplet)
            elif stuck_count <= 2:
                return self.generate_analogy_hint(triplet)
            elif stuck_count <= 3:
                return self.generate_multiple_choice_assessment(triplet)
            else:
                return self.generate_direct_explanation(triplet)
                
        except Exception as e:
            print(f"Scaffolding error: {e}")
            return AnswerEvaluation(
                evaluation="error",
                feedback="I'm here to help you work through this. Let's start with what you already know about this topic."
            )
    
    def generate_focused_hint(self, triplet: ReasoningTriplet) -> AnswerEvaluation:
        """
        Level 1: Generate a focused hint that guides to the next logical step
        
        Args:
            triplet: Expert reasoning for context
            
        Returns:
            AnswerEvaluation: Focused hint response
        """
        try:
            if not triplet:
                return self._generic_focused_hint()
            
            prompt = f"""
            Based on this expert reasoning: {triplet.reasoning_chain}
            And this answer: {triplet.answer}
            
            Provide a focused hint that guides the student to the next logical step in their thinking.
            The hint should:
            - Not give away the answer directly
            - Point to the most important concept or step to consider next
            - Be encouraging and supportive
            - Ask a guiding question if appropriate
            
            Keep it concise (1-2 sentences).
            """
            
            response = self.llm.complete(prompt)
            
            return AnswerEvaluation(
                evaluation="scaffold_focus_prompt",
                feedback=response.text.strip()
            )
            
        except Exception as e:
            print(f"Focused hint generation error: {e}")
            return self._generic_focused_hint()
    
    def generate_analogy_hint(self, triplet: ReasoningTriplet) -> AnswerEvaluation:
        """
        Level 2: Generate an analogical hint using familiar concepts
        
        Args:
            triplet: Expert reasoning for context
            
        Returns:
            AnswerEvaluation: Analogical hint response
        """
        try:
            if not triplet:
                return self._generic_analogy_hint()
            
            prompt = f"""
            Based on this expert reasoning: {triplet.reasoning_chain}
            And this answer: {triplet.answer}
            
            Create a helpful analogy that connects this concept to something more familiar or everyday.
            The analogy should:
            - Make the concept easier to understand
            - Use familiar situations or objects
            - Help bridge understanding without giving the direct answer
            - Be encouraging and relatable
            
            Format: "Think of it like..." or "Imagine if..." followed by your analogy.
            Keep it to 2-3 sentences.
            """
            
            response = self.llm.complete(prompt)
            
            return AnswerEvaluation(
                evaluation="scaffold_analogy",
                feedback=response.text.strip()
            )
            
        except Exception as e:
            print(f"Analogy hint generation error: {e}")
            return self._generic_analogy_hint()
    
    def generate_multiple_choice_assessment(self, triplet: ReasoningTriplet) -> AnswerEvaluation:
        """
        Level 3: Generate a multiple choice question to guide thinking
        
        Args:
            triplet: Expert reasoning for context
            
        Returns:
            AnswerEvaluation: Multiple choice assessment
        """
        try:
            if not triplet:
                return self._generic_multiple_choice()
            
            prompt = f"""
            Based on this expert reasoning: {triplet.reasoning_chain}
            And this answer: {triplet.answer}
            
            Create a multiple choice question that helps guide the student's thinking.
            The question should:
            - Focus on a key concept or step in the reasoning
            - Have 4 options (A, B, C, D)
            - Include one clearly correct answer
            - Have plausible but incorrect distractors
            - Help the student think through the logic
            
            Format:
            Question: [Your question]
            A) [Option A]
            B) [Option B] 
            C) [Option C]
            D) [Option D]
            
            What do you think is the best answer?
            """
            
            response = self.llm.complete(prompt)
            
            return AnswerEvaluation(
                evaluation="scaffold_multiple_choice",
                feedback=response.text.strip()
            )
            
        except Exception as e:
            print(f"Multiple choice generation error: {e}")
            return self._generic_multiple_choice()
    
    def generate_direct_explanation(self, triplet: ReasoningTriplet) -> AnswerEvaluation:
        """
        Level 4: Provide direct explanation when other scaffolding hasn't worked
        
        Args:
            triplet: Expert reasoning for context
            
        Returns:
            AnswerEvaluation: Direct explanation
        """
        try:
            if not triplet:
                return self._generic_direct_explanation()
            
            prompt = f"""
            Based on this expert reasoning: {triplet.reasoning_chain}
            And this answer: {triplet.answer}
            
            Provide a clear, direct explanation of the concept.
            The explanation should:
            - Break down the key ideas step by step
            - Use clear, simple language
            - Be encouraging and supportive
            - Help the student understand for future similar questions
            - End with a question to check understanding
            
            Keep it educational and supportive in tone.
            """
            
            response = self.llm.complete(prompt)
            
            return AnswerEvaluation(
                evaluation="correct",  # Mark as correct since we're providing the answer
                feedback=response.text.strip()
            )
            
        except Exception as e:
            print(f"Direct explanation generation error: {e}")
            return self._generic_direct_explanation()
    
    def _generic_focused_hint(self) -> AnswerEvaluation:
        """Generic focused hint when no triplet available"""
        hints = [
            "Let's think about this step by step. What's the first thing that comes to mind when you consider this topic?",
            "Good question! Let's break this down. What do you think might be the most important factor here?",
            "That's worth exploring. What aspects of this topic have you encountered before?",
            "Let's approach this systematically. What do you think we should consider first?"
        ]
        
        return AnswerEvaluation(
            evaluation="scaffold_focus_prompt",
            feedback=random.choice(hints)
        )
    
    def _generic_analogy_hint(self) -> AnswerEvaluation:
        """Generic analogy hint when no triplet available"""
        analogies = [
            "Think of it like building a house - you need a strong foundation before you can add the walls. What might be the foundation concept here?",
            "Imagine you're explaining this to a friend who's never heard of it before. What simple comparison would you use?",
            "This concept is like a recipe - there are key ingredients that need to come together. What do you think the main ingredients might be?",
            "Think of this like solving a puzzle - each piece has its place. What piece do you think we should look for first?"
        ]
        
        return AnswerEvaluation(
            evaluation="scaffold_analogy",
            feedback=random.choice(analogies)
        )
    
    def _generic_multiple_choice(self) -> AnswerEvaluation:
        """Generic multiple choice when no triplet available"""
        question = """
        Let's approach this systematically. Which of these strategies would be most helpful for understanding this topic?

        A) Look for key definitions and terminology
        B) Focus on practical applications and examples  
        C) Understand the underlying principles first
        D) All of the above - use a comprehensive approach

        What do you think would work best for you?
        """
        
        return AnswerEvaluation(
            evaluation="scaffold_multiple_choice",
            feedback=question.strip()
        )
    
    def _generic_direct_explanation(self) -> AnswerEvaluation:
        """Generic direct explanation when no triplet available"""
        explanation = """
        I can see you're working hard on this! Let me help break it down:

        When approaching complex topics like this, it's helpful to:
        1. Start with what you already know
        2. Identify the key concepts or components
        3. Look for connections and relationships
        4. Consider practical applications or examples

        This systematic approach often makes challenging material more manageable. 
        What part of this process feels most challenging to you right now?
        """
        
        return AnswerEvaluation(
            evaluation="correct",
            feedback=explanation.strip()
        )
    
    def get_scaffolding_level_name(self, stuck_count: int) -> str:
        """Get the name of the current scaffolding level"""
        if stuck_count <= 1:
            return "Focused Hint"
        elif stuck_count <= 2:
            return "Analogical Support"
        elif stuck_count <= 3:
            return "Guided Assessment"
        else:
            return "Direct Explanation"
