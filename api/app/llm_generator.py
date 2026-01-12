"""LLM Generator for Spatial-RAG answer synthesis."""

import json
from typing import AsyncGenerator, Optional

from .config import get_settings


class LLMGenerator:
    """
    Generate answers using LLM with retrieved spatial context.

    Supports streaming responses for real-time UI updates.
    """

    SYSTEM_PROMPT = """You are a geospatial reasoning assistant. Your task is to answer questions 
using ONLY the provided spatial documents as context.

Rules:
1. Only use information from the provided documents
2. Reference document locations when relevant to the answer
3. If documents don't contain enough information, say so explicitly
4. Consider spatial relationships between documents when reasoning
5. Cite document numbers when referencing specific information

Format your response clearly and concisely."""

    def __init__(self):
        self.settings = get_settings()
        self._client = None

    @property
    def client(self):
        """Lazy-load OpenAI client."""
        if self._client is None:
            if not self.settings.openai_api_key:
                raise ValueError(
                    "OPENAI_API_KEY not set. LLM synthesis requires an API key."
                )
            from openai import OpenAI

            # Initialize client with explicit parameters only
            self._client = OpenAI(
                api_key=self.settings.openai_api_key,
                timeout=60.0,
            )
        return self._client

    def _build_messages(
        self, query: str, context_text: str, documents: list[dict]
    ) -> list[dict]:
        """Build chat messages for the LLM."""
        # Include structured context
        context_json = json.dumps(
            [
                {"id": d["id"], "title": d["title"], "geometry": d.get("geometry")}
                for d in documents
            ],
            indent=2,
        )

        user_message = f"""Question: {query}

Retrieved Documents Context:
{context_text}

Document Metadata (JSON):
{context_json}

Please answer the question based on the above spatial context."""

        return [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ]

    def generate(self, query: str, context_text: str, documents: list[dict]) -> str:
        """
        Generate a non-streaming answer.

        Args:
            query: User's question
            context_text: Formatted context from retrieved documents
            documents: List of document dicts with metadata

        Returns:
            Generated answer string
        """
        messages = self._build_messages(query, context_text, documents)

        response = self.client.chat.completions.create(
            model=self.settings.llm_model,
            messages=messages,
            # temperature=self.settings.llm_temperature,
        )

        return response.choices[0].message.content

    async def generate_stream(
        self, query: str, context_text: str, documents: list[dict]
    ) -> AsyncGenerator[str, None]:
        """
        Generate a streaming answer.

        Yields chunks of the response as they're generated.
        """
        messages = self._build_messages(query, context_text, documents)

        response = self.client.chat.completions.create(
            model=self.settings.llm_model,
            messages=messages,
            # temperature=self.settings.llm_temperature,
            stream=True,
        )

        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


class MockLLMGenerator:
    """
    Mock LLM generator for testing without API key.

    Returns a formatted summary of retrieved documents.
    """

    def generate(self, query: str, context_text: str, documents: list[dict]) -> str:
        """Generate a mock answer summarizing retrieved documents."""
        if not documents:
            return "No relevant documents found for your query."

        doc_summaries = []
        for i, doc in enumerate(documents[:5], 1):
            title = doc.get("title", "Untitled")
            scores = doc.get("scores", {})
            semantic = scores.get("semantic", 0)
            spatial = scores.get("spatial", 0)
            hybrid = scores.get("hybrid", 0)

            doc_summaries.append(f"{i}. **{title}** (relevance: {hybrid:.2f})")

        return f"""Based on your query "{query}", I found {len(documents)} relevant spatial documents:

{chr(10).join(doc_summaries)}

*Note: This is a mock response. Configure OPENAI_API_KEY for full LLM synthesis.*"""

    async def generate_stream(
        self, query: str, context_text: str, documents: list[dict]
    ) -> AsyncGenerator[str, None]:
        """Generate mock streaming response."""
        response = self.generate(query, context_text, documents)
        # Simulate streaming by yielding word by word
        for word in response.split():
            yield word + " "


def get_llm_generator() -> LLMGenerator | MockLLMGenerator:
    """Get appropriate LLM generator based on API key availability."""
    settings = get_settings()
    if settings.openai_api_key:
        return LLMGenerator()
    return MockLLMGenerator()
