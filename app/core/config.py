from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./sql_app.db"
    SECRET_KEY: str = "supersecretkey"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # API keys
    OPENAI_API_KEY: str | None = None
    DEEPSEEK_API_KEY: str | None = None
    TAVILY_API_KEY: str | None = None

    # Model configuration
    MODEL_PROVIDER: str = "openai"
    MODEL_REASONER: str = "gpt-4o"
    MODEL_FAST: str = "gpt-4o-mini"

    # Langsmith
    LANGSMITH_TRACING: bool = False
    LANGSMITH_ENDPOINT: str = "https://api.smith.langchain.com"
    LANGSMITH_API_KEY: str | None = None
    LANGSMITH_PROJECT: str = "grifo"

    # Chroma
    CHROMA_PERSIST_DIRECTORY: str = "./data/chroma"

    # Text Processing
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 100

    # Agent
    REFLEXION_MAX_ITERATIONS: int = 2

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
