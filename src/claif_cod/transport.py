# this_file: claif_cod/src/claif_cod/transport.py
"""
Transport layer for Claif Codex CLI communication.

This module provides the `CodexTransport` class, responsible for managing
subprocess communication with the Codex CLI, including command execution,
output parsing, and retry mechanisms.
"""

import asyncio
import contextlib
import json
import os
import shlex
import signal
import subprocess
import time
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Type, Union

from claif.common import InstallError, TransportError, find_executable
from loguru import logger
from tenacity import (
    AsyncRetrying,
    RetryError,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from claif_cod.types import (
    CodeBlock,
    CodexMessage,
    CodexOptions,
    CodexResponse,
    ContentBlock,
    ErrorBlock,
    ResultMessage,
    TextBlock,
)


class CodexTransport:
    """
    Manages communication with the OpenAI Codex command-line interface (CLI).

    This class handles the execution of Codex CLI commands as a subprocess,
    manages environment variables, parses output, and implements retry logic
    for transient errors.
    """

    def __init__(self, verbose: bool = False) -> None:
        """
        Initializes the CodexTransport instance.

        Args:
            verbose: If True, enables verbose logging for debugging purposes.
        """
        self.verbose: bool = verbose
        self.process: asyncio.Process | None = None
        logger.debug("Initialized Codex transport")

    async def connect(self) -> None:
        """
        Establishes a connection for the transport.

        This method is a no-op for subprocess-based transports as the connection
        is established implicitly with each command execution.
        """
        pass

    async def disconnect(self) -> None:
        """
        Cleans up the transport by terminating any running Codex CLI subprocess.

        Ensures that the process is properly terminated and its resources are released.
        Handles process groups on Unix systems to prevent zombie processes.
        """
        if self.process:
            try:
                # Try graceful termination first
                if self.process.returncode is None:
                    self.process.terminate()

                    # Wait for graceful termination with timeout
                    try:
                        await asyncio.wait_for(self.process.wait(), timeout=5.0)
                    except asyncio.TimeoutError:
                        # Force kill if graceful termination failed
                        logger.debug("Process didn't terminate gracefully, forcing kill")
                        if os.name != "nt":
                            # Kill entire process group on Unix
                            try:
                                os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
                            except ProcessLookupError:
                                pass  # Process already dead
                        else:
                            # Just kill the process on Windows
                            self.process.kill()

                        # Wait for forced termination
                        await self.process.wait()

                self.process = None
            except Exception as e:
                logger.debug(f"Error during Codex CLI process disconnect: {e}")
                self.process = None

    async def send_query(self, prompt: str, options: CodexOptions) -> AsyncIterator[CodexMessage | ResultMessage]:
        """
        Sends a query to the Codex CLI with retry logic.

        This method constructs the CLI command, sets up the environment, and
        executes the command as an asynchronous subprocess. It includes retry
        functionality for transient errors based on the provided options.

        Args:
            prompt: The user's prompt to send to the Codex CLI.
            options: An instance of `CodexOptions` containing configuration for the query.

        Yields:
            An asynchronous iterator of `CodexMessage` or `ResultMessage` objects.
            `CodexMessage` contains content from the Codex CLI.
            `ResultMessage` indicates the status and duration of the query.
        """
        # Retrieve retry settings from options, with sensible defaults.
        retry_count: int = getattr(options, "retry_count", 3)
        retry_delay: float = getattr(options, "retry_delay", 1.0)
        no_retry: bool = getattr(options, "no_retry", False)

        # If retries are explicitly disabled or the retry count is zero/negative,
        # execute the query once without any retry mechanism.
        if no_retry or retry_count <= 0:
            try:
                async for message in self._execute_async(prompt, options):
                    yield message
            except Exception as e:
                logger.error(f"Codex query failed without retry: {e}")
                yield ResultMessage(
                    error=True,
                    message=str(e),
                    session_id="codex",  # Placeholder session_id
                )
            return

        # Define exceptions that are considered retryable. These typically indicate
        # temporary issues like network problems or service unavailability.
        retry_exceptions: tuple[type[Exception], ...] = (
            subprocess.TimeoutExpired,
            TransportError,
            ConnectionError,
            asyncio.TimeoutError,
        )

        try:
            # Configure and execute the retry mechanism.
            # `stop_after_attempt` ensures a maximum number of attempts.
            # `wait_exponential` implements a back-off strategy to avoid overwhelming the service.
            # `retry_if_exception_type` specifies which exceptions trigger a retry.
            # `reraise=False` prevents `RetryError` from being re-raised, allowing custom handling.
            async for attempt in AsyncRetrying(
                stop=stop_after_attempt(retry_count + 1),
                wait=wait_exponential(multiplier=retry_delay, min=retry_delay, max=retry_delay * 10),
                retry=retry_if_exception_type(retry_exceptions),
                reraise=False,
            ):
                with attempt:
                    logger.debug(f"Codex query attempt {attempt.retry_state.attempt_number}/{retry_count}")

                    # Execute the query and collect all results.
                    # This is necessary to check if any output was received at all.
                    results: list[CodexMessage | ResultMessage] = []
                    async for message in self._execute_async(prompt, options):
                        results.append(message)
                        yield message

                    # If no results were received after a successful command execution,
                    # it indicates an unexpected empty response, which is treated as an error.
                    if not results:
                        msg = "No response received from Codex CLI"
                        raise TransportError(msg)

                    # If execution reaches here, at least one result was received,
                    # and the query is considered successful for this attempt.
                    return

        except RetryError as e:
            # This block is executed if all retry attempts fail.
            # It extracts the last encountered error and yields a ResultMessage indicating failure.
            last_error: Exception = e.__cause__ or e
            logger.error(f"All retry attempts failed for Codex query: {last_error}")
            yield ResultMessage(
                error=True,
                message=f"Codex query failed after {retry_count} retries: {last_error!s}",
                session_id="codex",  # Placeholder session_id
            )

    async def _execute_async(
        self, prompt: str, options: CodexOptions
    ) -> AsyncIterator[CodexMessage | ResultMessage]:
        """
        Executes a Codex command asynchronously and streams its output.

        This is an internal helper method used by `send_query`. It handles
        subprocess creation, communication, and initial parsing of stdout/stderr.

        Args:
            prompt: The prompt to send to the Codex CLI.
            options: Codex options for building the command.

        Yields:
            An asynchronous iterator of `CodexMessage` or `ResultMessage` objects.
            `CodexMessage` contains parsed content from the CLI.
            `ResultMessage` indicates the status and duration of the execution.

        Raises:
            TransportError: If execution fails or times out.
        """
        command: list[str] = self._build_command(prompt, options)
        env: dict[str, str] = self._build_env()
        cwd: str | Path | None = options.working_dir or options.cwd

        if self.verbose:
            logger.debug(f"Running command: {' '.join(command)}")
            logger.debug(f"Working directory: {cwd}")

        start_time: float = time.time()
        process: asyncio.Process | None = None

        try:
            # Create the subprocess. Using `asyncio.create_subprocess_exec` for direct
            # asynchronous subprocess management, capturing stdout and stderr.
            # Use process group on Unix for better cleanup
            preexec_fn = None
            if os.name != "nt":  # Unix-like systems
                preexec_fn = os.setsid

            process = await asyncio.create_subprocess_exec(
                *command,
                env=env,
                cwd=cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                preexec_fn=preexec_fn,
            )
            self.process = process

            # Read stdout line by line to process streaming output
            while True:
                line_bytes: bytes | None = await process.stdout.readline()
                if not line_bytes:
                    break
                line: str = line_bytes.decode("utf-8").strip()
                if line:
                    try:
                        # Attempt to parse each line as JSON.
                        data: dict[str, Any] = json.loads(line)
                        # Convert parsed JSON data into appropriate CodexMessage content blocks.
                        content_blocks: list[ContentBlock] = []
                        if data.get("type") == "message" and "content" in data:
                            for block_data in data["content"]:
                                if block_data.get("type") == "output_text":
                                    content_blocks.append(TextBlock(text=block_data.get("text", "")))
                                elif block_data.get("type") == "code":
                                    content_blocks.append(
                                        CodeBlock(
                                            language=block_data.get("language", ""),
                                            content=block_data.get("content", ""),
                                        )
                                    )
                                elif block_data.get("type") == "error":
                                    content_blocks.append(ErrorBlock(error_message=block_data.get("error_message", "")))
                            yield CodexMessage(role=data.get("role", "assistant"), content=content_blocks)
                        else:
                            # If not a recognized message type, treat as plain text.
                            yield CodexMessage(role="assistant", content=[TextBlock(text=line)])
                    except json.JSONDecodeError:
                        # If a line is not valid JSON, treat it as a plain text message.
                        yield CodexMessage(role="assistant", content=[TextBlock(text=line)])

            # Wait for the process to finish with timeout
            timeout_seconds = options.timeout if options.timeout else 300  # Default 5 minutes
            try:
                returncode: int = await asyncio.wait_for(process.wait(), timeout=timeout_seconds)
            except asyncio.TimeoutError:
                # Force kill the process if it times out
                logger.warning(f"Process timed out after {timeout_seconds}s, terminating")
                if os.name != "nt":
                    with contextlib.suppress(ProcessLookupError):
                        os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                else:
                    process.kill()
                await process.wait()
                msg = f"Command timed out after {timeout_seconds}s"
                raise TransportError(msg)

            duration: float = time.time() - start_time

            if returncode != 0:
                # Read any remaining stderr output for error messages.
                stderr_output: str = (await process.stderr.read()).decode("utf-8").strip()
                error_msg: str = f"Codex command failed (exit code {returncode})"
                if stderr_output:
                    error_msg += f": {stderr_output}"
                raise TransportError(error_msg)

            # Yield a success ResultMessage after successful execution.
            yield ResultMessage(
                duration=duration,
                session_id="codex",  # Placeholder session_id
            )

        except Exception as e:
            # Catch any unexpected exceptions during execution and clean up
            if process and process.returncode is None:
                logger.debug(f"Cleaning up process due to exception: {e}")
                try:
                    # Try graceful termination first
                    process.terminate()
                    try:
                        await asyncio.wait_for(process.wait(), timeout=2.0)
                    except asyncio.TimeoutError:
                        # Force kill if needed
                        if os.name != "nt":
                            with contextlib.suppress(ProcessLookupError):
                                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                        else:
                            process.kill()
                        await process.wait()
                except Exception as cleanup_error:
                    logger.debug(f"Error during process cleanup: {cleanup_error}")

            # Re-raise the original exception
            if isinstance(e, TransportError):
                raise
            else:
                msg = f"Failed to execute Codex command: {e}"
                raise TransportError(msg) from e

    def _build_command(self, prompt: str, options: CodexOptions) -> list[str]:
        """
        Constructs the command-line argument list for the Codex CLI subprocess.

        This method intelligently handles the executable path (whether it's a simple
        command name or a full path with spaces) and appends various options
        based on the provided `CodexOptions`.

        Args:
            prompt: The user's prompt to be included in the command.
            options: An instance of `CodexOptions` containing command-line arguments.

        Returns:
            A list of strings representing the full command to be executed.
        """
        cli_path: str = self._find_cli(options.exec_path)

        # Determine how to split the command based on whether `cli_path` is a direct
        # file path or a command string that might contain arguments (e.g., "deno run").
        path_obj: Path = Path(cli_path)
        if path_obj.exists() and path_obj.is_file():
            # If it's an existing file, treat it as a single executable path.
            command: list[str] = [cli_path]
        elif " " in cli_path:
            # If it contains spaces but isn't a direct file, assume it's a command
            # with arguments and split it using shlex for proper handling of quotes.
            command = shlex.split(cli_path)
        else:
            # Otherwise, treat it as a simple command name (e.g., "codex").
            command = [cli_path]

        # Add various options to the command list based on `CodexOptions`.
        if options.model:
            command.extend(["-m", options.model])

        # Set the working directory for the Codex process.
        if options.working_dir:
            command.extend(["-w", str(options.working_dir)])

        # Set the action mode (e.g., "review", "full-auto").
        if options.action_mode:
            command.extend(["-a", options.action_mode])

        # Enable dangerously auto-approve everything if specified.
        if options.auto_approve_everything:
            command.append("--dangerously-auto-approve-everything")

        # Enable full auto mode if specified.
        if options.full_auto:
            command.append("--full-auto")

        # Add quiet mode flag for non-interactive output.
        command.append("-q")

        # Add image paths if provided.
        if options.images:
            for image_path in options.images:
                command.extend(["-i", image_path])

        # Add the main prompt as a positional argument.
        command.append(prompt)

        return command

    def _build_env(self) -> dict[str, str]:
        """
        Constructs the environment variables dictionary for the Codex CLI subprocess.

        This method ensures that the `claif` binary directory is added to the PATH
        (if available) and sets specific environment variables required by the
        Codex SDK and Claif framework.

        Returns:
            A dictionary of environment variables.
        """
        try:
            # Attempt to import and use `inject_claif_bin_to_path` from `claif.common.utils`
            # to ensure the Claif binaries are discoverable by the subprocess.
            from claif.common.utils import inject_claif_bin_to_path

            env: dict[str, str] = inject_claif_bin_to_path()
        except ImportError:
            # If `claif.common.utils` is not available, fall back to the current environment.
            env = os.environ.copy()

        # Set specific environment variables for the Codex SDK and Claif provider identification.
        env["CODEX_SDK"] = "1"
        env["CLAIF_PROVIDER"] = "codex"
        return env

    def _find_cli(self, exec_path: str | None = None) -> str:
        """
        Locates the Codex CLI executable.

        It uses a simplified 3-mode logic:
        1. If `exec_path` is provided, it attempts to use that directly.
        2. Otherwise, it searches for "codex" in standard executable locations.

        Args:
            exec_path: An optional explicit path to the Codex CLI executable.

        Returns:
            The absolute path to the Codex CLI executable.

        Raises:
            TransportError: If the Codex CLI executable cannot be found or accessed.
        """
        try:
            # Use `find_executable` from `claif.common` to locate the executable.
            return find_executable("codex", exec_path)
        except InstallError as e:
            # Wrap InstallError in TransportError for consistency within the transport layer.
            msg = f"Codex CLI executable not found: {e}"
            raise TransportError(msg) from e
