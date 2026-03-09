from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Gestão de configurações usando Pydantic Settings.
    Lê automaticamente do ficheiro .env na raiz do projeto.
    """

    OPENAI_API_KEY: str = ""
    DEEPSEEK_API_KEY: str = ""

    MODEL_PROVIDER: str = "openai"  # "openai" ou "deepseek"
    MODEL_NAME: str = "gpt-4o"

    CHROMA_PERSIST_DIRECTORY: str = "./data/chroma"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
