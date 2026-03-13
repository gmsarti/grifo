from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Gestão de configurações usando Pydantic Settings.
    Lê automaticamente do ficheiro .env na raiz do projeto.
    """

    OPENAI_API_KEY: str = ""
    DEEPSEEK_API_KEY: str = ""

    MODEL_PROVIDER: str = "openai"  # "openai" ou "deepseek"
    MODEL_REASONER: str = "gpt-4o"
    MODEL_FAST: str = "gpt-4o-mini"

    CHROMA_PERSIST_DIRECTORY: str = "./data/chroma"
    TAVILY_API_KEY: str = ""

    REFLEXION_MAX_ITERATIONS: int = 2
    LANGSMITH_API_KEY: str = ""

    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = int(CHUNK_SIZE * 0.2)

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
