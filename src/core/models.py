from pydantic import BaseModel, Field
from typing import Literal

# Using standard PascalCase naming and fixed typos
class ReasoningTriplet(BaseModel):
    """A data model for the question, reasoning chain, and answer triplet."""
    question: str = Field(description="The original question asked by the user.")
    reasoning_chain: str = Field(description="The step-by-step reasoning chain to arrive at the answer, based exclusively on the provided context.")
    answer: str = Field(description="The final, concise answer to the question, derived from the reasoning chain.")

class AnswerEvaluation(BaseModel):
    """A data model for evaluating a student's response during tutoring."""
    evaluation: Literal["new_question", "meta_question", "correct", "partially_correct", "incorrect", "error"] = Field(
        description="The evaluation category: 'new_question', 'meta_question', 'correct', 'partially_correct', 'incorrect', or 'error'."
    )
    feedback: str = Field(
        description="A brief message: hint, error notice, or feedback based on the evaluation."
    )