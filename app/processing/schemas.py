from typing import List
from pydantic import BaseModel, Field


class Reflection(BaseModel):
    missing: str = Field(description="Critique of what is missing from the answer")
    superfluous: str = Field(
        description="Critique of what is superfluous or unnecessary in the answer"
    )


class AnswerQuestion(BaseModel):
    """Answer the question with reflection and search recommendations."""

    answer: str = Field(description="Detailed answer to the question (~250 words)")
    reflection: Reflection = Field(description="Your reflection on the current answer")
    search_queries: List[str] = Field(
        description="1-3 search queries for researching improvements to address the critique of your current answer"
    )


class ReviseAnswer(AnswerQuestion):
    """Revise the original answer to the question based on new information and critique."""

    references: List[str] = Field(
        description="References to the sources used to answer the question"
    )
