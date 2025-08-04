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

    def decide_scaffolding(self, stuck_count: int, triplet: ReasoningTriplet, language: str = "en") -> ScaffoldingDecision:
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
                return self._generate_focused_scaffolding(triplet, stuck_count, language)
            elif stuck_count <= 2:
                return self._generate_analogy_scaffolding(triplet, stuck_count, language)
            elif stuck_count <= 3:
                return self._generate_multiple_choice_scaffolding(triplet, stuck_count, language)
            else:
                return self._generate_direct_hint_scaffolding(triplet, stuck_count, language)

        except Exception as e:
            print(f"Scaffolding error: {e}")
            return self._create_error_scaffolding(stuck_count, language)

    def _generate_focused_scaffolding(self, triplet: ReasoningTriplet, stuck_level: int, language: str = "en") -> ScaffoldingDecision:
        """Level 1: Generate a focused hint that guides to the next logical step"""
        reason_messages = {
        "en": "Student needs focused guidance on next logical step",
        "it": "Lo studente ha bisogno di una guida focalizzata sul prossimo passo logico"
    }
        return ScaffoldingDecision(
            scaffold_type="focus_prompt",
            stuck_level=stuck_level,
            reason=reason_messages.get(language, reason_messages["en"]),
            content=""  # LLM will generate this based on scaffold_type
        )

    def _generate_analogy_scaffolding(self, triplet: ReasoningTriplet, stuck_level: int, language: str = "en") -> ScaffoldingDecision:
        """Level 2: Generate an analogical hint using familiar concepts"""
        reason_messages = {
            "en": "Student needs conceptual bridge through familiar analogy",
            "it": "Lo studente ha bisogno di un ponte concettuale attraverso un'analogia familiare"
        }
        return ScaffoldingDecision(
            scaffold_type="analogy",
            stuck_level=stuck_level,
            reason=reason_messages.get(language, reason_messages["en"]),
            content=""  # LLM will generate this based on scaffold_type
        )

    def _generate_multiple_choice_scaffolding(self, triplet: ReasoningTriplet, stuck_level: int, language: str = "en") -> ScaffoldingDecision:
        """Level 3: Generate a multiple choice question to guide thinking"""
        reason_messages = {
            "en": "Student needs structured choice-based guidance",
            "it": "Lo studente ha bisogno di una guida strutturata basata sulle scelte"
        }
        return ScaffoldingDecision(
            scaffold_type="multiple_choice",
            stuck_level=stuck_level,
            reason=reason_messages.get(language, reason_messages["en"]),
            content=""  # LLM will generate this based on scaffold_type
        )

    def _generate_direct_hint_scaffolding(self, triplet: ReasoningTriplet, stuck_level: int, language: str = "en") -> ScaffoldingDecision:
        """Level 4: Provide more direct explanation while still being educational"""
        reason_messages = {
            "en": "Student needs more substantial guidance after multiple attempts",
            "it": "Lo studente ha bisogno di una guida più sostanziale dopo più tentativi"
        }
        return ScaffoldingDecision(
            scaffold_type="direct_hint",
            stuck_level=stuck_level,
            reason=reason_messages.get(language, reason_messages["en"]),
            content=""  # LLM will generate this based on scaffold_type
        )
    def _create_error_scaffolding(self, stuck_count: int, language: str = "en") -> ScaffoldingDecision:
        """Create error scaffolding when something goes wrong"""
        error_reasons = {
            "en": "Error occurred, providing generic help",
            "it": "Si è verificato un errore, fornendo aiuto generico"
        }

        return ScaffoldingDecision(
        scaffold_type="focus_prompt",
        stuck_level=stuck_count,
        reason=error_reasons.get(language, error_reasons["en"]),
        content=""  # LLM will generate fallback content
    )
    # Generic fallback methods
    def _generic_focused_scaffolding(self, stuck_level: int, language: str = "en") -> ScaffoldingDecision:
        reason_messages = {
            "en": "Generic focused help needed",
            "it": "Aiuto focalizzato generico necessario"
        }
        return ScaffoldingDecision(
            scaffold_type="focus_prompt",
            stuck_level=stuck_level,
            reason=reason_messages.get(language, reason_messages["en"]),
            content=""  # LLM will generate this
        )

    def _generic_analogy_scaffolding(self, stuck_level: int, language: str = "en") -> ScaffoldingDecision:
        reason_messages = {
            "en": "Generic analogy help needed",
            "it": "Aiuto per analogia generico necessario"
        }
        return ScaffoldingDecision(
            scaffold_type="analogy",
            stuck_level=stuck_level,
            reason=reason_messages.get(language, reason_messages["en"]),
            content=""  # LLM will generate this
        )

    def _generic_multiple_choice_scaffolding(self, stuck_level: int, language: str = "en") -> ScaffoldingDecision:
        reason_messages = {
            "en": "Generic structured choice help needed",
            "it": "Aiuto strutturato per scelta generico necessario"
        }
        return ScaffoldingDecision(
            scaffold_type="multiple_choice",
            stuck_level=stuck_level,
            reason=reason_messages.get(language, reason_messages["en"]),
            content=""  # LLM will generate this
        )

    def _generic_direct_hint_scaffolding(self, stuck_level: int, language: str = "en") -> ScaffoldingDecision:
        reason_messages = {
            "en": "Generic direct help needed",
            "it": "Aiuto diretto generico necessario"
        }
        return ScaffoldingDecision(
            scaffold_type="direct_hint",
            stuck_level=stuck_level,
            reason=reason_messages.get(language, reason_messages["en"]),
            content=""  # LLM will generate this
        )
