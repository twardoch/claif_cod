"""Test suite for claif_cod transport layer."""

import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
from claif.common import TransportError
from tenacity import RetryError

from claif_cod.transport import CodexTransport
from claif_cod.types import CodexOptions, CodexResponse, CodexMessage, ResultMessage, TextBlock


class TestCodexTransport:
    """Test suite for CodexTransport."""

    @pytest.fixture
    def transport(self):
        """Create a transport instance."""
        return CodexTransport(verbose=True)

    @pytest.fixture
    def mock_subprocess_run(self):
        """Mock subprocess.run."""
        with patch("claif_cod.transport.subprocess.run") as mock_run:
            yield mock_run

    @pytest.fixture
    def mock_find_executable(self):
        """Mock find_executable."""
        with patch("claif_cod.transport.find_executable") as mock_find:
            mock_find.return_value = "/usr/local/bin/codex"
            yield mock_find

    def test_init(self):
        """Test transport initialization."""
        transport = CodexTransport(verbose=True)
        assert transport.verbose is True

        transport2 = CodexTransport()
        assert transport2.verbose is False

    @pytest.mark.asyncio
    async def test_connect_disconnect(self, transport):
        """Test connect and disconnect are no-ops."""
        await transport.connect()  # Should not raise
        await transport.disconnect()  # Should not raise

    def test_build_command_basic(self, transport):
        """Test basic command building."""
        with patch("claif_cod.transport.find_executable", return_value="codex"):
            options = CodexOptions(model="o4-mini")
            command = transport._build_command("Hello world", options)
            
            assert command == ["codex", "-m", "o4-mini", "-q", "Hello world"]

    def test_build_command_with_all_options(self, transport):
        """Test command building with all options."""
        with patch("claif_cod.transport.find_executable", return_value="/path/to/codex"):
            options = CodexOptions(
                model="o4",
                working_dir="/tmp/work",
                action_mode="full-auto",
                auto_approve_everything=True,
                full_auto=True,
                images=["/img1.png", "/img2.jpg"]
            )
            command = transport._build_command("Test prompt", options)
            
            expected = [
                "/path/to/codex",
                "-m", "o4",
                "-w", "/tmp/work",
                "-a", "full-auto",
                "--dangerously-auto-approve-everything",
                "--full-auto",
                "-q",
                "-i", "/img1.png",
                "-i", "/img2.jpg",
                "Test prompt"
            ]
            assert command == expected

    def test_build_command_with_cwd_alias(self, transport):
        """Test that cwd is handled as alias for working_dir."""
        with patch("claif_cod.transport.find_executable", return_value="codex"):
            options = CodexOptions(cwd="/home/user")
            command = transport._build_command("test", options)
            
            # Should use cwd value
            assert "-w" in command
            assert "/home/user" in command

    def test_build_command_with_space_in_path(self, transport):
        """Test command building with spaces in executable path."""
        # Test with existing file path containing spaces
        with patch("claif_cod.transport.find_executable", return_value="/path with spaces/codex"):
            with patch("claif_cod.transport.Path.exists", return_value=True):
                options = CodexOptions()
                command = transport._build_command("test", options)
                assert command[0] == "/path with spaces/codex"

    def test_build_command_with_shell_command(self, transport):
        """Test command building with shell command format (e.g., 'deno run script.js')."""
        with patch("claif_cod.transport.find_executable", return_value="deno run /path/to/script.js"):
            with patch("claif_cod.transport.Path.exists", return_value=False):
                options = CodexOptions()
                command = transport._build_command("test", options)
                assert command[:3] == ["deno", "run", "/path/to/script.js"]

    def test_build_env(self, transport):
        """Test environment variable building."""
        with patch("claif_cod.transport.inject_claif_bin_to_path") as mock_inject:
            mock_inject.return_value = {"PATH": "/custom/path"}
            env = transport._build_env()
            
            assert env["CODEX_SDK"] == "1"
            assert env["CLAIF_PROVIDER"] == "codex"
            assert env["PATH"] == "/custom/path"

    def test_build_env_import_error(self, transport):
        """Test environment building when import fails."""
        with patch("claif_cod.transport.inject_claif_bin_to_path", side_effect=ImportError):
            with patch("claif_cod.transport.os.environ.copy", return_value={"PATH": "/bin"}):
                env = transport._build_env()
                
                assert env["CODEX_SDK"] == "1"
                assert env["CLAIF_PROVIDER"] == "codex"
                assert env["PATH"] == "/bin"

    def test_find_cli_success(self, transport, mock_find_executable):
        """Test successful CLI finding."""
        result = transport._find_cli()
        assert result == "/usr/local/bin/codex"
        mock_find_executable.assert_called_once_with("codex", None)

    def test_find_cli_with_exec_path(self, transport, mock_find_executable):
        """Test CLI finding with explicit exec_path."""
        mock_find_executable.return_value = "/custom/codex"
        result = transport._find_cli("/custom/codex")
        assert result == "/custom/codex"
        mock_find_executable.assert_called_once_with("codex", "/custom/codex")

    def test_find_cli_not_found(self, transport):
        """Test CLI not found error."""
        with patch("claif_cod.transport.find_executable", side_effect=TransportError("Not found")):
            with pytest.raises(TransportError, match="Not found"):
                transport._find_cli()

    def test_execute_success_jsonl_format(self, transport, mock_subprocess_run, mock_find_executable):
        """Test successful execution with JSONL response."""
        # Mock successful subprocess response
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({
            "type": "message",
            "role": "assistant",
            "status": "completed",
            "content": [
                {"type": "output_text", "text": "Hello from Codex!"}
            ]
        })
        mock_result.stderr = ""
        mock_subprocess_run.return_value = mock_result

        options = CodexOptions(model="o4-mini", timeout=30)
        response = transport.execute("Test prompt", options)

        assert isinstance(response, CodexResponse)
        assert response.content == "Hello from Codex!"
        assert response.role == "assistant"
        assert response.model == "o4-mini"

        # Verify subprocess was called correctly
        mock_subprocess_run.assert_called_once()
        call_args = mock_subprocess_run.call_args
        assert call_args[0][0][:2] == ["/usr/local/bin/codex", "-m"]
        assert call_args[1]["timeout"] == 30
        assert call_args[1]["text"] is True
        assert call_args[1]["capture_output"] is True

    def test_execute_success_multiple_content_blocks(self, transport, mock_subprocess_run, mock_find_executable):
        """Test execution with multiple content blocks."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({
            "type": "message",
            "role": "assistant",
            "status": "completed",
            "content": [
                {"type": "output_text", "text": "Part 1"},
                {"type": "output_text", "text": "Part 2"},
                {"type": "output_text", "text": "Part 3"}
            ]
        })
        mock_result.stderr = ""
        mock_subprocess_run.return_value = mock_result

        response = transport.execute("Test", CodexOptions())
        assert response.content == "Part 1\nPart 2\nPart 3"

    def test_execute_success_plain_text_fallback(self, transport, mock_subprocess_run, mock_find_executable):
        """Test execution with plain text response (non-JSON)."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Plain text response"
        mock_result.stderr = ""
        mock_subprocess_run.return_value = mock_result

        response = transport.execute("Test", CodexOptions())
        assert response.content == "Plain text response"
        assert response.raw_response == {"raw_output": "Plain text response"}

    def test_execute_error_non_zero_exit(self, transport, mock_subprocess_run, mock_find_executable):
        """Test execution with non-zero exit code."""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Command failed"
        mock_subprocess_run.return_value = mock_result

        with pytest.raises(TransportError, match="exit code 1.*Command failed"):
            transport.execute("Test", CodexOptions())

    def test_execute_timeout(self, transport, mock_subprocess_run, mock_find_executable):
        """Test execution timeout."""
        mock_subprocess_run.side_effect = subprocess.TimeoutExpired("codex", 30)

        with pytest.raises(TransportError, match="timed out after 30s"):
            transport.execute("Test", CodexOptions(timeout=30))

    def test_execute_generic_error(self, transport, mock_subprocess_run, mock_find_executable):
        """Test execution with generic error."""
        mock_subprocess_run.side_effect = OSError("Permission denied")

        with pytest.raises(TransportError, match="Failed to execute.*Permission denied"):
            transport.execute("Test", CodexOptions())

    @pytest.mark.asyncio
    async def test_send_query_no_retry(self, transport, mock_find_executable):
        """Test send_query with retry disabled."""
        with patch.object(transport, "execute") as mock_execute:
            mock_execute.return_value = CodexResponse(
                content="Test response",
                role="assistant"
            )

            options = CodexOptions(no_retry=True)
            messages = []
            async for msg in transport.send_query("Test", options):
                messages.append(msg)

            assert len(messages) == 2
            assert isinstance(messages[0], CodexMessage)
            assert messages[0].content[0].text == "Test response"
            assert isinstance(messages[1], ResultMessage)
            assert messages[1].error is False

    @pytest.mark.asyncio
    async def test_send_query_with_error_no_retry(self, transport, mock_find_executable):
        """Test send_query error handling with no retry."""
        with patch.object(transport, "execute") as mock_execute:
            mock_execute.side_effect = TransportError("Test error")

            options = CodexOptions(retry_count=0)
            messages = []
            async for msg in transport.send_query("Test", options):
                messages.append(msg)

            assert len(messages) == 1
            assert isinstance(messages[0], ResultMessage)
            assert messages[0].error is True
            assert "Test error" in messages[0].message

    @pytest.mark.asyncio
    async def test_send_query_retryable_error(self, transport, mock_find_executable):
        """Test send_query with retryable error patterns."""
        with patch.object(transport, "execute") as mock_execute:
            # First call fails with timeout, second succeeds
            mock_execute.side_effect = [
                TransportError("Connection timeout"),
                CodexResponse(content="Success", role="assistant")
            ]

            options = CodexOptions(retry_count=2, retry_delay=0.1)
            messages = []
            async for msg in transport.send_query("Test", options):
                messages.append(msg)

            assert len(messages) == 2
            assert isinstance(messages[0], CodexMessage)
            assert messages[0].content[0].text == "Success"
            assert mock_execute.call_count == 2

    @pytest.mark.asyncio 
    async def test_send_query_non_retryable_error(self, transport, mock_find_executable):
        """Test send_query with non-retryable error."""
        with patch.object(transport, "execute") as mock_execute:
            mock_execute.side_effect = TransportError("Invalid API key")

            options = CodexOptions(retry_count=3, retry_delay=0.1)
            messages = []
            async for msg in transport.send_query("Test", options):
                messages.append(msg)

            assert len(messages) == 1
            assert isinstance(messages[0], ResultMessage)
            assert messages[0].error is True
            assert "Invalid API key" in messages[0].message
            # Should not retry for non-retryable errors
            assert mock_execute.call_count == 1

    @pytest.mark.asyncio
    async def test_send_query_all_retries_fail(self, transport, mock_find_executable):
        """Test send_query when all retries fail."""
        with patch.object(transport, "execute") as mock_execute:
            mock_execute.side_effect = TransportError("Network error")

            options = CodexOptions(retry_count=2, retry_delay=0.1)
            messages = []
            async for msg in transport.send_query("Test", options):
                messages.append(msg)

            assert len(messages) == 1
            assert isinstance(messages[0], ResultMessage)
            assert messages[0].error is True
            assert "failed after 2 retries" in messages[0].message
            # Initial attempt + 2 retries = 3 calls
            assert mock_execute.call_count == 3

    @pytest.mark.asyncio
    async def test_send_query_checks_retryable_indicators(self, transport, mock_find_executable):
        """Test that send_query properly identifies retryable errors."""
        retryable_errors = [
            "timeout occurred",
            "connection refused",
            "network unreachable",
            "quota exhausted",
            "rate limit exceeded",
            "too many requests",
            "503 Service Unavailable",
            "502 Bad Gateway",
            "429 Too Many Requests"
        ]

        for error_msg in retryable_errors:
            with patch.object(transport, "execute") as mock_execute:
                mock_execute.side_effect = [
                    TransportError(error_msg),
                    CodexResponse(content="Success", role="assistant")
                ]

                options = CodexOptions(retry_count=1, retry_delay=0.1)
                messages = []
                async for msg in transport.send_query("Test", options):
                    messages.append(msg)

                assert len(messages) == 2
                assert isinstance(messages[0], CodexMessage)
                # Should have retried
                assert mock_execute.call_count == 2