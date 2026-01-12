"""Embedding model using sentence-transformers with HuggingFace authentication."""

from functools import lru_cache

import numpy as np
from huggingface_hub import login
from sentence_transformers import SentenceTransformer

from .config import get_settings


class EmbeddingModel:
    """
    Embedding model supporting multiple backends.

    Default: google/embeddinggemma-300m
    - 768 dimensions
    - ~300M parameters
    - Requires HuggingFace authentication
    - Native encode_query/encode_document support
    """

    def __init__(self, model_name: str = None):
        settings = get_settings()
        self.model_name = model_name or settings.embedding_model
        self.dimension = settings.embedding_dimension
        self._model = None
        self._hf_token = settings.huggingface_token

    def _authenticate_hf(self):
        """Authenticate with HuggingFace if token is provided."""
        if self._hf_token:
            login(token=self._hf_token)
            print("HuggingFace authentication successful")

    @property
    def model(self) -> SentenceTransformer:
        """Lazy load the model on first use."""
        if self._model is None:
            self._authenticate_hf()
            print(f"Loading embedding model: {self.model_name}")
            self._model = SentenceTransformer(
                self.model_name,
                trust_remote_code=True,
            )
            print(
                f"Model loaded. Dimension: {self._model.get_sentence_embedding_dimension()}"
            )
        return self._model

    def _is_gemma_model(self) -> bool:
        """Check if the model is a Gemma embedding model."""
        return "gemma" in self.model_name.lower()

    def embed_text(self, text: str) -> list[float]:
        """Generate embedding for a single text string."""
        embedding = self.model.encode(text, normalize_embeddings=True)
        return embedding.tolist()

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts in a batch."""
        embeddings = self.model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()

    def embed_query(self, query: str) -> list[float]:
        """
        Generate embedding for a search query.

        For Gemma models: uses native encode_query method
        For BGE models: prefixes with "query: "
        """
        if self._is_gemma_model():
            embedding = self.model.encode_query(query)
            return embedding.tolist()
        else:
            prefixed = f"query: {query}"
            return self.embed_text(prefixed)

    def embed_document(self, document: str) -> list[float]:
        """
        Generate embedding for a document to be indexed.

        For Gemma models: uses native encode_document method
        For BGE models: prefixes with "passage: "
        """
        if self._is_gemma_model():
            embedding = self.model.encode_document(document)
            return embedding.tolist()
        else:
            prefixed = f"passage: {document}"
            return self.embed_text(prefixed)

    def embed_documents(self, documents: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple documents."""
        if self._is_gemma_model():
            embeddings = self.model.encode_document(documents)
            return embeddings.tolist()
        else:
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
