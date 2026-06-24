from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal
from pydantic import computed_field, Field, PostgresDsn
from functools import lru_cache
from pydantic_core import MultiHostUrl
import os


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        env_ignore_empty=True,
        case_sensitive=True,
    )
    CORS_ORIGINS: list[str] = Field(default_factory=list)
    GEMINI_API: str
    COHERE_API_KEY: str
    REDIS_URL: str
    DOMAIN: str = "localhost"
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"
    JWT_SECRET_KEY: str
    JIRA_DOMAIN: str
    JIRA_EMAIL: str
    JIRA_API_TOKEN: str
    JIRA_PROJECT_KEY: str
    JIRA_ISSUE_TYPE: str
    BUG_REPORT_RATE_LIMIT_SECONDS: int
    ALLOW_PUBLIC_REGISTRATION: bool = True
    REGISTRATION_RATE_LIMIT_SECONDS: int = 3600
    MAX_REFRESH_SESSIONS_PER_USER: int = 5
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    PINECONE_API: str
    PINECONE_INDEX_NAME: str = "documents"
    VECTOR_STORE_PROVIDER: Literal["chroma", "pinecone"] = "pinecone"
    ADMIN_PASSWORD: str
    ADMIN_EMAIL: str

    @computed_field
    @property
    def server_host(self) -> str:
        # Use HTTPS for anything other than local development
        if self.ENVIRONMENT == "local":
            return f"http://{self.DOMAIN}"
        return f"https://{self.DOMAIN}"

    POSTGRESQL_USERNAME: str
    POSTGRESQL_PASSWORD: str
    POSTGRESQL_SERVER: str
    POSTGRESQL_PORT: int = 5432
    POSTGRESQL_DATABASE: str

    # gemini-3.1-flash-lite limits (https://ai.google.dev/gemini-api/docs/models)
    MODEL_INPUT_TOKEN_LIMIT: int = 1_048_576
    MODEL_OUTPUT_TOKEN_LIMIT: int = 65_536
    INPUT_TOKEN_BUFFER: int = 4096
    MAX_REDIS_MESSAGES: int = 100
    MIN_RECENT_TURNS: int = 4
    SUMMARIZE_THRESHOLD: float = 0.8

    CHROMA_PATH: str = "./chroma"
    CHROMA_COLLECTION_NAME: str = "documents"
    EMBEDDING_MODEL: str = "./models/onnx/baai-bge-small"
    EMBEDDING_DEVICE: str = "cpu"
    RAG_INITIAL_TOP_K: int = 20
    RAG_TOP_K: int = 5
    RAG_RELEVANCE_THRESHOLD: float = 0.4
    MAX_UPLOAD_BYTES: int = 10_485_760
    PARENT_CHUNK_SIZE_TOKENS: int = 2000
    PARENT_CHUNK_OVERLAP_TOKENS: int = 100

    @computed_field  # type: ignore[misc]
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> PostgresDsn:
        uri_string = (
            f"postgresql+asyncpg://{self.POSTGRESQL_USERNAME}:"
            f"{self.POSTGRESQL_PASSWORD}@{self.POSTGRESQL_SERVER}:"
            f"{self.POSTGRESQL_PORT}/{self.POSTGRESQL_DATABASE}"
        )
        return MultiHostUrl(uri_string)


@lru_cache()
def getSettings():
    """Return cached settings loaded from environment variables."""
    return Settings()
