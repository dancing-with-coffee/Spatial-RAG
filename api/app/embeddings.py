"""Local BGE embeddings using sentence-transformers."""

from functools import lru_cache
from typing import Union

import numpy as np
from sentence_transformers import SentenceTransformer

from .config import get_settings


class EmbeddingModel:
    """
    Local embedding model using BGE (BAAI General Embedding).

    Uses BAAI/bge-small-en-v1.5 by default:
    - 384 dimensions
    - ~33M parameters
    - Fast inference on CPU
    """

    def __init__(self, model_name: str = None):
        settings = get_settings()
        self.model_name = model_name or settings.embedding_model
        self.dimension = settings.embedding_dimension
        self._model = None

    @property
    def model(self) -> SentenceTransformer:
        """Lazy load the model on first use."""
        if self._model is None:
            print(f"Loading embedding model: {self.model_name}")
            self._model = SentenceTransformer(self.model_name)
            print(
                f"Model loaded. Dimension: {self._model.get_sentence_embedding_dimension()}"
            )
        return self._model

    def embed_text(self, text: str) -> list[float]:
        """
        Generate embedding for a single text string.

        For BGE models, prepending "query: " or "passage: " can improve results.
        We use bare text here for simplicity.
        """
        embedding = self.model.encode(text, normalize_embeddings=True)
        return embedding.tolist()

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for multiple texts in a batch.

        More efficient than calling embed_text repeatedly.
        """
        embeddings = self.model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()

    def embed_query(self, query: str) -> list[float]:
        """
        Generate embedding for a search query.

        BGE models recommend prefixing queries with "query: " for retrieval.
        """
        prefixed = f"query: {query}"
        return self.embed_text(prefixed)

    def embed_document(self, document: str) -> list[float]:
        """
        Generate embedding for a document to be indexed.

        BGE models recommend prefixing documents with "passage: " for retrieval.
        """
        prefixed = f"passage: {document}"
        return self.embed_text(prefixed)

    def embed_documents(self, documents: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple documents."""
        prefixed = [f"passage: {doc}" for doc in documents]
        return self.embed_texts(prefixed)


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
