"""FastAPI package for Team 2 RAG API."""
from .app import create_app
from .handlers import install_error_handlers

__all__ = ["create_app", "install_error_handlers"]