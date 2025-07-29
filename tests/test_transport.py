"""Test suite for claif_cod transport layer."""

import json
import os
import signal
import subprocess
from unittest.mock import AsyncMock, Mock, patch

import pytest
from claif.common import TransportError
from tenacity import RetryError

from claif_cod.transport import CodexTransport
from claif_cod.types import CodeBlock, CodexMessage, CodexOptions, CodexResponse, ErrorBlock, ResultMessage, TextBlock


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
                images=["/img1.png", "/img2.jpg"],
            )
            command = transport._build_command("Test prompt", options)

            expected = [
                "/path/to/codex",
                "-m",
                "o4",
                "-w",
                "/tmp/work",
                "-a",
                "full-auto",
                "--dangerously-auto-approve-everything",
                "--full-auto",
                "-q",
                "-i",
                "/img1.png",
                "-i",
                "/img2.jpg",
                "Test prompt",
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
        mock_result.stdout = json.dumps(
            {
                "type": "message",
                "role": "assistant",
                "status": "completed",
                "content": [{"type": "output_text", "text": "Hello from Codex!"}],
            }
        )
        mock_result.stderr = ""
        mock_subprocess_run.return_value = mock_result

        options = CodexOptions(model="o4-mini", timeout=30)
        response = transport.execute("Test prompt", options)

        assert isinstance(response, CodexResponse)
        assert len(response.content) == 1
        assert response.content[0].text == "Hello from Codex!"
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
        mock_result.stdout = json.dumps(
            {
                "type": "message",
                "role": "assistant",
                "status": "completed",
                "content": [
                    {"type": "output_text", "text": "Part 1"},
                    {"type": "output_text", "text": "Part 2"},
                    {"type": "output_text", "text": "Part 3"},
                ],
            }
        )
        mock_result.stderr = ""
        mock_subprocess_run.return_value = mock_result

        response = transport.execute("Test", CodexOptions())
        assert len(response.content) == 1
        assert response.content[0].text == "Part 1\nPart 2\nPart 3"

    def test_execute_success_plain_text_fallback(self, transport, mock_subprocess_run, mock_find_executable):
        """Test execution with plain text response (non-JSON)."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Plain text response"
        mock_result.stderr = ""
        mock_subprocess_run.return_value = mock_result

        response = transport.execute("Test", CodexOptions())
        assert len(response.content) == 1
        assert response.content[0].text == "Plain text response"
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
            mock_execute.return_value = CodexResponse(content="Test response", role="assistant")

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
                CodexResponse(content="Success", role="assistant"),
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
            "429 Too Many Requests",
        ]

        for error_msg in retryable_errors:
            with patch.object(transport, "execute") as mock_execute:
                mock_execute.side_effect = [
                    TransportError(error_msg),
                    CodexResponse(content="Success", role="assistant"),
                ]

                options = CodexOptions(retry_count=1, retry_delay=0.1)
                messages = []
                async for msg in transport.send_query("Test", options):
                    messages.append(msg)

                assert len(messages) == 2
                assert isinstance(messages[0], CodexMessage)
                # Should have retried
                assert mock_execute.call_count == 2

    @pytest.mark.asyncio
    async def test_execute_async_basic(self, transport):
        """Test basic _execute_async functionality."""
        with patch("claif_cod.transport.asyncio.create_subprocess_exec") as mock_create:
            mock_process = Mock()
            mock_process.stdout = AsyncMock()
            mock_process.stderr = AsyncMock()
            mock_process.wait = AsyncMock(return_value=0)

            # Mock stdout reading
            json_response = {
                "type": "message",
                "role": "assistant",
                "content": [{"type": "output_text", "text": "Hello"}],
            }
            mock_process.stdout.readline = AsyncMock(
                side_effect=[
                    json.dumps(json_response).encode() + b"\n",
                    b"",  # End of stream
                ]
            )
            mock_process.stderr.read = AsyncMock(return_value=b"")

            mock_create.return_value = mock_process

            options = CodexOptions(timeout=30)
            messages = []
            async for msg in transport._execute_async("Test prompt", options):
                messages.append(msg)

            assert len(messages) == 2  # CodexMessage + ResultMessage
            assert isinstance(messages[0], CodexMessage)
            assert messages[0].role == "assistant"
            assert len(messages[0].content) == 1
            assert isinstance(messages[0].content[0], TextBlock)
            assert messages[0].content[0].text == "Hello"

            assert isinstance(messages[1], ResultMessage)
            assert messages[1].error is False

    @pytest.mark.asyncio
    async def test_execute_async_with_code_block(self, transport):
        """Test _execute_async handling code blocks."""
        with patch("claif_cod.transport.asyncio.create_subprocess_exec") as mock_create:
            mock_process = Mock()
            mock_process.stdout = AsyncMock()
            mock_process.stderr = AsyncMock()
            mock_process.wait = AsyncMock(return_value=0)

            json_response = {
                "type": "message",
                "role": "assistant",
                "content": [{"type": "code", "language": "python", "content": "print('hello')"}],
            }
            mock_process.stdout.readline = AsyncMock(
                side_effect=[
                    json.dumps(json_response).encode() + b"\n",
                    b"",
                ]
            )
            mock_process.stderr.read = AsyncMock(return_value=b"")

            mock_create.return_value = mock_process

            options = CodexOptions()
            messages = []
            async for msg in transport._execute_async("Test", options):
                messages.append(msg)

            assert len(messages) == 2
            assert isinstance(messages[0], CodexMessage)
            assert len(messages[0].content) == 1
            assert isinstance(messages[0].content[0], CodeBlock)
            assert messages[0].content[0].language == "python"
            assert messages[0].content[0].content == "print('hello')"

    @pytest.mark.asyncio
    async def test_execute_async_with_error_block(self, transport):
        """Test _execute_async handling error blocks."""
        with patch("claif_cod.transport.asyncio.create_subprocess_exec") as mock_create:
            mock_process = Mock()
            mock_process.stdout = AsyncMock()
            mock_process.stderr = AsyncMock()
            mock_process.wait = AsyncMock(return_value=0)

            json_response = {
                "type": "message",
                "role": "assistant",
                "content": [{"type": "error", "error_message": "Something went wrong"}],
            }
            mock_process.stdout.readline = AsyncMock(
                side_effect=[
                    json.dumps(json_response).encode() + b"\n",
                    b"",
                ]
            )
            mock_process.stderr.read = AsyncMock(return_value=b"")

            mock_create.return_value = mock_process

            options = CodexOptions()
            messages = []
            async for msg in transport._execute_async("Test", options):
                messages.append(msg)

            assert len(messages) == 2
            assert isinstance(messages[0], CodexMessage)
            assert len(messages[0].content) == 1
            assert isinstance(messages[0].content[0], ErrorBlock)
            assert messages[0].content[0].error_message == "Something went wrong"

    @pytest.mark.asyncio
    async def test_execute_async_plain_text_fallback(self, transport):
        """Test _execute_async with non-JSON output."""
        with patch("claif_cod.transport.asyncio.create_subprocess_exec") as mock_create:
            mock_process = Mock()
            mock_process.stdout = AsyncMock()
            mock_process.stderr = AsyncMock()
            mock_process.wait = AsyncMock(return_value=0)

            # Non-JSON output
            mock_process.stdout.readline = AsyncMock(
                side_effect=[
                    b"Plain text output\n",
                    b"",
                ]
            )
            mock_process.stderr.read = AsyncMock(return_value=b"")

            mock_create.return_value = mock_process

            options = CodexOptions()
            messages = []
            async for msg in transport._execute_async("Test", options):
                messages.append(msg)

            assert len(messages) == 2
            assert isinstance(messages[0], CodexMessage)
            assert messages[0].role == "assistant"
            assert len(messages[0].content) == 1
            assert isinstance(messages[0].content[0], TextBlock)
            assert messages[0].content[0].text == "Plain text output"

    @pytest.mark.asyncio
    async def test_execute_async_process_timeout(self, transport):
        """Test _execute_async with process timeout."""
        with patch("claif_cod.transport.asyncio.create_subprocess_exec") as mock_create:
            mock_process = Mock()
            mock_process.stdout = AsyncMock()
            mock_process.stderr = AsyncMock()
            mock_process.wait = AsyncMock(side_effect=TimeoutError())
            mock_process.kill = Mock()
            mock_process.pid = 12345

            mock_process.stdout.readline = AsyncMock(
                side_effect=[
                    b"Some output\n",
                    b"",
                ]
            )

            mock_create.return_value = mock_process

            options = CodexOptions(timeout=1)

            with pytest.raises(TransportError, match="timed out after 1s"):
                async for _ in transport._execute_async("Test", options):
                    pass

    @pytest.mark.asyncio
    async def test_execute_async_process_error(self, transport):
        """Test _execute_async with process returning error code."""
        with patch("claif_cod.transport.asyncio.create_subprocess_exec") as mock_create:
            mock_process = Mock()
            mock_process.stdout = AsyncMock()
            mock_process.stderr = AsyncMock()
            mock_process.wait = AsyncMock(return_value=1)  # Error exit code

            mock_process.stdout.readline = AsyncMock(side_effect=[b""])
            mock_process.stderr.read = AsyncMock(return_value=b"Command failed with error")

            mock_create.return_value = mock_process

            options = CodexOptions()

            with pytest.raises(TransportError, match="exit code 1.*Command failed with error"):
                async for _ in transport._execute_async("Test", options):
                    pass

    @pytest.mark.asyncio
    async def test_execute_async_process_cleanup_on_exception(self, transport):
        """Test _execute_async properly cleans up process on exception."""
        with patch("claif_cod.transport.asyncio.create_subprocess_exec") as mock_create:
            mock_process = Mock()
            mock_process.stdout = AsyncMock()
            mock_process.stderr = AsyncMock()
            mock_process.wait = AsyncMock(return_value=0)
            mock_process.returncode = None
            mock_process.terminate = Mock()
            mock_process.kill = Mock()
            mock_process.pid = 12345

            # Make stdout reading raise an exception
            mock_process.stdout.readline = AsyncMock(side_effect=Exception("Read error"))

            mock_create.return_value = mock_process

            options = CodexOptions()

            with pytest.raises(TransportError):
                async for _ in transport._execute_async("Test", options):
                    pass

            # Verify cleanup was attempted
            mock_process.terminate.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_async_unix_process_groups(self, transport):
        """Test _execute_async uses process groups on Unix systems."""
        with patch("claif_cod.transport.os.name", "posix"):
            with patch("claif_cod.transport.asyncio.create_subprocess_exec") as mock_create:
                mock_process = Mock()
                mock_process.stdout = AsyncMock()
                mock_process.stderr = AsyncMock()
                mock_process.wait = AsyncMock(return_value=0)

                mock_process.stdout.readline = AsyncMock(side_effect=[b""])
                mock_process.stderr.read = AsyncMock(return_value=b"")

                mock_create.return_value = mock_process

                options = CodexOptions()

                messages = []
                async for msg in transport._execute_async("Test", options):
                    messages.append(msg)

                # Verify process was created with preexec_fn for process group
                mock_create.assert_called_once()
                call_kwargs = mock_create.call_args[1]
                assert call_kwargs["preexec_fn"] == os.setsid

    @pytest.mark.asyncio
    async def test_execute_async_windows_no_process_groups(self, transport):
        """Test _execute_async doesn't use process groups on Windows."""
        with patch("claif_cod.transport.os.name", "nt"):
            with patch("claif_cod.transport.asyncio.create_subprocess_exec") as mock_create:
                mock_process = Mock()
                mock_process.stdout = AsyncMock()
                mock_process.stderr = AsyncMock()
                mock_process.wait = AsyncMock(return_value=0)

                mock_process.stdout.readline = AsyncMock(side_effect=[b""])
                mock_process.stderr.read = AsyncMock(return_value=b"")

                mock_create.return_value = mock_process

                options = CodexOptions()

                messages = []
                async for msg in transport._execute_async("Test", options):
                    messages.append(msg)

                # Verify process was created without preexec_fn
                mock_create.assert_called_once()
                call_kwargs = mock_create.call_args[1]
                assert call_kwargs["preexec_fn"] is None

    @pytest.mark.asyncio
    async def test_disconnect_with_running_process(self, transport):
        """Test disconnect properly terminates running process."""
        mock_process = Mock()
        mock_process.returncode = None
        mock_process.terminate = Mock()
        mock_process.kill = Mock()
        mock_process.wait = AsyncMock(return_value=0)
        mock_process.pid = 12345

        transport.process = mock_process

        await transport.disconnect()

        mock_process.terminate.assert_called_once()
        mock_process.wait.assert_called_once()
        assert transport.process is None

    @pytest.mark.asyncio
    async def test_disconnect_force_kill_on_timeout(self, transport):
        """Test disconnect force kills process if graceful termination times out."""
        mock_process = Mock()
        mock_process.returncode = None
        mock_process.terminate = Mock()
        mock_process.kill = Mock()
        mock_process.wait = AsyncMock(side_effect=TimeoutError())
        mock_process.pid = 12345

        transport.process = mock_process

        with patch("claif_cod.transport.os.name", "posix"):
            with patch("claif_cod.transport.os.killpg") as mock_killpg:
                with patch("claif_cod.transport.os.getpgid", return_value=12345):
                    await transport.disconnect()

                    mock_process.terminate.assert_called_once()
                    mock_killpg.assert_called_once_with(12345, signal.SIGKILL)

    @pytest.mark.asyncio
    async def test_disconnect_windows_force_kill(self, transport):
        """Test disconnect on Windows uses kill() instead of killpg."""
        mock_process = Mock()
        mock_process.returncode = None
        mock_process.terminate = Mock()
        mock_process.kill = Mock()
        mock_process.wait = AsyncMock(side_effect=TimeoutError())
        mock_process.pid = 12345

        transport.process = mock_process

        with patch("claif_cod.transport.os.name", "nt"):
            await transport.disconnect()

            mock_process.terminate.assert_called_once()
            mock_process.kill.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect_handles_process_lookup_error(self, transport):
        """Test disconnect handles ProcessLookupError gracefully."""
        mock_process = Mock()
        mock_process.returncode = None
        mock_process.terminate = Mock()
        mock_process.kill = Mock()
        mock_process.wait = AsyncMock(side_effect=TimeoutError())
        mock_process.pid = 12345

        transport.process = mock_process

        with patch("claif_cod.transport.os.name", "posix"):
            with patch("claif_cod.transport.os.killpg", side_effect=ProcessLookupError):
                with patch("claif_cod.transport.os.getpgid", return_value=12345):
                    # Should not raise exception
                    await transport.disconnect()

                    mock_process.terminate.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect_no_process(self, transport):
        """Test disconnect when no process is running."""
        transport.process = None

        # Should not raise exception
        await transport.disconnect()

    @pytest.mark.asyncio
    async def test_disconnect_exception_handling(self, transport):
        """Test disconnect handles exceptions gracefully."""
        mock_process = Mock()
        mock_process.returncode = None
        mock_process.terminate = Mock(side_effect=Exception("Terminate failed"))

        transport.process = mock_process

        # Should not raise exception
        await transport.disconnect()

        # Process should still be cleared
        assert transport.process is None

    def test_build_env_with_claif_utils(self, transport):
        """Test _build_env with claif.common.utils available."""
        mock_env = {"PATH": "/custom/path", "HOME": "/home/user"}

        with patch("claif_cod.transport.inject_claif_bin_to_path", return_value=mock_env):
            env = transport._build_env()

            assert env["PATH"] == "/custom/path"
            assert env["HOME"] == "/home/user"
            assert env["CODEX_SDK"] == "1"
            assert env["CLAIF_PROVIDER"] == "codex"

    def test_build_env_import_error_fallback(self, transport):
        """Test _build_env fallback when claif.common.utils is unavailable."""
        mock_env = {"PATH": "/system/path"}

        with patch("claif_cod.transport.inject_claif_bin_to_path", side_effect=ImportError):
            with patch("claif_cod.transport.os.environ.copy", return_value=mock_env):
                env = transport._build_env()

                assert env["PATH"] == "/system/path"
                assert env["CODEX_SDK"] == "1"
                assert env["CLAIF_PROVIDER"] == "codex"

    def test_find_cli_with_install_error(self, transport):
        """Test _find_cli converts InstallError to TransportError."""
        from claif.common import InstallError

        with patch("claif_cod.transport.find_executable", side_effect=InstallError("CLI not found")):
            with pytest.raises(TransportError, match="Codex CLI executable not found: CLI not found"):
                transport._find_cli()

    def test_build_command_working_dir_and_cwd_priority(self, transport):
        """Test that working_dir takes priority over cwd in command building."""
        with patch("claif_cod.transport.find_executable", return_value="codex"):
            options = CodexOptions(working_dir="/work", cwd="/cwd")
            command = transport._build_command("test", options)

            assert "-w" in command
            assert "/work" in command
            assert "/cwd" not in command

    def test_build_command_cwd_fallback(self, transport):
        """Test that cwd is used when working_dir is not set."""
        with patch("claif_cod.transport.find_executable", return_value="codex"):
            options = CodexOptions(cwd="/fallback/cwd")
            command = transport._build_command("test", options)

            assert "-w" in command
            assert "/fallback/cwd" in command

    def test_build_command_no_model(self, transport):
        """Test command building without model specified."""
        with patch("claif_cod.transport.find_executable", return_value="codex"):
            options = CodexOptions(model=None)
            command = transport._build_command("test", options)

            assert "-m" not in command
            assert command == ["codex", "-q", "test"]

    def test_build_command_with_path_object(self, transport):
        """Test command building with Path object for working_dir."""
        with patch("claif_cod.transport.find_executable", return_value="codex"):
            from pathlib import Path

            options = CodexOptions(working_dir=Path("/path/to/work"))
            command = transport._build_command("test", options)

            assert "-w" in command
            assert "/path/to/work" in command
