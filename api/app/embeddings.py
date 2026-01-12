"""Embedding model using OpenAI API."""

from functools import lru_cache

from openai import OpenAI

from .config import get_settings


class EmbeddingModel:
    """
    Embedding model using OpenAI API.

    Default: text-embedding-3-small
    - 768 dimensions (configurable, max 1536)
    - Fast and cost-effective
    """

    def __init__(self, model_name: str = None):
        settings = get_settings()
        self.model_name = model_name or settings.embedding_model
        self.dimension = settings.embedding_dimension
        self._client = None

    @property
    def client(self) -> OpenAI:
        """Lazy load the OpenAI client."""
        if self._client is None:
            settings = get_settings()
            self._client = OpenAI(api_key=settings.openai_api_key)
            print(f"OpenAI client initialized. Model: {self.model_name}, Dimension: {self.dimension}")
        return self._client

    def embed_text(self, text: str) -> list[float]:
        """Generate embedding for a single text string."""
        response = self.client.embeddings.create(
            model=self.model_name,
            input=text,
            dimensions=self.dimension,
        )
        return response.data[0].embedding

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts in a batch."""
        response = self.client.embeddings.create(
            model=self.model_name,
            input=texts,
            dimensions=self.dimension,
        )
        return [item.embedding for item in response.data]

    def embed_query(self, query: str) -> list[float]:
        """Generate embedding for a search query."""
        return self.embed_text(query)

    def embed_document(self, document: str) -> list[float]:
        """Generate embedding for a document to be indexed."""
        return self.embed_text(document)

    def embed_documents(self, documents: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple documents."""
        return self.embed_texts(documents)


@lru_cache(maxsize=1)
def get_embedding_model() -> EmbeddingModel:
    """Get cached embedding model instance (singleton)."""
    return EmbeddingModel()


def embed_query(query: str) -> list[float]:
    """Convenience function to embed a query."""
    return get_embedding_model().embed_query(query)


def embed_document(document: str) -> list[float]:
    """Convenience function to embed a document."""
    return get_embedding_model().embed_document(document)


def embed_documents(documents: list[str]) -> list[list[float]]:
    """Convenience function to embed multiple documents."""
    return get_embedding_model().embed_documents(documents)
