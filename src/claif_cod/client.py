"""Client implementation for Codex."""

from collections.abc import AsyncIterator

from claif.common import ClaifOptions, ClaifTimeoutError, Message, ProviderError
from loguru import logger
from tenacity import (
    AsyncRetrying,
    RetryError,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from claif_cod.transport import CodexTransport
from claif_cod.types import CodexMessage, CodexOptions, ResultMessage


def _is_cli_missing_error(error: Exception) -> bool:
    """Check if error indicates missing CLI tool."""
    # Check exception type first
    if isinstance(error, FileNotFoundError):
        return True
        
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
    ]
    return any(indicator in error_str for indicator in error_indicators)


def _convert_claif_to_codex_options(claif_options: ClaifOptions) -> CodexOptions:
    """Convert ClaifOptions to CodexOptions."""
    return CodexOptions(
        model=claif_options.model or "o4-mini",
        temperature=claif_options.temperature,
        max_tokens=claif_options.max_tokens,
        timeout=claif_options.timeout,
        verbose=claif_options.verbose,
    )


class CodexClient:
    """Client for interacting with Codex."""

    def __init__(self):
        self.transport = CodexTransport()

    async def query(
        self,
        prompt: str,
        options: CodexOptions | ClaifOptions | None = None,
    ) -> AsyncIterator[Message]:
        """Query Codex with retry logic and auto-install on missing tools."""
        # Handle options conversion
        if options is None:
            codex_options = CodexOptions()
            retry_count = 3  # Default retry count
            retry_delay = 1.0  # Default retry delay
        elif isinstance(options, ClaifOptions):
            # Convert ClaifOptions to CodexOptions
            codex_options = _convert_claif_to_codex_options(options)
            retry_count = options.retry_count
            retry_delay = options.retry_delay
        else:
            codex_options = options
            retry_count = 3  # Default retry count
            retry_delay = 1.0  # Default retry delay

        logger.debug(f"Querying Codex with prompt: {prompt[:100]}...")
        logger.debug(f"Using model: {codex_options.model}")

        # Define retry exceptions
        retry_exceptions = (
            ProviderError,
            ClaifTimeoutError,
            ConnectionError,
            TimeoutError,
            Exception,  # For general transport errors
        )

        # Check if this is a CLI missing error first (before retry logic)
        try:
            # Test connection first
            test_transport = CodexTransport()
            await test_transport.connect()
            await test_transport.disconnect()
        except Exception as e:
            if _is_cli_missing_error(e):
                logger.info("Codex CLI not found, attempting auto-install...")

                # Import and run install
                from claif_cod.install import install_codex

                install_result = install_codex()

                if not install_result.get("installed"):
                    error_msg = install_result.get("message", "Unknown installation error")
                    logger.error(f"Auto-install failed: {error_msg}")
                    msg = f"Codex CLI not found and auto-install failed: {error_msg}"
                    msg = "codex"
                    raise ProviderError(msg, msg) from e

                logger.info("Codex CLI installed successfully")

        # Now proceed with retry logic
        if retry_count <= 0:
            logger.debug("Codex provider: Retry disabled, single attempt")
            async for message in self._query_impl(prompt, codex_options):
                yield message
            return

        attempt = 0
        last_error: Exception | None = None

        try:
            async for attempt in AsyncRetrying(
                stop=stop_after_attempt(retry_count),
                wait=wait_exponential(
                    multiplier=retry_delay,
                    min=retry_delay,
                    max=retry_delay * 10,
                ),
                retry=retry_if_exception_type(retry_exceptions),
                reraise=True,
            ):
                with attempt:
                    try:
                        logger.debug(f"Codex provider: Attempt {attempt.retry_state.attempt_number}/{retry_count}")

                        messages_yielded = False
                        async for message in self._query_impl(prompt, codex_options):
                            messages_yielded = True
                            yield message

                        if not messages_yielded:
                            msg = "codex"
                            raise ProviderError(
                                msg,
                                "No response received from Codex",
                            )

                        return

                    except retry_exceptions as e:
                        last_error = e
                        logger.warning(f"Codex provider: Attempt {attempt.retry_state.attempt_number} failed: {e}")
                        if attempt.retry_state.attempt_number >= retry_count:
                            raise
                        raise

        except RetryError as e:
            if last_error:
                raise last_error
            msg = "codex"
            raise ProviderError(
                msg,
                f"All {retry_count} retry attempts failed",
                {"retry_error": str(e)},
            )

    async def _query_impl(
        self,
        prompt: str,
        options: CodexOptions,
    ) -> AsyncIterator[Message]:
        """Implementation of the actual query logic."""
        try:
            await self.transport.connect()

            async for response in self.transport.send_query(prompt, options):
                if isinstance(response, CodexMessage):
                    yield response.to_claif_message()
                elif isinstance(response, ResultMessage) and response.error:
                    logger.error(f"Codex error: {response.message}")
                    msg = "codex"
                    raise ProviderError(msg, response.message)

        except Exception as e:
            # Convert transport errors to ProviderError
            if not isinstance(e, ProviderError):
                msg = "codex"
                raise ProviderError(msg, str(e)) from e
            raise
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
    options: CodexOptions | ClaifOptions | None = None,
) -> AsyncIterator[Message]:
    """Query Codex using the default client with retry logic and auto-install support."""
    client = _get_client()
    async for message in client.query(prompt, options):
        yield message
