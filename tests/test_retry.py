"""Test retry functionality for claif_cod."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from claif.common import ClaifOptions, Message, MessageRole, ProviderError

from claif_cod.client import CodexClient, query
from claif_cod.types import CodexMessage, CodexOptions, TextBlock


@pytest.mark.asyncio
async def test_retry_on_provider_error():
    """Test that retry logic works on ProviderError."""
    client = CodexClient()

    # Mock transport to fail twice then succeed
    call_count = 0

    async def mock_send_query(prompt, options):
        nonlocal call_count
        call_count += 1

        if call_count < 3:
            msg = "codex"
            raise ProviderError(msg, f"Mock error attempt {call_count}")

        # Success on third attempt
        yield CodexMessage(role="assistant", content=[TextBlock(text="Success after retries")])

    with patch.object(client.transport, "send_query", side_effect=mock_send_query):
        with patch.object(client.transport, "connect", new_callable=AsyncMock):
            with patch.object(client.transport, "disconnect", new_callable=AsyncMock):
                messages = []
                options = ClaifOptions(retry_count=3, retry_delay=0.1)

                async for message in client.query("test prompt", options):
                    messages.append(message)

                assert len(messages) == 1
                assert messages[0].content == "Success after retries"
                assert call_count == 3


@pytest.mark.asyncio
async def test_retry_exhausted():
    """Test that all retries are exhausted properly."""
    client = CodexClient()

    # Mock transport to always fail
    async def mock_send_query(prompt, options):
        msg = "codex"
        raise ProviderError(msg, "Persistent error")

    with patch.object(client.transport, "send_query", side_effect=mock_send_query):
        with patch.object(client.transport, "connect", new_callable=AsyncMock):
            with patch.object(client.transport, "disconnect", new_callable=AsyncMock):
                options = ClaifOptions(retry_count=2, retry_delay=0.1)

                with pytest.raises(ProviderError) as exc_info:
                    async for _message in client.query("test prompt", options):
                        pass

                assert "Persistent error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_no_retry_when_disabled():
    """Test that retry is skipped when retry_count is 0."""
    client = CodexClient()

    call_count = 0

    async def mock_send_query(prompt, options):
        nonlocal call_count
        call_count += 1
        msg = "codex"
        raise ProviderError(msg, "Error without retry")

    with patch.object(client.transport, "send_query", side_effect=mock_send_query):
        with patch.object(client.transport, "connect", new_callable=AsyncMock):
            with patch.object(client.transport, "disconnect", new_callable=AsyncMock):
                options = ClaifOptions(retry_count=0)

                with pytest.raises(ProviderError):
                    async for _message in client.query("test prompt", options):
                        pass

                # Should only be called once when retry is disabled
                assert call_count == 1


@pytest.mark.asyncio
async def test_codex_options_compatibility():
    """Test that CodexOptions still work with the updated client."""
    client = CodexClient()

    async def mock_send_query(prompt, options):
        yield CodexMessage(role="assistant", content=[TextBlock(text="Response with CodexOptions")])

    with patch.object(client.transport, "send_query", side_effect=mock_send_query):
        with patch.object(client.transport, "connect", new_callable=AsyncMock):
            with patch.object(client.transport, "disconnect", new_callable=AsyncMock):
                messages = []
                options = CodexOptions(model="o4")

                async for message in client.query("test prompt", options):
                    messages.append(message)

                assert len(messages) == 1
                assert messages[0].content == "Response with CodexOptions"


@pytest.mark.asyncio
async def test_module_level_query_with_retry():
    """Test module-level query function with retry."""
    # Mock the transport at module level
    with patch("claif_cod.client.CodexTransport") as MockTransport:
        mock_transport = MockTransport.return_value
        mock_transport.connect = AsyncMock()
        mock_transport.disconnect = AsyncMock()

        call_count = 0

        async def mock_send_query(prompt, options):
            nonlocal call_count
            call_count += 1

            if call_count == 1:
                msg = "codex"
                raise ProviderError(msg, "First attempt failed")

            yield CodexMessage(role="assistant", content=[TextBlock(text="Success on second attempt")])

        mock_transport.send_query = mock_send_query

        messages = []
        options = ClaifOptions(retry_count=2, retry_delay=0.1)

        async for message in query("test prompt", options):
            messages.append(message)

        assert len(messages) == 1
        assert messages[0].content == "Success on second attempt"
        assert call_count == 2
