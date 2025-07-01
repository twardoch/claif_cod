"""Client implementation for Codex."""

from typing import AsyncIterator, Optional

from ..claif.common import Message, get_logger
from .types import CodexOptions, CodexMessage, ResultMessage
from .transport import CodexTransport


logger = get_logger(__name__)


class CodexClient:
    """Client for interacting with Codex."""
    
    def __init__(self):
        self.transport = CodexTransport()
    
    async def query(
        self,
        prompt: str,
        options: Optional[CodexOptions] = None,
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


# Module-level client instance
_client = CodexClient()


async def query(
    prompt: str,
    options: Optional[CodexOptions] = None,
) -> AsyncIterator[Message]:
    """Query Codex using the default client."""
    async for message in _client.query(prompt, options):
        yield message