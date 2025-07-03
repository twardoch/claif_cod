"""Test suite for claif_cod client."""

from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from claif.common import ClaifOptions, ClaifTimeoutError, Message, MessageRole, ProviderError

from claif_cod.client import CodexClient, _convert_claif_to_codex_options, _is_cli_missing_error, query
from claif_cod.types import CodexMessage, CodexOptions, ResultMessage, TextBlock


class TestHelperFunctions:
    """Test helper functions."""

    def test_is_cli_missing_error(self):
        """Test CLI missing error detection."""
        # Positive cases
        assert _is_cli_missing_error(Exception("command not found"))
        assert _is_cli_missing_error(Exception("No such file or directory"))
        assert _is_cli_missing_error(Exception("is not recognized as an internal or external command"))
        assert _is_cli_missing_error(Exception("Cannot find codex"))
        assert _is_cli_missing_error(Exception("codex not found"))
        assert _is_cli_missing_error(Exception("executable not found"))
        assert _is_cli_missing_error(Exception("Permission denied"))
        assert _is_cli_missing_error(FileNotFoundError("codex"))

        # Negative cases
        assert not _is_cli_missing_error(Exception("API key invalid"))
        assert not _is_cli_missing_error(Exception("Network error"))
        assert not _is_cli_missing_error(Exception("Rate limit exceeded"))

    def test_convert_claif_to_codex_options(self):
        """Test options conversion."""
        claif_opts = ClaifOptions(
            model="gpt-4",
            temperature=0.7,
            max_tokens=1000,
            timeout=60,
            verbose=True
        )
        
        codex_opts = _convert_claif_to_codex_options(claif_opts)
        
        assert isinstance(codex_opts, CodexOptions)
        assert codex_opts.model == "gpt-4"
        assert codex_opts.temperature == 0.7
        assert codex_opts.max_tokens == 1000
        assert codex_opts.timeout == 60
        assert codex_opts.verbose is True

    def test_convert_claif_to_codex_options_defaults(self):
        """Test options conversion with defaults."""
        claif_opts = ClaifOptions()
        codex_opts = _convert_claif_to_codex_options(claif_opts)
        
        assert codex_opts.model == "o4-mini"  # Default when None


class TestCodexClient:
    """Test suite for CodexClient."""

    @pytest.fixture
    def client(self):
        """Create a client instance."""
        return CodexClient()

    @pytest.fixture
    def mock_transport(self):
        """Create a mock transport."""
        transport = MagicMock()
        transport.connect = AsyncMock()
        transport.disconnect = AsyncMock()
        transport.send_query = AsyncMock()
        return transport

    @pytest.mark.anyio
    async def test_query_with_codex_options(self, client, mock_transport):
        """Test query with CodexOptions."""
        client.transport = mock_transport

        # Mock transport responses
        async def mock_send_query(prompt, options):
            yield CodexMessage(
                role="assistant",
                content=[TextBlock(text="Test response")]
            )
            yield ResultMessage(error=False, session_id="test")

        mock_transport.send_query.return_value = mock_send_query("Test prompt", None)

        options = CodexOptions(model="o4", temperature=0.5)
        messages = []
        async for msg in client.query("Test prompt", options):
            messages.append(msg)

        assert len(messages) == 1
        assert isinstance(messages[0], Message)
        # Content is now auto-converted to List[TextBlock]
        assert len(messages[0].content) == 1
        assert messages[0].content[0].text == "Test response"
        assert messages[0].role == MessageRole.ASSISTANT

        mock_transport.connect.assert_called_once()
        mock_transport.disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_query_with_claif_options(self, client, mock_transport):
        """Test query with ClaifOptions conversion."""
        client.transport = mock_transport

        async def mock_send_query(prompt, options):
            # Verify options were converted correctly
            assert isinstance(options, CodexOptions)
            assert options.model == "gpt-4"
            yield CodexMessage(
                role="assistant",
                content=[TextBlock(text="Response")]
            )

        mock_transport.send_query.side_effect = mock_send_query

        claif_options = ClaifOptions(model="gpt-4", retry_count=5, retry_delay=2.0)
        messages = []
        async for msg in client.query("Test", claif_options):
            messages.append(msg)

        assert len(messages) == 1
        # Content is now auto-converted to List[TextBlock]
        assert len(messages[0].content) == 1
        assert messages[0].content[0].text == "Response"

    @pytest.mark.asyncio
    async def test_query_no_options(self, client, mock_transport):
        """Test query with no options (defaults)."""
        client.transport = mock_transport

        async def mock_send_query(prompt, options):
            assert isinstance(options, CodexOptions)
            assert options.model == "o4-mini"  # Default
            yield CodexMessage(
                role="assistant",
                content=[TextBlock(text="Default response")]
            )

        mock_transport.send_query.side_effect = mock_send_query

        messages = []
        async for msg in client.query("Test"):
            messages.append(msg)

        assert len(messages) == 1
        assert len(messages[0].content) == 1 and messages[0].content[0].text == "Default response"

    @pytest.mark.asyncio
    async def test_query_with_error_result(self, client, mock_transport):
        """Test query handling error results."""
        client.transport = mock_transport

        async def mock_send_query(prompt, options):
            yield ResultMessage(
                error=True,
                message="API error occurred",
                session_id="test"
            )

        mock_transport.send_query.side_effect = mock_send_query

        with pytest.raises(ProviderError) as exc_info:
            async for _ in client.query("Test"):
                pass

        assert "API error occurred" in str(exc_info.value)
        assert exc_info.value.provider == "codex"

    @pytest.mark.asyncio
    async def test_query_auto_install_on_cli_missing(self, client):
        """Test auto-install when CLI is missing."""
        # Mock transport to raise CLI missing error on first connect
        with patch("claif_cod.client.CodexTransport") as MockTransport:
            mock_transport = MockTransport.return_value
            mock_transport.connect = AsyncMock(
                side_effect=[FileNotFoundError("codex not found"), None]
            )
            mock_transport.disconnect = AsyncMock()
            
            async def mock_send_query(prompt, options):
                yield CodexMessage(
                    role="assistant",
                    content=[TextBlock(text="Installed and working")]
                )

            mock_transport.send_query = AsyncMock(side_effect=mock_send_query)

            # Mock successful install
            with patch("claif_cod.client.install_codex") as mock_install:
                mock_install.return_value = {"installed": True}

                new_client = CodexClient()
                messages = []
                async for msg in new_client.query("Test"):
                    messages.append(msg)

                assert len(messages) == 1
                assert len(messages[0].content) == 1 and messages[0].content[0].text == "Installed and working"
                mock_install.assert_called_once()

    @pytest.mark.asyncio
    async def test_query_auto_install_fails(self, client):
        """Test when auto-install fails."""
        with patch("claif_cod.client.CodexTransport") as MockTransport:
            mock_transport = MockTransport.return_value
            mock_transport.connect = AsyncMock(
                side_effect=OSError("codex not found")
            )

            with patch("claif_cod.client.install_codex") as mock_install:
                mock_install.return_value = {
                    "installed": False,
                    "message": "Installation failed"
                }

                new_client = CodexClient()
                with pytest.raises(ProviderError) as exc_info:
                    async for _ in new_client.query("Test"):
                        pass

                assert "auto-install failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_query_retry_disabled(self, client, mock_transport):
        """Test query with retry disabled."""
        client.transport = mock_transport

        async def mock_send_query(prompt, options):
            yield CodexMessage(
                role="assistant",
                content=[TextBlock(text="No retry")]
            )

        mock_transport.send_query.side_effect = mock_send_query

        options = CodexOptions(retry_count=0)
        messages = []
        async for msg in client.query("Test", options):
            messages.append(msg)

        assert len(messages) == 1
        assert len(messages[0].content) == 1 and messages[0].content[0].text == "No retry"
        # Should be called only once
        mock_transport.send_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_query_retry_on_failure(self, client, mock_transport):
        """Test retry logic on failures."""
        client.transport = mock_transport

        # First attempt fails, second succeeds
        attempt_count = 0

        async def mock_send_query(prompt, options):
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count == 1:
                raise ConnectionError("Network error")
            yield CodexMessage(
                role="assistant",
                content=[TextBlock(text="Success after retry")]
            )

        mock_transport.send_query.side_effect = mock_send_query

        options = ClaifOptions(retry_count=2, retry_delay=0.1)
        messages = []
        async for msg in client.query("Test", options):
            messages.append(msg)

        assert len(messages) == 1
        assert len(messages[0].content) == 1 and messages[0].content[0].text == "Success after retry"
        assert attempt_count == 2

    @pytest.mark.asyncio
    async def test_query_all_retries_fail(self, client, mock_transport):
        """Test when all retry attempts fail."""
        client.transport = mock_transport

        async def mock_send_query(prompt, options):
            raise TimeoutError("Connection timeout")

        mock_transport.send_query.side_effect = mock_send_query

        options = ClaifOptions(retry_count=2, retry_delay=0.1)
        
        with pytest.raises(TimeoutError):
            async for _ in client.query("Test", options):
                pass

    @pytest.mark.asyncio
    async def test_query_no_messages_yielded(self, client, mock_transport):
        """Test error when no messages are yielded."""
        client.transport = mock_transport

        async def mock_send_query(prompt, options):
            # Yield nothing
            return
            yield  # Make it a generator

        mock_transport.send_query.side_effect = mock_send_query

        with pytest.raises(ProviderError) as exc_info:
            async for _ in client.query("Test"):
                pass

        assert "No response received" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_query_transport_error_conversion(self, client, mock_transport):
        """Test that transport errors are converted to ProviderError."""
        client.transport = mock_transport

        async def mock_send_query(prompt, options):
            raise ValueError("Some transport error")

        mock_transport.send_query.side_effect = mock_send_query

        options = CodexOptions(retry_count=0)  # Disable retry for this test
        
        with pytest.raises(ProviderError) as exc_info:
            async for _ in client.query("Test", options):
                pass

        assert exc_info.value.provider == "codex"
        assert "Some transport error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_query_ensures_disconnect(self, client, mock_transport):
        """Test that disconnect is called even on error."""
        client.transport = mock_transport

        async def mock_send_query(prompt, options):
            raise Exception("Test error")

        mock_transport.send_query.side_effect = mock_send_query

        options = CodexOptions(retry_count=0)
        
        with pytest.raises(ProviderError):
            async for _ in client.query("Test", options):
                pass

        # Disconnect should still be called
        mock_transport.disconnect.assert_called_once()


class TestModuleLevelFunctions:
    """Test module-level functions."""

    @pytest.mark.asyncio
    async def test_query_function(self):
        """Test the module-level query function."""
        with patch("claif_cod.client._get_client") as mock_get_client:
            mock_client = MagicMock()
            
            async def mock_query(prompt, options):
                yield Message(role=MessageRole.ASSISTANT, content="Module test")

            mock_client.query = mock_query
            mock_get_client.return_value = mock_client

            messages = []
            async for msg in query("Test prompt"):
                messages.append(msg)

            assert len(messages) == 1
            assert len(messages[0].content) == 1 and messages[0].content[0].text == "Module test"

    def test_get_client_singleton(self):
        """Test that _get_client returns singleton."""
        from claif_cod.client import _get_client, _client

        # Reset global client
        import claif_cod.client
        claif_cod.client._client = None

        client1 = _get_client()
        client2 = _get_client()

        assert client1 is client2
        assert isinstance(client1, CodexClient)