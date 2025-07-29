# this_file: claif_cod/src/claif_cod/client.py
"""Codex client with OpenAI Responses API compatibility using new Rust-based codex CLI."""

import os
import subprocess
import time
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from openai import NOT_GIVEN, NotGiven
from openai.types import CompletionUsage
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionChunk,
    ChatCompletionMessage,
    ChatCompletionMessageParam,
)
from openai.types.chat.chat_completion import Choice
from openai.types.chat.chat_completion_chunk import Choice as ChunkChoice
from openai.types.chat.chat_completion_chunk import ChoiceDelta


class ChatCompletions:
    """Namespace for completions methods to match OpenAI client structure."""

    def __init__(self, parent: "CodexClient"):
        self.parent = parent

    def create(
        self,
        *,
        messages: list[ChatCompletionMessageParam],
        model: str = "gpt-4o",
        frequency_penalty: float | None | NotGiven = NOT_GIVEN,
        function_call: Any | None | NotGiven = NOT_GIVEN,
        functions: list[Any] | None | NotGiven = NOT_GIVEN,
        logit_bias: dict[str, int] | None | NotGiven = NOT_GIVEN,
        logprobs: bool | None | NotGiven = NOT_GIVEN,
        max_tokens: int | None | NotGiven = NOT_GIVEN,
        n: int | None | NotGiven = NOT_GIVEN,
        presence_penalty: float | None | NotGiven = NOT_GIVEN,
        response_format: Any | None | NotGiven = NOT_GIVEN,
        seed: int | None | NotGiven = NOT_GIVEN,
        stop: str | None | list[str] | NotGiven = NOT_GIVEN,
        stream: bool | None | NotGiven = NOT_GIVEN,
        temperature: float | None | NotGiven = NOT_GIVEN,
        tool_choice: Any | None | NotGiven = NOT_GIVEN,
        tools: list[Any] | None | NotGiven = NOT_GIVEN,
        top_logprobs: int | None | NotGiven = NOT_GIVEN,
        top_p: float | None | NotGiven = NOT_GIVEN,
        user: str | NotGiven = NOT_GIVEN,
        # Additional parameters
        extra_headers: Any | None | NotGiven = NOT_GIVEN,
        extra_query: Any | None | NotGiven = NOT_GIVEN,
        extra_body: Any | None | NotGiven = NOT_GIVEN,
        timeout: float | NotGiven = NOT_GIVEN,
    ) -> ChatCompletion | Iterator[ChatCompletionChunk]:
        """Create a chat completion using the new Rust-based Codex CLI.

        This method provides compatibility with OpenAI's chat.completions.create API.
        """
        # Extract the last user message as the prompt
        prompt = ""
        system_prompt = ""

        for msg in messages:
            if isinstance(msg, dict):
                role = msg["role"]
                content = msg["content"]
            else:
                role = msg.role
                content = msg.content

            if role == "system":
                system_prompt = content
            elif role == "user":
                prompt = content  # Take the last user message
            elif role == "assistant":
                # For multi-turn conversations, append assistant responses
                if prompt:
                    prompt = f"{prompt}\n\nAssistant: {content}\n\nHuman: "

        # If system prompt exists, prepend it
        if system_prompt:
            prompt = f"{system_prompt}\n\n{prompt}"

        # Build codex command
        cmd = [self.parent.codex_path, "exec"]  # Use 'exec' command for non-interactive

        # Add model if specified
        if model:
            cmd.extend(["--model", model])

        # Add temperature if specified
        if temperature is not NOT_GIVEN:
            cmd.extend(["--temperature", str(temperature)])

        # Add sandbox mode
        cmd.extend(["--sandbox", self.parent.sandbox_mode])

        # Add approval policy
        cmd.extend(["--ask-for-approval", self.parent.approval_policy])

        # Add the prompt as the last argument
        cmd.append(prompt)

        # Handle streaming
        if stream is True:
            return self._create_stream(cmd, model, timeout)
        return self._create_sync(cmd, model, timeout)

    def _create_sync(self, cmd: list[str], model: str, timeout: float | NotGiven) -> ChatCompletion:
        """Create a synchronous chat completion."""
        use_timeout = self.parent.timeout if timeout is NOT_GIVEN else timeout

        try:
            # Run codex CLI
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=use_timeout, check=True, cwd=self.parent.working_dir
            )

            # Extract response content
            content = result.stdout.strip()

            # The new Rust codex might output structured data
            # For now, assume plain text output

        except subprocess.TimeoutExpired:
            msg = f"Codex CLI timed out after {use_timeout} seconds"
            raise TimeoutError(msg)
        except subprocess.CalledProcessError as e:
            msg = f"Codex CLI error: {e.stderr}"
            raise RuntimeError(msg)
        except FileNotFoundError:
            msg = f"Codex CLI not found at {cmd[0]}. Please install the new Rust-based codex CLI."
            raise RuntimeError(msg)

        # Create ChatCompletion response
        timestamp = int(time.time())
        response_id = f"chatcmpl-{timestamp}{os.getpid()}"

        # Estimate token counts (rough approximation)
        prompt_tokens = len(cmd[-1].split()) * 2  # Rough estimate
        completion_tokens = len(content.split()) * 2  # Rough estimate

        return ChatCompletion(
            id=response_id,
            object="chat.completion",
            created=timestamp,
            model=model,
            choices=[
                Choice(
                    index=0,
                    message=ChatCompletionMessage(
                        role="assistant",
                        content=content,
                    ),
                    finish_reason="stop",
                    logprobs=None,
                )
            ],
            usage=CompletionUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
            ),
        )

    def _create_stream(self, cmd: list[str], model: str, timeout: float | NotGiven) -> Iterator[ChatCompletionChunk]:
        """Create a streaming chat completion using codex proto mode."""
        # For streaming, we might use 'codex proto' instead of 'codex exec'
        # Modify command to use proto mode
        proto_cmd = cmd.copy()
        proto_cmd[1] = "proto"  # Replace 'exec' with 'proto'

        # For now, implement a simple non-streaming fallback
        # In a real implementation, this would parse the protocol stream
        response = self._create_sync(cmd, model, timeout)

        timestamp = int(time.time())
        chunk_id = f"chatcmpl-{timestamp}{os.getpid()}"

        # Initial chunk with role
        yield ChatCompletionChunk(
            id=chunk_id,
            object="chat.completion.chunk",
            created=timestamp,
            model=model,
            choices=[
                ChunkChoice(
                    index=0,
                    delta=ChoiceDelta(role="assistant", content=""),
                    finish_reason=None,
                    logprobs=None,
                )
            ],
        )

        # Content chunk
        yield ChatCompletionChunk(
            id=chunk_id,
            object="chat.completion.chunk",
            created=timestamp,
            model=model,
            choices=[
                ChunkChoice(
                    index=0,
                    delta=ChoiceDelta(content=response.choices[0].message.content),
                    finish_reason=None,
                    logprobs=None,
                )
            ],
        )

        # Final chunk
        yield ChatCompletionChunk(
            id=chunk_id,
            object="chat.completion.chunk",
            created=timestamp,
            model=model,
            choices=[
                ChunkChoice(
                    index=0,
                    delta=ChoiceDelta(),
                    finish_reason="stop",
                    logprobs=None,
                )
            ],
        )


class Chat:
    """Namespace for chat-related methods to match OpenAI client structure."""

    def __init__(self, parent: "CodexClient"):
        self.parent = parent
        self.completions = ChatCompletions(parent)


class CodexClient:
    """Codex client compatible with OpenAI's chat completions API."""

    def __init__(
        self,
        api_key: str | None = None,
        codex_path: str | None = None,
        working_dir: str | None = None,
        timeout: float = 600.0,
        model: str | None = None,
        sandbox_mode: str | None = None,
        approval_policy: str | None = None,
    ):
        """Initialize the Codex client.

        Args:
            api_key: OpenAI API key (defaults to env var) - passed to codex CLI
            codex_path: Path to codex CLI binary (defaults to finding in PATH)
            working_dir: Working directory for codex operations
            timeout: Request timeout in seconds
            model: Default model to use (e.g., "gpt-4o", "o1-preview", "o3")
            sandbox_mode: Sandbox policy (read-only, workspace-write, danger-full-access)
            approval_policy: Approval policy (untrusted, on-failure, never)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.codex_path = codex_path or self._find_codex_cli()
        self.working_dir = working_dir or os.getcwd()
        self.timeout = timeout
        self.default_model = model or os.getenv("CODEX_DEFAULT_MODEL", "gpt-4o")
        self.sandbox_mode = sandbox_mode or os.getenv("CODEX_SANDBOX_MODE", "workspace-write")
        self.approval_policy = approval_policy or os.getenv("CODEX_APPROVAL_POLICY", "on-failure")

        # Set API key environment variable if provided
        if self.api_key:
            os.environ["OPENAI_API_KEY"] = self.api_key

        # Create namespace structure to match OpenAI client
        self.chat = Chat(self)

    def _find_codex_cli(self) -> str:
        """Find the new Rust-based codex CLI in PATH or common locations."""
        # Check if codex is in PATH
        import shutil

        codex_path = shutil.which("codex")
        if codex_path:
            return codex_path

        # Check common installation locations for Rust binaries
        common_paths = [
            "/usr/local/bin/codex",
            "/opt/homebrew/bin/codex",
            str(Path.home() / ".cargo" / "bin" / "codex"),
            str(Path.home() / ".local" / "bin" / "codex"),
            # Windows paths
            "C:\\Program Files\\Codex\\codex.exe",
            str(Path.home() / ".cargo" / "bin" / "codex.exe"),
        ]

        for path in common_paths:
            if Path(path).exists():
                return path

        # Check if old node-based codex exists and warn
        old_codex = shutil.which("codex-old") or shutil.which("codex-node")
        if old_codex:
            msg = (
                "Found old Node.js-based codex CLI, but claif_cod now requires "
                "the new Rust-based codex. Please install it from: "
                "https://github.com/openai/codex"
            )
            raise RuntimeError(msg)

        msg = (
            "New Rust-based codex CLI not found. Please install it from: "
            "https://github.com/openai/codex or specify the path explicitly."
        )
        raise RuntimeError(msg)

    # Convenience method for backward compatibility
    def create(self, **kwargs) -> ChatCompletion:
        """Create a chat completion (backward compatibility method)."""
        return self.chat.completions.create(**kwargs)
