"""Transport layer for Claif Codex CLI communication."""

import json
import os
import shlex
import subprocess
from pathlib import Path

from claif.common import InstallError, TransportError, find_executable
from loguru import logger
from tenacity import (
    AsyncRetrying,
    RetryError,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from claif_cod.types import CodexOptions, CodexResponse


class CodexTransport:
    """Transport for communicating with Codex CLI."""

    def __init__(self, verbose: bool = False):
        """Initialize transport.

        Args:
            verbose: Enable verbose logging
        """
        self.verbose = verbose
        logger.debug("Initialized Codex transport")

    async def connect(self) -> None:
        """Initialize transport (no-op for subprocess)."""

    async def disconnect(self) -> None:
        """Cleanup transport (no-op for subprocess)."""

    async def send_query(self, prompt: str, options: CodexOptions):
        """Send query to Codex CLI with retry logic.

        This is an async wrapper around the synchronous execute method
        with added retry functionality for transient errors.
        """
        from claif_cod.types import CodexMessage, ResultMessage, TextBlock
        
        # Get retry settings from options or use defaults
        retry_count = getattr(options, "retry_count", 3)
        retry_delay = getattr(options, "retry_delay", 1.0)
        no_retry = getattr(options, "no_retry", False)
        
        # If retry is disabled, execute once without retry
        if no_retry or retry_count <= 0:
            try:
                response = self.execute(prompt, options)
                yield CodexMessage(
                    role=response.role,
                    content=[TextBlock(text=response.content)],
                )
                yield ResultMessage(
                    duration=0.0,
                    session_id="codex",
                )
            except Exception as e:
                yield ResultMessage(
                    error=True,
                    message=str(e),
                    session_id="codex",
                )
            return
        
        # Define retry exceptions
        retry_exceptions = (
            subprocess.TimeoutExpired,
            TransportError,
            ConnectionError,
            TimeoutError,
        )
        
        try:
            async for attempt in AsyncRetrying(
                stop=stop_after_attempt(retry_count + 1),
                wait=wait_exponential(multiplier=retry_delay, min=retry_delay, max=retry_delay * 10),
                retry=retry_if_exception_type(retry_exceptions),
                reraise=False,
            ):
                with attempt:
                    logger.debug(f"Codex query attempt {attempt.retry_state.attempt_number}/{retry_count}")
                    
                    # Check if the error is retryable
                    try:
                        response = self.execute(prompt, options)
                    except TransportError as e:
                        error_msg = str(e).lower()
                        retryable_indicators = [
                            "timeout", "connection", "network", "quota", "exhausted",
                            "rate limit", "too many requests", "503", "502", "429"
                        ]
                        if any(indicator in error_msg for indicator in retryable_indicators):
                            logger.warning(f"Retryable error: {e}")
                            raise
                        else:
                            # Non-retryable error
                            yield ResultMessage(
                                error=True,
                                message=str(e),
                                session_id="codex",
                            )
                            return
                    
                    # Success - yield messages
                    yield CodexMessage(
                        role=response.role,
                        content=[TextBlock(text=response.content)],
                    )
                    yield ResultMessage(
                        duration=0.0,
                        session_id="codex",
                    )
                    return
                    
        except RetryError as e:
            last_error = e.__cause__ or e
            logger.error(f"All retry attempts failed for Codex query: {last_error}")
            yield ResultMessage(
                error=True,
                message=f"Codex query failed after {retry_count} retries: {last_error!s}",
                session_id="codex",
            )

    def execute(self, prompt: str, options: CodexOptions) -> CodexResponse:
        """Execute a Codex command.

        Args:
            prompt: The prompt to send
            options: Codex options

        Returns:
            CodexResponse containing the result

        Raises:
            TransportError: If execution fails
        """
        command = self._build_command(prompt, options)
        env = self._build_env()
        cwd = options.working_dir or options.cwd

        if self.verbose:
            logger.debug(f"Running command: {' '.join(command)}")
            logger.debug(f"Working directory: {cwd}")

        try:
            result = subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
                env=env,
                timeout=options.timeout,
                cwd=cwd,
            )

            if result.returncode != 0:
                error_msg = f"Codex command failed (exit code {result.returncode})"
                if result.stderr:
                    error_msg += f": {result.stderr}"
                raise TransportError(error_msg)

            # Parse response - Codex CLI outputs JSONL format
            content = ""
            role = "assistant"
            raw_response = None

            if result.stdout.strip():
                try:
                    # Parse each line as separate JSON
                    for line in result.stdout.strip().split("\n"):
                        if line.strip():
                            data = json.loads(line)

                            # Look for assistant message with content
                            if (
                                data.get("type") == "message"
                                and data.get("role") == "assistant"
                                and data.get("status") == "completed"
                            ):
                                # Extract text from content blocks
                                content_blocks = data.get("content", [])
                                text_parts = []
                                for block in content_blocks:
                                    if block.get("type") == "output_text":
                                        text_parts.append(block.get("text", ""))

                                content = "\n".join(text_parts)
                                role = data.get("role", "assistant")
                                raw_response = data
                                break

                except json.JSONDecodeError:
                    # Fallback for non-JSON output
                    content = result.stdout
                    raw_response = {"raw_output": result.stdout}

            if not content:
                content = result.stdout or "No response received"

            return CodexResponse(
                content=content,
                role=role,
                model=options.model,
                usage={},
                raw_response=raw_response,
            )

        except subprocess.TimeoutExpired as e:
            msg = f"Codex command timed out after {options.timeout}s"
            raise TransportError(msg) from e
        except Exception as e:
            msg = f"Failed to execute Codex command: {e}"
            raise TransportError(msg) from e

    def _build_command(self, prompt: str, options: CodexOptions) -> list[str]:
        """Build command line arguments."""
        exec_path = getattr(options, "exec_path", None)
        cli_path = self._find_cli(exec_path)

        # Check if this is a single file path (possibly with spaces) or a command with arguments
        path_obj = Path(cli_path)
        if path_obj.exists():
            # This is a file path, treat as single argument even if it has spaces
            command = [cli_path]
        elif " " in cli_path:
            # This is a command with arguments (e.g., "deno run script.js")
            command = shlex.split(cli_path)
        else:
            # Simple command name
            command = [cli_path]

        # Model
        if options.model:
            command.extend(["-m", options.model])

        # Working directory (writable root for sandbox)
        if options.working_dir:
            command.extend(["-w", str(options.working_dir)])

        # Approval mode
        if options.action_mode:
            command.extend(["-a", options.action_mode])

        # Auto-approve everything (dangerous)
        if options.auto_approve_everything:
            command.append("--dangerously-auto-approve-everything")

        # Full auto mode
        if options.full_auto:
            command.append("--full-auto")

        # Quiet mode for non-interactive output
        command.append("-q")

        # Add images if provided (Codex supports -i flag)
        if options.images:
            for image_path in options.images:
                command.extend(["-i", image_path])

        # Prompt as positional argument
        command.append(prompt)

        return command

    def _build_env(self) -> dict:
        """Build environment variables."""
        try:
            from claif.common.utils import inject_claif_bin_to_path

            env = inject_claif_bin_to_path()
        except ImportError:
            env = os.environ.copy()

        env["CODEX_SDK"] = "1"
        env["CLAIF_PROVIDER"] = "codex"
        return env

    def _find_cli(self, exec_path: str | None = None) -> str:
        """Find Codex CLI executable using simplified 3-mode logic.

        Args:
            exec_path: Optional explicit path provided by user

        Returns:
            Path to the executable

        Raises:
            TransportError: If executable cannot be found
        """
        try:
            return find_executable("codex", exec_path)
        except InstallError as e:
            raise TransportError(str(e)) from e
