#!/usr/bin/env python3
"""
Scaffolding System Module (Refactored for Separation of Concerns)

Handles progressive scaffolding support:
- Level 1: Focused hints
- Level 2: Analogical hints  
- Level 3: Multiple choice assessment
- Level 4: Direct explanations

Returns ScaffoldingDecision with strategy type - LLM generates content based on type
"""

from .models import ScaffoldingDecision, ReasoningTriplet


class ScaffoldingSystem:
    """Handles progressive scaffolding support for struggling students"""
    
    def __init__(self):
        # No LLM needed - just decision logic
        pass
    
    def decide_scaffolding(self, stuck_count: int, triplet: ReasoningTriplet) -> ScaffoldingDecision:
        """
        Decide scaffolding strategy based on how many times student has been stuck
        
        Args:
            stuck_count: Number of times student has asked for help
            triplet: Expert reasoning triplet for context
            
        Returns:
            ScaffoldingDecision: Strategy and content for scaffolding
        """
        try:
            if stuck_count <= 1:
                return self._generate_focused_scaffolding(triplet, stuck_count)
            elif stuck_count <= 2:
                return self._generate_analogy_scaffolding(triplet, stuck_count)
            elif stuck_count <= 3:
                return self._generate_multiple_choice_scaffolding(triplet, stuck_count)
            else:
                return self._generate_direct_hint_scaffolding(triplet, stuck_count)
                
        except Exception as e:
            print(f"Scaffolding error: {e}")
            return ScaffoldingDecision(
                scaffold_type="focus_prompt",
                stuck_level=stuck_count,
                reason="Error occurred, providing generic help",
                content=""  # LLM will generate fallback content
            )
    
    def _generate_focused_scaffolding(self, triplet: ReasoningTriplet, stuck_level: int) -> ScaffoldingDecision:
        """Level 1: Generate a focused hint that guides to the next logical step"""
        return ScaffoldingDecision(
            scaffold_type="focus_prompt",
            stuck_level=stuck_level,
            reason="Student needs focused guidance on next logical step",
            content=""  # LLM will generate this based on scaffold_type
        )
    
    def _generate_analogy_scaffolding(self, triplet: ReasoningTriplet, stuck_level: int) -> ScaffoldingDecision:
        """Level 2: Generate an analogical hint using familiar concepts"""
        return ScaffoldingDecision(
            scaffold_type="analogy",
            stuck_level=stuck_level,
            reason="Student needs conceptual bridge through familiar analogy",
            content=""  # LLM will generate this based on scaffold_type
        )
    
    def _generate_multiple_choice_scaffolding(self, triplet: ReasoningTriplet, stuck_level: int) -> ScaffoldingDecision:
        """Level 3: Generate a multiple choice question to guide thinking"""
        return ScaffoldingDecision(
            scaffold_type="multiple_choice",
            stuck_level=stuck_level,
            reason="Student needs structured choice-based guidance",
            content=""  # LLM will generate this based on scaffold_type
        )
    
    def _generate_direct_hint_scaffolding(self, triplet: ReasoningTriplet, stuck_level: int) -> ScaffoldingDecision:
        """Level 4: Provide more direct explanation while still being educational"""
        return ScaffoldingDecision(
            scaffold_type="direct_hint",
            stuck_level=stuck_level,
            reason="Student needs more substantial guidance after multiple attempts",
            content=""  # LLM will generate this based on scaffold_type
        )
    
    # Generic fallback methods
    def _generic_focused_scaffolding(self, stuck_level: int) -> ScaffoldingDecision:
        return ScaffoldingDecision(
            scaffold_type="focus_prompt",
            stuck_level=stuck_level,
            reason="Generic focused help",
            content=""  # LLM will generate this
        )
    
    def _generic_analogy_scaffolding(self, stuck_level: int) -> ScaffoldingDecision:
        return ScaffoldingDecision(
            scaffold_type="analogy",
            stuck_level=stuck_level,
            reason="Generic analogy help",
            content=""  # LLM will generate this
        )
    
    def _generic_multiple_choice_scaffolding(self, stuck_level: int) -> ScaffoldingDecision:
        return ScaffoldingDecision(
            scaffold_type="multiple_choice",
            stuck_level=stuck_level,
            reason="Generic structured choice help",
            content=""  # LLM will generate this
        )
    
    def _generic_direct_hint_scaffolding(self, stuck_level: int) -> ScaffoldingDecision:
        return ScaffoldingDecision(
            scaffold_type="direct_hint",
            stuck_level=stuck_level,
            reason="Generic direct help",
            content=""  # LLM will generate this
        )
