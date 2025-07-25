from pydantic import BaseModel, Field
from typing import Literal, Optional

# Using standard PascalCase naming and fixed typos
class ReasoningTriplet(BaseModel):
    """A data model for the question, reasoning chain, and answer triplet."""
    question: str = Field(description="The original question asked by the user.")
    reasoning_chain: str = Field(description="The step-by-step reasoning chain to arrive at the answer, based exclusively on the provided context.")
    answer: str = Field(description="The final, concise answer to the question, derived from the reasoning chain.")

class AnswerEvaluation(BaseModel):
    """Pure evaluation of student's answer quality (separated from scaffolding)"""
    evaluation: Literal[
        "correct",
        "partially_correct", 
        "incorrect", 
        "no_answer",
        "error"
    ] = Field(
        description="The evaluation category for answer quality assessment."
    )
    feedback: str = Field(
        description="Specific feedback about what the student got right or wrong."
    )
    reasoning_analysis: Optional[str] = Field(
        default=None,
        description="Analysis of which parts of the expert reasoning the student demonstrated understanding of."
    )

class ScaffoldingDecision(BaseModel):
    """Separate scaffolding strategy decision"""
    scaffold_type: Literal[
        "focus_prompt", 
        "analogy", 
        "multiple_choice",
        "direct_hint"
    ] = Field(
        description="The type of scaffolding to apply based on student's stuck level."
    )
    stuck_level: int = Field(
        description="How many times the student has been stuck (1-4+)."
    )
    reason: str = Field(
        description="Pedagogical reason for choosing this scaffolding approach."
    )
    content: str = Field(
        description="The actual scaffolding content/message to deliver."
    )