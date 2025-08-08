from .models import LearningLevel, ReasoningTriplet, ScaffoldingDecision

class ScaffoldingSystem:
    """
    A system for managing scaffolding in the learning environment.
    """
    def __init__(self):
        self.strategies_by_level = {
            LearningLevel.L0_PRE_CONCEPTUAL: [
                "focusing_prompt",
                "simple_analogy",
                "multiple_choice_simple",
                "direct_explanation"
            ],
            LearningLevel.L1_FAMILIARIZATION: [
                "rephrase_question",
                "conceptual_hint",
                "source_citation_hint",
                "provide_sentence_starter"
            ],
            LearningLevel.L2_STRUCTURED_COMPREHENSION: [
                "ask_for_evidence",
                "break_down_problem",
                "contrasting_case",
                "provide_key_term"
            ],
            LearningLevel.L3_PROCEDURAL_FLUENCY: [
                "socratic_hint",
                "challenge_assumption",
                "ask_for_generalization",
                "point_to_contradiction"
            ],
            LearningLevel.L4_CONCEPTUAL_TRANSFER: [
                "metacognitive_prompt",
                "introduce_new_constraint",
                "ask_for_new_analogy",
                "philosophical_probe"
            ]
        }
    def decide_scaffolding_strategy(
            self,
            learning_level: LearningLevel,
            stuck_count: int,
            triplet: ReasoningTriplet
    ) -> ScaffoldingDecision:
        if stuck_count <1: 
            stuck_count = 1

        strategies = self.strategies_by_level.get(learning_level, self.strategies_by_level[LearningLevel.L2_STRUCTURED_COMPREHENSION])
        strategy_index = min(stuck_count -1, len(strategies)-1)
        chosen_strategy = strategies[strategy_index]
        
        reason = f"Student at Level {learning_level.value} is stuck for the {stuck_count} time. Applying strategy : {chosen_strategy}."

 # TODO: 'multiple_choice_simple'과 같은 특정 전략은 
        # triplet을 사용하여 동적으로 content를 생성하는 로직을 추가할 수 있습니다.
        # 예: content = self._create_mcq(triplet)

        print (f"DEBUG: scaffolding decision - {reason}")
        return ScaffoldingDecision(
            scaffold_strategy=chosen_strategy,
            stuck_count=stuck_count,
            reason=reason,
            content=None  # TODO: 실제 content 생성 로직 추가 예정
        )
