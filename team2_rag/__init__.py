"""Team 2 RAG module: `query` là mock cho Team 3; `generate_answer` là luồng LLM thật (VLRA-29)."""

from .service import generate_answer, query, to_error_response

__all__ = ["generate_answer", "query", "to_error_response"]
