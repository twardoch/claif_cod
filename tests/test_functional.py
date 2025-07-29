# this_file: claif_cod/tests/test_functional.py
"""Functional tests for claif_cod that validate actual client behavior."""

from unittest.mock import MagicMock, patch

import pytest
from openai.types.chat import ChatCompletion, ChatCompletionChunk
from openai.types.chat.chat_completion import Choice
from openai.types.chat.chat_completion_chunk import Choice as ChunkChoice
from openai.types.chat.chat_completion_chunk import ChoiceDelta
from openai.types.chat.chat_completion_message import ChatCompletionMessage
from openai.types.completion_usage import CompletionUsage

from claif_cod.client import CodexClient


class TestCodexClientFunctional:
    """Functional tests for the CodexClient."""

    @pytest.fixture
    def mock_codex_response(self):
        """Create a mock response from Codex CLI."""
        return "Hello! I'm Codex, OpenAI's code-focused AI assistant. How can I help you with coding today?"

    @patch("claif_cod.client.subprocess.run")
    @patch("shutil.which")
    def test_basic_query(self, mock_which, mock_run, mock_codex_response):
        """Test basic non-streaming query functionality."""
        # Setup mocks
        mock_which.return_value = "/usr/local/bin/codex"
        mock_run.return_value = MagicMock(returncode=0, stdout=mock_codex_response, stderr="")

        # Create client
        client = CodexClient()

        # Execute
        response = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": "Hello Codex"}])

        # Verify response structure
        assert isinstance(response, ChatCompletion)
        assert response.choices[0].message.content == mock_codex_response
        assert response.choices[0].message.role == "assistant"
        assert response.model == "gpt-4o"

        # Verify subprocess was called correctly
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        cmd = call_args[0][0]

        # Check command structure
        assert "codex" in cmd[0]
        assert "exec" in cmd
        assert "--model" in cmd
        assert "gpt-4o" in cmd[cmd.index("--model") + 1]
        assert "--sandbox" in cmd
        assert "--ask-for-approval" in cmd
        # Prompt should be the last argument
        assert cmd[-1] == "Hello Codex"

    @patch("claif_cod.client.subprocess.run")
    @patch("shutil.which")
    def test_streaming_query(self, mock_which, mock_run):
        """Test streaming query functionality."""
        # Setup mocks
        mock_which.return_value = "/usr/local/bin/codex"
        # The current implementation falls back to sync mode for streaming
        mock_run.return_value = MagicMock(returncode=0, stdout="Hello from Codex!", stderr="")

        client = CodexClient()

        # Execute with streaming
        stream = client.chat.completions.create(
            model="gpt-4o", messages=[{"role": "user", "content": "Hello"}], stream=True
        )

        # Collect chunks
        chunks = list(stream)

        # Verify we got chunks
        assert len(chunks) >= 3
        assert all(isinstance(chunk, ChatCompletionChunk) for chunk in chunks)

        # First chunk should have role
        assert chunks[0].choices[0].delta.role == "assistant"

        # Verify content
        content_parts = []
        for chunk in chunks[1:]:
            if chunk.choices and chunk.choices[0].delta.content:
                content_parts.append(chunk.choices[0].delta.content)

        assert "Hello from Codex!" in "".join(content_parts)

    @patch("claif_cod.client.subprocess.run")
    @patch("shutil.which")
    def test_with_parameters(self, mock_which, mock_run, mock_codex_response):
        """Test query with additional parameters."""
        # Setup mocks
        mock_which.return_value = "/usr/local/bin/codex"
        mock_run.return_value = MagicMock(returncode=0, stdout=mock_codex_response, stderr="")

        client = CodexClient()

        # Execute with parameters
        client.chat.completions.create(
            model="o4-mini",
            messages=[
                {"role": "system", "content": "You are a Python expert."},
                {"role": "user", "content": "Write a fibonacci function"},
            ],
            temperature=0.7,
            max_tokens=100,
        )

        # Verify subprocess was called with parameters
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        cmd = call_args[0][0]

        # Check parameters in command
        assert "--temperature" in cmd
        assert "0.7" in cmd
        assert "--model" in cmd
        assert "o4-mini" in cmd[cmd.index("--model") + 1]
        # Note: max_tokens is not currently passed to the CLI

        # Check that system prompt is in the last argument
        prompt = cmd[-1]
        assert "You are a Python expert" in prompt
        assert "Write a fibonacci function" in prompt

    @patch("claif_cod.client.subprocess.run")
    @patch("shutil.which")
    def test_sandbox_and_approval(self, mock_which, mock_run):
        """Test sandbox mode and approval policy."""
        # Setup mocks
        mock_which.return_value = "/usr/local/bin/codex"
        mock_run.return_value = MagicMock(returncode=0, stdout="Code executed safely", stderr="")

        # Test with custom sandbox and approval settings
        client = CodexClient(sandbox_mode="strict", approval_policy="always")

        client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": "Execute this code"}])

        # Verify sandbox and approval were passed
        call_args = mock_run.call_args
        cmd = call_args[0][0]
        assert "--sandbox" in cmd
        assert "strict" in cmd[cmd.index("--sandbox") + 1]
        assert "--ask-for-approval" in cmd
        assert "always" in cmd[cmd.index("--ask-for-approval") + 1]

    @patch("claif_cod.client.subprocess.run")
    @patch("shutil.which")
    def test_error_handling(self, mock_which, mock_run):
        """Test error handling for CLI failures."""
        # Setup mocks
        mock_which.return_value = "/usr/local/bin/codex"
        # Make subprocess.run raise CalledProcessError
        from subprocess import CalledProcessError

        mock_run.side_effect = CalledProcessError(
            returncode=1, cmd=["/usr/local/bin/codex"], stderr="Error: Model not available"
        )

        client = CodexClient()

        # Execute and verify error
        with pytest.raises(RuntimeError) as exc_info:
            client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": "Hello"}])

        assert "Codex CLI error" in str(exc_info.value)
        assert "Model not available" in str(exc_info.value)

    @patch("shutil.which")
    @patch("pathlib.Path.exists")
    def test_cli_not_found(self, mock_exists, mock_which):
        """Test error when Codex CLI is not found."""
        mock_which.return_value = None
        mock_exists.return_value = False

        # Should raise error during initialization
        with pytest.raises(RuntimeError) as exc_info:
            CodexClient()

        assert "codex CLI not found" in str(exc_info.value)

    @patch("claif_cod.client.subprocess.run")
    @patch("shutil.which")
    def test_multi_turn_conversation(self, mock_which, mock_run):
        """Test multi-turn conversation handling."""
        # Setup mocks
        mock_which.return_value = "/usr/local/bin/codex"
        mock_run.return_value = MagicMock(returncode=0, stdout="I remember you're Alice!", stderr="")

        client = CodexClient()

        # Execute with conversation history
        client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": "Hi, my name is Alice"},
                {"role": "assistant", "content": "Hello Alice! Nice to meet you."},
                {"role": "user", "content": "What's my name?"},
            ],
        )

        # Verify the conversation was formatted correctly
        call_args = mock_run.call_args
        cmd = call_args[0][0]
        prompt = cmd[-1]

        # The current implementation only keeps the last user message
        # TODO: This might be a bug in the implementation
        assert "What's my name?" in prompt
        # Note: The conversation history is lost in current implementation

    @patch("claif_cod.client.subprocess.run")
    @patch("shutil.which")
    def test_working_directory(self, mock_which, mock_run):
        """Test working directory specification."""
        # Setup mocks
        mock_which.return_value = "/usr/local/bin/codex"
        mock_run.return_value = MagicMock(returncode=0, stdout="Working in specified directory", stderr="")

        # Test with custom working directory
        client = CodexClient(working_dir="/tmp/test-project")

        client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": "List files"}])

        # Verify working directory was passed as cwd
        call_args = mock_run.call_args
        assert call_args.kwargs.get("cwd") == "/tmp/test-project"


class TestCodexClientIntegration:
    """Integration tests that would run against real Codex CLI."""

    @pytest.mark.skip(reason="Requires Codex CLI")
    def test_real_codex_connection(self):
        """Test connection to real Codex CLI."""
        client = CodexClient()

        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": "Say 'test successful' and nothing else"}],
                max_tokens=10,
            )

            assert "test successful" in response.choices[0].message.content.lower()
        except Exception as e:
            pytest.skip(f"Codex CLI not available: {e}")

    @pytest.mark.skip(reason="Requires Codex CLI")
    def test_real_streaming(self):
        """Test streaming with real Codex CLI."""
        client = CodexClient()

        try:
            stream = client.chat.completions.create(
                model="gpt-4o", messages=[{"role": "user", "content": "Count to 3"}], stream=True, max_tokens=20
            )

            chunks = list(stream)
            assert len(chunks) > 0

            # Reconstruct message
            full_content = "".join(
                chunk.choices[0].delta.content or ""
                for chunk in chunks
                if chunk.choices and chunk.choices[0].delta.content
            )

            # Should contain numbers
            assert any(num in full_content for num in ["1", "2", "3"])
        except Exception as e:
            pytest.skip(f"Codex CLI not available: {e}")
