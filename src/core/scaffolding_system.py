from .models import LearningLevel, ReasoningTriplet, ScaffoldingDecision

class ScaffoldingSystem:
    """
    A system for managing scaffolding in the learning environment.
    """
    def __init__(self):
        self.strategies_by_level = {
            LearningLevel.L0_PRE_CONCEPTUAL: [
                {"name": "focusing_prompt", "description": "Asks the student to focus on a single, critical concept or word."},
                {"name": "simple_analogy", "description": "Provides a simple, everyday comparison to make a concept concrete."},
                {"name": "multiple_choice_simple", "description": "Offers a clear choice between 2-3 options to guide thinking."},
                {"name": "direct_explanation", "description": "Gives a straightforward, simple definition or explanation."}
            ],
            LearningLevel.L1_FAMILIARIZATION: [
                {"name": "rephrase_question", "description": "Asks the same question in a simpler or different way."},
                {"name": "conceptual_hint", "description": "Gives a small clue about the core concept without the full answer."},
                {"name": "provide_sentence_starter", "description": "Offers the beginning of a sentence to help structure thoughts."},
                {"name": "source_citation_hint", "description": "Points to a specific location in the source material."}
            ],
            LearningLevel.L2_STRUCTURED_COMPREHENSION: [
                {"name": "break_down_problem", "description": "Breaks a complex question into smaller, manageable sub-questions."},
                {"name": "provide_key_term", "description": "Introduces a critical keyword the student might be missing."},
                {"name": "contrasting_case", "description": "Presents a contrasting example to clarify a concept's boundaries."},
                {"name": "ask_for_evidence", "description": "Prompts the student to find direct textual support for their reasoning."}
            ],
            LearningLevel.L3_PROCEDURAL_FLUENCY: [
                {"name": "socratic_hint", "description": "Asks a leading question to guide the student to question their own answer."},
                {"name": "challenge_assumption", "description": "Prompts the student to examine an unstated assumption."},
                {"name": "ask_for_generalization", "description": "Asks if the principle can be applied to other contexts."},
                {"name": "point_to_contradiction", "description": "Highlights a potential inconsistency in the student's statements."}
            ],
            LearningLevel.L4_CONCEPTUAL_TRANSFER: [
                {"name": "metacognitive_prompt", "description": "Asks the student to reflect on their own thought process."},
                {"name": "introduce_new_constraint", "description": "Adds a new condition to the problem to test understanding."},
                {"name": "ask_for_new_analogy", "description": "Challenges the student to create their own analogy for the concept."},
                {"name": "philosophical_probe", "description": "Poses a broader, abstract, or ethical question."}
            ]
        }
    def decide_scaffolding_strategy(
            self,
            learning_level: LearningLevel,
            stuck_count: int,
            triplet: ReasoningTriplet
    ) -> ScaffoldingDecision:
        """
        Decides the appropriate scaffolding strategy based on student's learning level and performance.
        
        Args:
            learning_level: Current learning level of the student (L0-L4)
            stuck_count: Number of times student has been stuck on this question
            triplet: The question-reasoning-answer triplet for context
            
        Returns:
            ScaffoldingDecision: Contains strategy name, description, reason, and content
        """
        if stuck_count <1: 
            stuck_count = 1

        strategies = self.strategies_by_level.get(learning_level, self.strategies_by_level[LearningLevel.L2_STRUCTURED_COMPREHENSION])
        strategy_index = min(stuck_count -1, len(strategies)-1)
        chosen_strategy = strategies[strategy_index]
        strategy_name = chosen_strategy["name"]
        strategy_description = chosen_strategy["description"]
        reason = f"Student at Level {learning_level.value} is stuck for the {stuck_count} time. Applying strategy : {chosen_strategy}."

 # TODO: 'multiple_choice_simple'과 같은 특정 전략은 
        # triplet을 사용하여 동적으로 content를 생성하는 로직을 추가할 수 있습니다.
        # 예: content = self._create_mcq(triplet)

        print (f"DEBUG: scaffolding decision - {reason}")
        return ScaffoldingDecision(
            scaffold_strategy=strategy_name,
            strategy_description=strategy_description,
            stuck_count=stuck_count,
            reason=reason,
            content=None  # TODO: 실제 content 생성 로직 추가 예정
        )
