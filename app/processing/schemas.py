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

class ExtractedFact(BaseModel):
    fact: str = Field(
        description="Fato claro, conciso e autossuficiente extraído da conversa (ex: 'O usuário prefere respostas curtas')."
    )
    topic: str = Field(
        description="Tópico geral do fato (ex: 'Preferência do Usuário', 'Detalhes do Projeto', 'Tecnologias')."
    )


class KnowledgeExtraction(BaseModel):
    """Extração de fatos e conhecimentos úteis da conversa para armazenamento de longo prazo."""
    
    facts: List[ExtractedFact] = Field(
        default_factory=list, 
        description="Lista de fatos extraídos. Retorne uma lista vazia se não houver nada útil ou novo para lembrar."
    )
