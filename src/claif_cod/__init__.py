"""Claif Codex wrapper."""

from collections.abc import AsyncIterator

from claif.common import ClaifOptions, Message
from loguru import logger

from claif_cod.client import query as codex_query
from claif_cod.types import CodexOptions

__version__ = "0.1.0"


async def query(
    prompt: str,
    options: ClaifOptions | None = None,
) -> AsyncIterator[Message]:
    """Query Codex using Claif interface.

    Args:
        prompt: The prompt to send to Codex
        options: Optional Claif options

    Yields:
        Messages from Codex
    """
    if options is None:
        options = ClaifOptions()

    # Convert Claif options to Codex options
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


__all__ = ["CodexOptions", "query"]
