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
    search_queries: list[str] = Field(
        description="1-3 search queries for researching improvements to address the critique of your current answer"
    )


class ReviseAnswer(AnswerQuestion):
    """Revise the original answer to the question based on new information and critique."""

    references: list[str] = Field(
        description="References to the sources used to answer the question"
    )


class ExtractedFact(BaseModel):
    fact: str = Field(
        description=(
            "Fato que o usuário declarou ou afirmou diretamente na conversa. "
            "Deve ser conciso, autossuficiente e ancorado em algo que o usuário disse explicitamente. "
            "Exemplos válidos: 'Usuário mencionou que usa Python como linguagem favorita', "
            "'Usuário disse que trabalha com Go no emprego', "
            "'Usuário afirmou ter um projeto de IA chamado Grifo'. "
            "NÃO escreva suposições como 'Usuário pode estar interessado em X' ou 'Possivelmente usa Y'."
        )
    )
    topic: str = Field(
        description="Tópico geral do fato (ex: 'Preferência do Usuário', 'Interesse de Pesquisa', 'Contexto de Trabalho', 'Tecnologia/Ferramenta', 'Nível Técnico', 'Detalhes do Projeto')."
    )


class KnowledgeExtraction(BaseModel):
    """Extração de fatos e conhecimentos úteis da conversa para armazenamento de longo prazo."""

    facts: list[ExtractedFact] = Field(
        default_factory=list,
        description="Lista de fatos extraídos. Retorne uma lista vazia se não houver nada útil ou novo para lembrar.",
    )
