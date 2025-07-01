"""Transport layer for Codex CLI communication."""

import json
import os
import shutil
import sys
import uuid
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

import anyio
from claif.common import TransportError
from loguru import logger

from claif_cod.types import CodeBlock, CodexMessage, CodexOptions, ContentBlock, ErrorBlock, ResultMessage, TextBlock


class CodexTransport:
    """Transport for communicating with Codex CLI."""

    def __init__(self):
        self.process: anyio.Process | None = None
        self.session_id = str(uuid.uuid4())

    async def connect(self) -> None:
        """Initialize transport (no-op for subprocess)."""

    async def disconnect(self) -> None:
        """Cleanup transport."""
        if self.process:
            try:
                self.process.terminate()
                await self.process.wait()
            except Exception as e:
                # Disconnect errors during cleanup are usually not critical
                logger.debug(f"Error during disconnect (expected during cleanup): {e}")
            finally:
                self.process = None

    async def send_query(self, prompt: str, options: CodexOptions) -> AsyncIterator[CodexMessage | ResultMessage]:
        """Send query to Codex and yield responses."""
        command = self._build_command(prompt, options)
        env = self._build_env()
        cwd = options.working_dir or options.cwd

        if options.verbose:
            logger.debug(f"Running command: {' '.join(command)}")
            logger.debug(f"Working directory: {cwd}")

        try:
            import asyncio

            start_time = anyio.current_time()

            # Use asyncio subprocess instead of anyio for reliability
            process = await asyncio.create_subprocess_exec(
                *command,
                env=env,
                cwd=cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            self.process = process

            # Wait for process and get all output at once
            stdout_data, stderr_data = await process.communicate()

            duration = anyio.current_time() - start_time

            # Decode the output
            stdout_output = stdout_data.decode("utf-8").strip() if stdout_data else ""
            stderr_output = stderr_data.decode("utf-8").strip() if stderr_data else ""

            # Check for errors
            if process.returncode != 0:
                error_msg = stderr_output or "Unknown error"
                yield ResultMessage(
                    error=True,
                    message=f"Codex CLI error: {error_msg}",
                    duration=duration,
                    session_id=self.session_id,
                    model=options.model,
                )
                return

            # Process output line by line for streaming JSON
            if stdout_output:
                for line in stdout_output.split("\n"):
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        data = json.loads(line)
                        message = self._parse_message(data)
                        if message:
                            yield message
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse JSON line: {e}")
                        logger.debug(f"Raw line: {line}")
                        # Treat as plain text if not JSON
                        yield CodexMessage(role="assistant", content=[TextBlock(text=line)])

            # Send success result message
            yield ResultMessage(
                duration=duration,
                session_id=self.session_id,
                model=options.model,
            )

        except Exception as e:
            logger.error(f"Transport error: {e}")
            yield ResultMessage(
                error=True,
                message=str(e),
                session_id=self.session_id,
                model=options.model,
            )

    def _parse_message(self, data: dict[str, Any]) -> CodexMessage | ResultMessage | None:
        """Parse a JSON message into appropriate type."""
        msg_type = data.get("type")

        # Skip input_text blocks (these are just echoing the user's prompt)
        if msg_type == "input_text":
            return None

        if msg_type == "result":
            return ResultMessage(
                type="result",
                duration=data.get("duration"),
                error=data.get("error", False),
                message=data.get("message"),
                session_id=data.get("session_id"),
                model=data.get("model"),
                token_count=data.get("token_count"),
            )

        # Parse as CodexMessage
        role = data.get("role", "assistant")
        content = data.get("content", [])
        content_blocks: list[ContentBlock] = []

        if isinstance(content, str):
            # Handle plain string content
            content_blocks.append(TextBlock(text=content))
        else:
            # Parse content blocks
            for block in content:
                block_type = block.get("type")

                if block_type == "output_text":
                    content_blocks.append(
                        TextBlock(
                            type=block_type,
                            text=block.get("text", ""),
                        )
                    )
                elif block_type == "code":
                    content_blocks.append(
                        CodeBlock(
                            type=block_type,
                            language=block.get("language", ""),
                            content=block.get("content", ""),
                        )
                    )
                elif block_type == "error":
                    content_blocks.append(
                        ErrorBlock(
                            type=block_type,
                            error_message=block.get("error_message", ""),
                        )
                    )
                elif block_type == "input_text":
                    # Skip input_text blocks (these are user prompts echoed back)
                    continue
                else:
                    # Unknown block type - treat as text (common during normal operation)
                    logger.debug(f"Unknown block type: {block_type}")
                    content_blocks.append(
                        TextBlock(
                            text=str(block),
                        )
                    )

        # Skip messages that only contain input_text (user prompts echoed back)
        if not content_blocks:
            return None

        return CodexMessage(role=role, content=content_blocks)

    def _build_command(self, prompt: str, options: CodexOptions) -> list[str]:
        """Build command line arguments."""
        cli_path = self._find_cli()
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
        if True:  # FIXME: hasattr(options, "quiet") and options.quiet:
            command.append("-q")

        # Add verbose/debug support
        if options.verbose:
            # Codex doesn't have a debug flag, but we can use quiet mode
            pass

        # Prompt as positional argument (not with -q flag)
        command.append(prompt)

        return command

    def _build_env(self) -> dict:
        """Build environment variables."""
        env = os.environ.copy()
        env["CODEX_SDK"] = "1"
        env["CLAIF_PROVIDER"] = "codex"
        return env

    def _find_cli(self) -> str:
        """Find Codex CLI executable."""
        # Check if specified in environment
        if cli_path := os.environ.get("CODEX_CLI_PATH"):
            if Path(cli_path).exists():
                return cli_path

        # Search in PATH
        if cli := shutil.which("codex"):
            return cli

        # Search common locations
        search_paths = [
            Path.home() / ".local" / "bin" / "codex",
            Path("/usr/local/bin/codex"),
            Path("/opt/codex/bin/codex"),
        ]

        # Add platform-specific paths
        if sys.platform == "darwin":
            search_paths.append(Path("/opt/homebrew/bin/codex"))
        elif sys.platform == "win32":
            search_paths.extend(
                [
                    Path("C:/Program Files/Codex/codex.exe"),
                    Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "codex" / "codex.exe",
                ]
            )

        for path in search_paths:
            if path.exists():
                return str(path)

        msg = "Codex CLI not found. Please install it or set CODEX_CLI_PATH environment variable."
        raise TransportError(msg)
