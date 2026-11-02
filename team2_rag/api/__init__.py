"""Team 2 RAG API package."""
import os
os.environ.setdefault("HF_HOME", "D:\\hf_cache")
os.environ.setdefault("TORCH_HOME", "D:\\hf_cache\\torch")

from .app import create_app

__all__ = ["create_app"]
