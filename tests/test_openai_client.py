# this_file: claif_cod/tests/test_openai_client.py
"""Tests for Codex client with OpenAI compatibility."""

import subprocess
import unittest
from unittest.mock import MagicMock, Mock, patch

import pytest
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionChunk,
)

from claif_cod.client import CodexClient


class TestCodexClient(unittest.TestCase):
    """Test cases for CodexClient."""

    def setUp(self):
        """Set up test fixtures."""
        with patch.object(CodexClient, "_find_codex_cli", return_value="/usr/bin/codex"):
            self.client = CodexClient()

    @patch("shutil.which")
    def test_find_codex_cli_in_path(self, mock_which):
        """Test finding codex CLI in PATH."""
        mock_which.return_value = "/usr/local/bin/codex"
        client = CodexClient()
        assert client.codex_path == "/usr/local/bin/codex"

    @patch("shutil.which")
    @patch("pathlib.Path.exists")
    def test_find_codex_cli_common_location(self, mock_exists, mock_which):
        """Test finding codex CLI in common locations."""
        mock_which.return_value = None
        mock_exists.side_effect = [False, True, False, False]  # Second path exists
        client = CodexClient()
        assert client.codex_path == "/opt/homebrew/bin/codex"

    @patch("shutil.which")
    @patch("pathlib.Path.exists")
    def test_find_codex_cli_not_found(self, mock_exists, mock_which):
        """Test error when codex CLI not found."""
        mock_which.return_value = None
        mock_exists.return_value = False
        with pytest.raises(RuntimeError):
            CodexClient()

    def test_init_default(self):
        """Test client initialization with defaults."""
        with patch.object(CodexClient, "_find_codex_cli", return_value="/usr/bin/codex"):
            client = CodexClient()
            assert client.codex_path == "/usr/bin/codex"
            assert client.timeout == 600.0
            assert client.default_model == "o4-mini"
            assert client.sandbox_mode == "workspace-write"
            assert client.approval_policy == "on-failure"

    def test_init_custom(self):
        """Test client initialization with custom values."""
        client = CodexClient(
            codex_path="/custom/path/codex",
            working_dir="/custom/work",
            timeout=300.0,
            model="o3",
            sandbox_mode="read-only",
            approval_policy="never",
        )
        assert client.codex_path == "/custom/path/codex"
        assert client.working_dir == "/custom/work"
        assert client.timeout == 300.0
        assert client.default_model == "o3"
        assert client.sandbox_mode == "read-only"
        assert client.approval_policy == "never"

    def test_namespace_structure(self):
        """Test that the client has the correct namespace structure."""
        assert self.client.chat is not None
        assert self.client.chat.completions is not None
        assert hasattr(self.client.chat.completions, "create")

    @patch("subprocess.run")
    def test_create_sync(self, mock_run):
        """Test synchronous chat completion creation."""
        # Mock subprocess response
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Generated code response"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        # Create request
        response = self.client.chat.completions.create(
            model="o4-mini", messages=[{"role": "user", "content": "Write hello world"}]
        )

        # Verify response
        assert isinstance(response, ChatCompletion)
        assert response.model == "o4-mini"
        assert len(response.choices) == 1
        assert response.choices[0].message.content == "Generated code response"
        assert response.choices[0].message.role == "assistant"

        # Verify subprocess call
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert call_args[0] == "/usr/bin/codex"
        assert call_args[1] == "exec"
        assert "--model" in call_args
        assert "o4-mini" in call_args

    @patch("subprocess.Popen")
    def test_create_stream(self, mock_popen):
        """Test streaming chat completion creation."""
        # Mock subprocess
        mock_process = Mock()
        mock_process.stdout = iter(
            [
                '{"type": "content", "text": "Hello"}\n',
                '{"type": "content", "text": " world"}\n',
            ]
        )
        mock_process.stderr = Mock()
        mock_process.returncode = 0
        mock_process.wait.return_value = None
        mock_popen.return_value = mock_process

        # Create streaming request
        stream = self.client.chat.completions.create(
            model="o4-mini", messages=[{"role": "user", "content": "Hello"}], stream=True
        )

        # Collect chunks
        chunks = list(stream)

        # Verify chunks
        assert len(chunks) == 4  # Role chunk + 2 content chunks + finish chunk
        assert isinstance(chunks[0], ChatCompletionChunk)
        assert chunks[0].choices[0].delta.role == "assistant"
        assert chunks[1].choices[0].delta.content == "Hello"
        assert chunks[2].choices[0].delta.content == " world"
        assert chunks[3].choices[0].finish_reason == "stop"

    def test_messages_to_prompt(self):
        """Test message conversion to prompt."""
        namespace = self.client.chat.completions

        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
            {"role": "user", "content": "How are you?"},
        ]

        prompt = namespace._messages_to_prompt(messages)
        expected = "System: You are helpful\n\nUser: Hello\n\nAssistant: Hi there\n\nUser: How are you?"
        assert prompt == expected

    def test_model_name_mapping(self):
        """Test model name mapping from OpenAI to Codex."""
        namespace = self.client.chat.completions

        assert namespace._map_model_name("gpt-4") == "o4"
        assert namespace._map_model_name("gpt-3.5-turbo") == "o4-mini"
        assert namespace._map_model_name("o3") == "o3"
        assert namespace._map_model_name("custom-model") == "custom-model"

    @patch("subprocess.run")
    def test_error_handling(self, mock_run):
        """Test error handling for failed subprocess."""
        # Mock subprocess error
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Model not available"
        mock_run.return_value = mock_result

        # Should raise RuntimeError
        with pytest.raises(RuntimeError) as cm:
            self.client.chat.completions.create(model="o4-mini", messages=[{"role": "user", "content": "Test"}])

        assert "Codex error" in str(cm.value)
        assert "Model not available" in str(cm.value)

    @patch("subprocess.run")
    def test_timeout_handling(self, mock_run):
        """Test timeout handling."""
        # Mock subprocess timeout
        mock_run.side_effect = subprocess.TimeoutExpired("codex", 600)

        # Should raise TimeoutError
        with pytest.raises(TimeoutError) as cm:
            self.client.chat.completions.create(model="o4-mini", messages=[{"role": "user", "content": "Test"}])

        assert "timed out" in str(cm.value)

    def test_backward_compatibility(self):
        """Test the backward compatibility create method."""
        with patch.object(self.client.chat.completions, "create") as mock_create:
            mock_create.return_value = MagicMock(spec=ChatCompletion)

            self.client.create(model="o4-mini", messages=[{"role": "user", "content": "Hello"}])

            mock_create.assert_called_once_with(model="o4-mini", messages=[{"role": "user", "content": "Hello"}])


if __name__ == "__main__":
    unittest.main()
