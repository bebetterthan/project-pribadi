"""
Core components for AI Pentest Agent

This package contains architectural components that prevent
the '\n description' Gemini API bug through explicit context management.
"""
from app.core.context_serializer import ContextSerializer

__all__ = ['ContextSerializer']

