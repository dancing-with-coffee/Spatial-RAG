"""Database connection and utilities for Spatial-RAG."""

import json
from contextlib import contextmanager
from typing import Any, Generator

import psycopg2
from psycopg2.extras import RealDictCursor

from .config import get_settings


class DatabaseConnection:
    """Manages PostgreSQL connections with PostGIS and pgvector support."""

    def __init__(self):
        self.settings = get_settings()

    @contextmanager
    def get_connection(self) -> Generator[psycopg2.extensions.connection, None, None]:
        """Get a database connection with automatic cleanup."""
        conn = psycopg2.connect(
            host=self.settings.database_host,
            port=self.settings.database_port,
            database=self.settings.database_name,
            user=self.settings.database_user,
            password=self.settings.database_password,
        )
        try:
            yield conn
        finally:
            conn.close()

    @contextmanager
    def get_cursor(
        self, dict_cursor: bool = True
    ) -> Generator[psycopg2.extensions.cursor, None, None]:
        """Get a database cursor with automatic commit/rollback."""
        with self.get_connection() as conn:
            cursor_factory = RealDictCursor if dict_cursor else None
            cursor = conn.cursor(cursor_factory=cursor_factory)
            try:
                yield cursor
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                cursor.close()

    def execute_query(self, sql: str, params: tuple = None) -> list[dict[str, Any]]:
        """Execute a SELECT query and return results as list of dicts."""
        with self.get_cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchall()

    def execute_insert(self, sql: str, params: tuple = None) -> None:
        """Execute an INSERT/UPDATE/DELETE query."""
        with self.get_cursor() as cursor:
            cursor.execute(sql, params)

    def execute_many(self, sql: str, params_list: list[tuple]) -> None:
        """Execute a query with multiple parameter sets."""
        with self.get_cursor() as cursor:
            cursor.executemany(sql, params_list)


# Singleton instance
db = DatabaseConnection()


def format_embedding_for_pg(embedding: list[float]) -> str:
    """Format embedding list as PostgreSQL vector string."""
    return f"[{','.join(map(str, embedding))}]"


def format_metadata_for_pg(metadata: dict) -> str:
    """Format metadata dict as PostgreSQL JSONB string."""
    return json.dumps(metadata)
