"""Configuration settings for Spatial-RAG API."""

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_host: str = "localhost"
    database_port: int = 5432
    database_name: str = "spatial_rag"
    database_user: str = "postgres"
    database_password: str = "postgres"

    # HuggingFace
    huggingface_token: str = ""

    # Embedding model
    embedding_model: str = "google/embeddinggemma-300m"
    embedding_dimension: int = 768

    # Retrieval settings
    retrieval_top_k: int = 10
    hybrid_alpha: float = 0.7  # Semantic weight
    hybrid_beta: float = 0.3  # Spatial weight
    default_radius_m: float = 1000.0  # Default search radius in meters

    # LLM settings (optional)
    openai_api_key: str = ""
    llm_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.0

    @property
    def database_url(self) -> str:
        """Construct PostgreSQL connection URL."""
        return f"postgresql://{self.database_user}:{self.database_password}@{self.database_host}:{self.database_port}/{self.database_name}"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
