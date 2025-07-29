# this_file: claif_cod/src/claif_cod/__init__.py
"""Claif provider for OpenAI Codex with OpenAI Responses API compatibility."""

from claif_cod._version import __version__
from claif_cod.client import CodexClient

__all__ = ["CodexClient", "__version__"]
