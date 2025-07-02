"""Client implementation for Codex."""

from collections.abc import AsyncIterator

from claif.common import Message
from loguru import logger

from claif_cod.transport import CodexTransport
from claif_cod.types import CodexMessage, CodexOptions, ResultMessage


def _is_cli_missing_error(error: Exception) -> bool:
    """Check if error indicates missing CLI tool."""
    error_str = str(error).lower()
    error_indicators = [
        "command not found",
        "no such file or directory",
        "is not recognized as an internal or external command",
        "cannot find",
        "not found",
        "executable not found",
        "codex not found",
        "permission denied",
        "filenotfounderror",
    ]
    return any(indicator in error_str for indicator in error_indicators)


class CodexClient:
    """Client for interacting with Codex."""

    def __init__(self):
        self.transport = CodexTransport()

    async def query(
        self,
        prompt: str,
        options: CodexOptions | None = None,
    ) -> AsyncIterator[Message]:
        """Query Codex and yield messages with auto-install on missing tools."""
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

        except Exception as e:
            # Check if this is a missing CLI tool error
            if _is_cli_missing_error(e):
                logger.info("Codex CLI not found, attempting auto-install...")

                # Import and run install
                from claif_cod.install import install_codex

                install_result = install_codex()

                if install_result.get("installed"):
                    logger.info("Codex CLI installed, retrying query...")

                    # Retry the query with new transport instance
                    retry_transport = CodexTransport()
                    try:
                        await retry_transport.connect()

                        async for response in retry_transport.send_query(prompt, options):
                            if isinstance(response, CodexMessage):
                                yield response.to_claif_message()
                            elif isinstance(response, ResultMessage) and response.error:
                                logger.error(f"Codex error: {response.message}")
                                raise Exception(response.message)

                    finally:
                        await retry_transport.disconnect()

                else:
                    error_msg = install_result.get("message", "Unknown installation error")
                    logger.error(f"Auto-install failed: {error_msg}")
                    msg = f"Codex CLI not found and auto-install failed: {error_msg}"
                    raise Exception(msg) from e
            else:
                # Re-raise non-CLI-missing errors unchanged
                raise e
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
    """Query Codex using the default client with auto-install support."""
    client = _get_client()
    async for message in client.query(prompt, options):
        yield message
