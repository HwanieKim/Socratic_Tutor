from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Literal, Optional, Dict
from enum import Enum

# reasoning triplet 
class ReasoningTriplet(BaseModel):
    """A data model for the question, reasoning chain, and answer triplet."""
    question: str = Field(description="The original question asked by the user.")
    reasoning_chain: str = Field(description="The step-by-step reasoning chain to arrive at the answer, based exclusively on the provided context.")
    answer: str = Field(description="The final, concise answer to the question, derived from the reasoning chain.")


# Evaluation Models
class MultidimensionalScores(BaseModel):
    conceptual_accuracy: float = Field(
        ge=0.0, le=1.0, 
        description="How well the student's answer uses the key concept correctly (30% weight)"
    )
    reasoning_coherence: float = Field(
        ge=0.0, le=1.0,
        description = "How logically the student's reasoning process develops (25% weight)"
    )
    use_of_evidence_and_rules: float = Field(
        ge=0.0, le=1.0,
        description="How well the student's answer uses evidence and rules from the context (15% weight)"
    )
    conceptual_integration: float = Field(
        ge=0.0, le=1.0,
        description = "How much the student's answer integrates multiple concepts, links them together, and applies them in a coherent manner (20% weight)"
    )
    clarity_of_expression: float = Field(
        ge=0.0, le=1.0,
        description="How clearly the student explains their reasoning and answer (10% weight)"
    )
    @property
    def weighted_overall_score(self) -> float:
        """Calculate the average of all scores (weighted)"""
        return (
            self.conceptual_accuracy * 0.30 +
            self.reasoning_coherence * 0.25 +
            self.use_of_evidence_and_rules * 0.15 +
            self.conceptual_integration * 0.20 +
            self.clarity_of_expression * 0.10
        )
    
    @property
    def multidimensional_average(self) -> float:
        """Calculate the average of all scores without weights"""
        return (
            self.conceptual_accuracy +
            self.reasoning_coherence +
            self.use_of_evidence_and_rules +
            self.conceptual_integration +
            self.clarity_of_expression
        ) / 5
    def get_weighted_breakdown(self) -> Dict[str, float]:
        """가중치 적용된 세부 점수 분석"""
        return {
            "conceptual_accuracy_weighted": self.conceptual_accuracy * 0.30,
            "reasoning_coherence_weighted": self.reasoning_coherence * 0.25,
            "evidence_utilization_weighted": self.use_of_evidence_and_rules * 0.15,
            "conceptual_integration_weighted": self.conceptual_integration * 0.20,
            "expression_clarity_weighted": self.clarity_of_expression * 0.10,
            "total_weighted_score": self.weighted_overall_score
        }

# - Multidimensional evaluation scores for student's answer
class EnhancedAnswerEvaluation(BaseModel):
    """Pure evaluation of student's answer quality (separated from scaffolding)"""
    binary_evaluation: Literal[
        "correct",
        "partially_correct", 
        "incorrect_but_related",
        "incorrect",
        "unclear",
        "error"
    ] 
    #60%
    multidimensional_scores: MultidimensionalScores 
    reasoning_quality : Literal[ "excellent", "good", "fair", "poor","none" ] 

    misconceptions: List[str]= Field(default= [], description="List of specific misconceptions or errors in the student's reasoning.")
    strengths: List[str] = Field(default=[], description="List of specific strengths in the student's reasoning or answer.")
    feedback: str = Field(
        description="Specific evaluative feedback about what the student got right or wrong."
    )
    reasoning_analysis: Optional[str] = Field(
        default=None,
        description="Analysis of which parts of the expert reasoning the student demonstrated understanding of."
    )
    @property
    def binary_score(self) -> float:
        binary_mapping ={
            "correct":1.0,
            "partially_correct":0.7,
            "incorrect_but_related":0.4,
            "incorrect":0.1,
            "unclear":0.0,
            "error":0.0
        }
        return binary_mapping.get(self.binary_evaluation, 0.0)
    
    @property
    def overall_score(self) -> float:
        return self.multidimensional_scores.weighted_overall_score
    
    def get_detailed_breakdown(self)-> Dict[str, float]:
        """
        Get a detailed breakdown of the evaluation scores.
        
        Returns:
            Dict[str, float]: Dictionary with score categories and their values.
        """
        return {
            "binary_score": self.binary_score,
            "multidimensional_average": self.multidimensional_scores.multidimensional_average,
            "overall_score": self.overall_score,
            "dimensional_breakdown": {
                "conceptual_accuracy": self.multidimensional_scores.conceptual_accuracy,
                "reasoning_coherence": self.multidimensional_scores.reasoning_coherence,
                "use_of_evidence_and_rules": self.multidimensional_scores.use_of_evidence_and_rules,
                "conceptual_integration": self.multidimensional_scores.conceptual_integration,
                "clarity_of_expression": self.multidimensional_scores.clarity_of_expression
            }
        }

# Level model
class LearningLevel (str, Enum):
    """ 
    5 level of learning state
    It states the student's current learning level.
    """
    L0_PRE_CONCEPTUAL = "L0_pre_conceptual"
    L1_FAMILIARIZATION = "L1_familiarization"
    L2_STRUCTURED_COMPREHENSION = "L2_structured_comprehension"
    L3_PROCEDURAL_FLUENCY = "L3_procedural_fluency"
    L4_CONCEPTUAL_TRANSFER = "L4_conceptual_transfer"

class LevelAdjustment(BaseModel):
    previous_level: LearningLevel
    new_level: LearningLevel
    reason: str = Field(
        description = "Reason for the level adjustment based on student's performance."
    )
    evaluation_score: float = Field(
        description= "overall evaluation score that influenced the level change."
    )
    timestamp: datetime = Field(
        default_factory=datetime.now
        )

class SessionLearningProfile(BaseModel):

    current_level: LearningLevel  = Field( default=LearningLevel.L2_STRUCTURED_COMPREHENSION)

    recent_scores_history: List[float] = Field (
        default_factory=list,
        description = "List of recent evaluation overall scores, up to five scores."
    )

    level_adjustments_history: List[LevelAdjustment] = Field(
        default_factory=list,
        description = "History of level adjustments made during the session."
    )

    # statistics
    total_interactions: int = Field(default=0)
    session_start_time: datetime = Field(default_factory=datetime.now)

    # New fields for improved level management
    consecutive_high_performance: int = Field(default=0, description="Count of consecutive good performances")
    consecutive_low_performance: int = Field(default=0, description="Count of consecutive poor performances")
    level_stability_count: int = Field(default=0, description="How many evaluations at current level")

    def add_evaluation_score(self,evaluation:EnhancedAnswerEvaluation) -> None:
        score = evaluation.overall_score
        self.recent_scores_history.append(score)
        self.total_interactions += 1 

        if len(self.recent_scores_history) > 5:
            self.recent_scores_history.pop(0)

        self._update_performance_counters(score)
        self.level_stability_count += 1
        self.update_level(evaluation)

    def _update_performance_counters(self, score: float) -> None:
        HIGH_THRESHOLD = 0.75
        LOW_THRESHOLD = 0.45

        if score >= HIGH_THRESHOLD:
            self.consecutive_high_performance += 1
            self.consecutive_low_performance = 0
        elif score <= LOW_THRESHOLD:
            self.consecutive_low_performance += 1
            self.consecutive_high_performance = 0
        else:
            pass

    def should_level_up(self) -> bool:
        if self.current_level == LearningLevel.L4_CONCEPTUAL_TRANSFER:
            return False
        
        if self.level_stability_count < 3:
            return False
        
        if len(self.recent_scores_history) >= 3:
            recent_avg = sum(self.recent_scores_history[-3:]) / 3
            return (
                self.consecutive_high_performance >= 3 or  # 3 consecutive high scores
                (recent_avg >= 0.8 and self.consecutive_high_performance >= 2) or  # Very high average + 2 good
                (recent_avg >= 0.85 and len(self.recent_scores_history) >= 5)  # Excellent sustained performance
            )
        return False
    
    def should_level_down(self) -> bool:
        if self.current_level == LearningLevel.L0_PRE_CONCEPTUAL:
            return False
        
        if self.level_stability_count < 4:
            return False
        
        if len(self.recent_scores_history) >= 4:
            recent_avg = sum(self.recent_scores_history[-4:]) / 4
            return (
                self.consecutive_low_performance >= 3 or  # 3 consecutive low scores
                (recent_avg <= 0.3 and self.consecutive_low_performance >= 4)  # Very low average + 4 bad
               
            )
        return False

    def update_level(self, last_evaluation:EnhancedAnswerEvaluation) -> Optional[LevelAdjustment]:
        """
        Intelligently update learning level based on performance patterns
        
        Args:
            last_evaluation: Most recent evaluation
            
        Returns:
            Optional[LevelAdjustment]: Level change details if level changed
        """


        previous_level = self.current_level
        adjustment = None

        if self.should_level_up():
            new_level = self._get_next_level_up()
            if new_level:
                reason = self._get_level_up_reason()
                adjustment = LevelAdjustment(
                    previous_level=previous_level,
                    new_level=new_level,
                    reason=reason,
                    evaluation_score=last_evaluation.overall_score
                )
                self.current_level = new_level
                self._reset_level_tracking()
        elif self.should_level_down():
            new_level = self._get_next_level_down()
            if new_level:
                reason = self._get_level_down_reason()
                adjustment = LevelAdjustment(
                    previous_level=previous_level,
                    new_level=new_level,
                    reason=reason,
                    evaluation_score=last_evaluation.overall_score
                )
                self.current_level = new_level
                self._reset_level_tracking()

        if adjustment:
            self.level_adjustments_history.append(adjustment)
            print(f"[DEBUG] Level adjustment: {adjustment}")
        
        return adjustment

    def _get_next_level_up(self) -> Optional[LearningLevel]:
        """Get the next level up from current level"""
        level_progression = [
            LearningLevel.L0_PRE_CONCEPTUAL,
            LearningLevel.L1_FAMILIARIZATION,
            LearningLevel.L2_STRUCTURED_COMPREHENSION,
            LearningLevel.L3_PROCEDURAL_FLUENCY,
            LearningLevel.L4_CONCEPTUAL_TRANSFER
        ]
        
        current_index = level_progression.index(self.current_level)
        if current_index < len(level_progression) - 1:
            return level_progression[current_index + 1]
        return None
    
    def _get_next_level_down(self) -> Optional[LearningLevel]:
        """Get the next level down from current level"""
        level_progression = [
            LearningLevel.L0_PRE_CONCEPTUAL,
            LearningLevel.L1_FAMILIARIZATION,
            LearningLevel.L2_STRUCTURED_COMPREHENSION,
            LearningLevel.L3_PROCEDURAL_FLUENCY,
            LearningLevel.L4_CONCEPTUAL_TRANSFER
        ]
        
        current_index = level_progression.index(self.current_level)
        if current_index > 0:
            return level_progression[current_index - 1]
        return None
    
    def _get_level_up_reason(self) -> str:
        """Get reason for level up based on performance pattern"""
        if self.consecutive_high_performance >= 3:
            return f"Consistent excellence: {self.consecutive_high_performance} consecutive high scores"
        
        recent_avg = sum(self.recent_scores_history[-3:]) / min(3, len(self.recent_scores_history))
        if recent_avg >= 0.85:
            return f"Outstanding recent performance (avg: {recent_avg:.2f})"
        
        return f"Strong sustained performance (avg: {recent_avg:.2f})"
    
    def _get_level_down_reason(self) -> str:
        """Get reason for level down based on performance pattern"""
        if self.consecutive_low_performance >= 4:
            return f"Needs additional support: {self.consecutive_low_performance} consecutive low scores"
        
        recent_avg = sum(self.recent_scores_history[-4:]) / min(4, len(self.recent_scores_history))
        return f"Requires foundational reinforcement (recent avg: {recent_avg:.2f})"
    
    def _reset_level_tracking(self) -> None:
        """Reset tracking counters after level change"""
        self.consecutive_high_performance = 0
        self.consecutive_low_performance = 0
        self.level_stability_count = 0
    
    def get_level_description(self) -> str:
        """Get description of current learning level"""
        descriptions = {
            LearningLevel.L0_PRE_CONCEPTUAL: "Building basic familiarity with concepts",
            LearningLevel.L1_FAMILIARIZATION: "Developing initial understanding",
            LearningLevel.L2_STRUCTURED_COMPREHENSION: "Organizing knowledge systematically",
            LearningLevel.L3_PROCEDURAL_FLUENCY: "Applying knowledge confidently",
            LearningLevel.L4_CONCEPTUAL_TRANSFER: "Mastering advanced applications"
        }
        return descriptions.get(self.current_level, "Developing understanding")
    def get_performance_insights(self) -> Dict:
        """Get comprehensive performance insights for the session"""
        try:
            insights = {
                "current_level": self.current_level.value,
                "level_description": self.get_level_description(),
                "total_interactions": self.total_interactions,
                "level_adjustments_count": len(self.level_adjustments_history),
                "session_duration_minutes": self._calculate_session_duration(),
            }
            
            # Performance metrics
            if self.recent_scores_history:
                insights.update({
                    "recent_performance": {
                        "average_score": round(sum(self.recent_scores_history) / len(self.recent_scores_history), 2),
                        "latest_score": round(self.recent_scores_history[-1], 2),
                        "score_trend": self._calculate_trend(),
                        "scores_count": len(self.recent_scores_history)
                    },
                    "performance_streaks": {
                        "consecutive_high": self.consecutive_high_performance,
                        "consecutive_low": self.consecutive_low_performance,
                        "stability_at_level": self.level_stability_count
                    }
                })
            else:
                insights["recent_performance"] = None
                insights["performance_streaks"] = {
                    "consecutive_high": 0,
                    "consecutive_low": 0,
                    "stability_at_level": self.level_stability_count
                }
            
            # Level progression insights
            if self.level_adjustments_history:
                latest_adjustment = self.level_adjustments_history[-1]
                insights["level_progression"] = {
                    "last_change": {
                        "from": latest_adjustment.previous_level.value,
                        "to": latest_adjustment.new_level.value,
                        "reason": latest_adjustment.reason,
                        "score": round(latest_adjustment.evaluation_score, 2)
                    },
                    "total_changes": len(self.level_adjustments_history)
                }
            else:
                insights["level_progression"] = None
                
            return insights
            
        except Exception as e:
            return {"error": f"Could not generate insights: {str(e)}"}  
           
    def _calculate_session_duration(self) -> float:
        """Calculate session duration in minutes"""
        try:
            duration = (datetime.now() - self.session_start_time).total_seconds() / 60
            return round(duration, 1)
        except:
            return 0.0
    
    def _calculate_trend(self) -> str:
        """Calculate performance trend from recent scores"""
        if len(self.recent_scores_history) < 2:
            return "insufficient_data"
        
        recent_half = self.recent_scores_history[len(self.recent_scores_history)//2:]
        earlier_half = self.recent_scores_history[:len(self.recent_scores_history)//2]
        
        if not earlier_half:
            return "insufficient_data"
        
        recent_avg = sum(recent_half) / len(recent_half)
        earlier_avg = sum(earlier_half) / len(earlier_half)
        
        diff = recent_avg - earlier_avg
        
        if diff > 0.1:
            return "improving"
        elif diff < -0.1:
            return "declining"
        else:
            return "stable"
class ScaffoldingDecision(BaseModel):

    """Separate scaffolding strategy decision"""
    scaffold_strategy: str = Field(
        description=(
            "The type of scaffolding strategy to be executed. One of 20 possible values, such as:\n"
            "- L0: 'focusing_prompt', 'simple_analogy', 'multiple_choice_simple', 'direct_explanation'\n"
            "- L1: 'rephrase_question', 'conceptual_hint', 'source_citation_hint', 'provide_sentence_starter'\n"
            "- L2: 'ask_for_evidence', 'break_down_problem', 'contrasting_case', 'provide_key_term'\n"
            "- L3: 'socratic_hint', 'challenge_assumption', 'ask_for_generalization', 'point_to_contradiction'\n"
            "- L4: 'metacognitive_prompt', 'introduce_new_constraint', 'ask_for_new_analogy', 'philosophical_probe'"
        )
    )
    stuck_count: int = Field(
        description="How many times the student has been stuck (1-4+)."
    )

    reason: str = Field(
        description="Pedagogical reason for choosing this scaffolding approach."
    )

    content: Optional[Dict] = Field(
        default=None,
        description="Optional content to provide as part of the scaffolding (e.g., hint text, example)."
    )

    