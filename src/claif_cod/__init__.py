"""CLAIF Codex wrapper."""

from typing import AsyncIterator, Optional

from ..claif.common import Message, ClaifOptions, get_logger
from .client import query as codex_query
from .types import CodexOptions


__version__ = "0.1.0"

logger = get_logger(__name__)


async def query(
    prompt: str,
    options: Optional[ClaifOptions] = None,
) -> AsyncIterator[Message]:
    """Query Codex using CLAIF interface.
    
    Args:
        prompt: The prompt to send to Codex
        options: Optional CLAIF options
        
    Yields:
        Messages from Codex
    """
    if options is None:
        options = ClaifOptions()
    
    # Convert CLAIF options to Codex options
    codex_options = CodexOptions(
        model=options.model or "o4-mini",
        temperature=options.temperature,
        max_tokens=options.max_tokens,
        timeout=options.timeout,
        verbose=options.verbose,
    )
    
    logger.debug(f"Querying Codex with prompt: {prompt[:100]}...")
    
    # Pass through to Codex client
    async for message in codex_query(prompt, codex_options):
        yield message


__all__ = ["query", "CodexOptions"]