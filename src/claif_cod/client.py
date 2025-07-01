"""Client implementation for Codex."""

from collections.abc import AsyncIterator

from claif.common import Message
from loguru import logger

from claif_cod.transport import CodexTransport
from claif_cod.types import CodexMessage, CodexOptions, ResultMessage


class CodexClient:
    """Client for interacting with Codex."""

    def __init__(self):
        self.transport = CodexTransport()

    async def query(
        self,
        prompt: str,
        options: CodexOptions | None = None,
    ) -> AsyncIterator[Message]:
        """Query Codex and yield messages."""
        if options is None:
            options = CodexOptions()

        logger.debug(f"Querying Codex with prompt: {prompt[:100]}...")
        logger.debug(f"Using model: {options.model}")

        try:
            await self.transport.connect()

            async for response in self.transport.send_query(prompt, options):
                if isinstance(response, CodexMessage):
                    yield response.to_claif_message()
                elif isinstance(response, ResultMessage) and response.error:
                    logger.error(f"Codex error: {response.message}")
                    raise Exception(response.message)

        finally:
            await self.transport.disconnect()


# Module-level client instance (lazy-loaded)
_client = None


def _get_client() -> CodexClient:
    """Get or create the client instance."""
    global _client
    if _client is None:
        _client = CodexClient()
    return _client


async def query(
    prompt: str,
    options: CodexOptions | None = None,
) -> AsyncIterator[Message]:
    """Query Codex using the default client."""
    client = _get_client()
    async for message in client.query(prompt, options):
        yield message
