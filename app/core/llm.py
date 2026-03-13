from langchain_openai import ChatOpenAI
from app.core.config import settings


def _get_llm(model_name: str, temperature: float = 0.2):
    """Factory base para instanciar o LLM configurado."""
    if settings.MODEL_PROVIDER == "deepseek":
        return ChatOpenAI(
            model=model_name,
            api_key=settings.DEEPSEEK_API_KEY,
            base_url="https://api.deepseek.com/v1",
            temperature=temperature,
        )
    # Default para OpenAI
    return ChatOpenAI(
        model=model_name, api_key=settings.OPENAI_API_KEY, temperature=temperature
    )


def get_reasoner():
    """
    Retorna o modelo de alto raciocínio (REASONER).
    Ideal para críticas, reflexão e síntese complexa.
    """
    return _get_llm(settings.MODEL_REASONER, temperature=0.1)


def get_fast_model():
    """
    Retorna o modelo ágil e de baixo custo (FAST).
    Ideal para roteamento, classificação simples e rascunhos iniciais.
    """
    return _get_llm(settings.MODEL_FAST, temperature=0.2)
