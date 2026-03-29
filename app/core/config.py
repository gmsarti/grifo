from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_INSECURE_KEYS = {"supersecretkey", "", "changeme", "secret", "your-secret-key"}


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/sql_app.db"
    SECRET_KEY: str
    ALGORITHM: str = "HS256"

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        if v.lower() in _INSECURE_KEYS:
            raise ValueError(
                "SECRET_KEY insegura. Defina um valor forte no .env "
                "(ex: openssl rand -hex 32)."
            )
        return v

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
    CHUNK_OVERLAP: int = 200

    # Agent Memory
    REFLEXION_MAX_ITERATIONS: int = 2
    MEMORY_DB_PATH: str = "./data/grifo_memory.db"

    # Rate limiting
    RATE_LIMIT_CHAT: str = "20/minute"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
