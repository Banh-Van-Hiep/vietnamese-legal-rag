"""Team 2 RAG module: Week 2 mock entry point."""
import os
os.environ.setdefault("HF_HOME", "D:\\hf_cache")
os.environ.setdefault("TORCH_HOME", "D:\\hf_cache\\torch")

from .service import query

__all__ = ["query"]
