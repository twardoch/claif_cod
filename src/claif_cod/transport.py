"""Transport layer for Codex CLI communication."""

import json
import os
import shutil
import sys
import uuid
from pathlib import Path
from typing import AsyncIterator, Optional, List, Union, Dict, Any

import anyio
from anyio.streams.text import TextReceiveStream

from ..claif.common import get_logger, TransportError
from .types import (
    CodexOptions, 
    CodexMessage, 
    ResultMessage,
    TextBlock,
    CodeBlock,
    ErrorBlock,
    ContentBlock,
)


logger = get_logger(__name__)


class CodexTransport:
    """Transport for communicating with Codex CLI."""
    
    def __init__(self):
        self.process: Optional[anyio.Process] = None
        self.session_id = str(uuid.uuid4())
    
    async def connect(self) -> None:
        """Initialize transport (no-op for subprocess)."""
        pass
    
    async def disconnect(self) -> None:
        """Cleanup transport."""
        if self.process:
            try:
                self.process.terminate()
                await self.process.wait()
            except Exception as e:
                logger.warning(f"Error during disconnect: {e}")
            finally:
                self.process = None
    
    async def send_query(
        self, 
        prompt: str, 
        options: CodexOptions
    ) -> AsyncIterator[Union[CodexMessage, ResultMessage]]:
        """Send query to Codex and yield responses."""
        command = self._build_command(prompt, options)
        env = self._build_env()
        cwd = options.working_dir or options.cwd
        
        if options.verbose:
            logger.debug(f"Running command: {' '.join(command)}")
            logger.debug(f"Working directory: {cwd}")
        
        try:
            start_time = anyio.current_time()
            
            async with await anyio.open_process(
                command,
                env=env,
                cwd=cwd,
                stdout=anyio.subprocess.PIPE,
                stderr=anyio.subprocess.PIPE,
            ) as process:
                self.process = process
                
                # Read output line by line for streaming JSON
                stdout_stream = TextReceiveStream(process.stdout)
                stderr_lines = []
                
                # Collect stderr in background
                async def read_stderr():
                    stderr_stream = TextReceiveStream(process.stderr)
                    async for line in stderr_stream:
                        stderr_lines.append(line)
                
                async with anyio.create_task_group() as tg:
                    tg.start_soon(read_stderr)
                    
                    # Process stdout line by line
                    async for line in stdout_stream:
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
                
                # Wait for process to complete
                await process.wait()
                
                duration = anyio.current_time() - start_time
                
                # Check for errors
                if process.returncode != 0:
                    error_msg = "".join(stderr_lines) or "Unknown error"
                    yield ResultMessage(
                        error=True,
                        message=f"Codex CLI error: {error_msg}",
                        duration=duration,
                        session_id=self.session_id,
                        model=options.model,
                    )
                else:
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
    
    def _parse_message(self, data: Dict[str, Any]) -> Optional[Union[CodexMessage, ResultMessage]]:
        """Parse a JSON message into appropriate type."""
        msg_type = data.get("type")
        
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
        
        if isinstance(content, str):
            # Handle plain string content
            content_blocks = [TextBlock(text=content)]
        else:
            # Parse content blocks
            content_blocks = []
            for block in content:
                block_type = block.get("type")
                
                if block_type == "output_text":
                    content_blocks.append(TextBlock(
                        type=block_type,
                        text=block.get("text", ""),
                    ))
                elif block_type == "code":
                    content_blocks.append(CodeBlock(
                        type=block_type,
                        language=block.get("language", ""),
                        content=block.get("content", ""),
                    ))
                elif block_type == "error":
                    content_blocks.append(ErrorBlock(
                        type=block_type,
                        error_message=block.get("error_message", ""),
                    ))
                else:
                    # Unknown block type - treat as text
                    logger.warning(f"Unknown block type: {block_type}")
                    content_blocks.append(TextBlock(
                        text=str(block),
                    ))
        
        return CodexMessage(role=role, content=content_blocks)
    
    def _build_command(self, prompt: str, options: CodexOptions) -> List[str]:
        """Build command line arguments."""
        cli_path = self._find_cli()
        command = [cli_path]
        
        # Model
        command.extend(["-m", options.model])
        
        # Working directory
        if options.working_dir:
            command.extend(["-w", str(options.working_dir)])
        
        # Action mode
        command.extend(["-a", options.action_mode])
        
        # Auto-approve
        if options.auto_approve_everything:
            command.append("--auto-approve")
        
        # Full auto
        if options.full_auto:
            command.append("--full-auto")
        
        # Optional parameters
        if options.temperature is not None:
            command.extend(["--temperature", str(options.temperature)])
        
        if options.max_tokens is not None:
            command.extend(["--max-tokens", str(options.max_tokens)])
        
        if options.top_p is not None:
            command.extend(["--top-p", str(options.top_p)])
        
        # JSON output format
        command.extend(["--output-format", "json"])
        
        # Query/prompt
        command.extend(["-q", prompt])
        
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
            search_paths.extend([
                Path("C:/Program Files/Codex/codex.exe"),
                Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "codex" / "codex.exe",
            ])
        
        for path in search_paths:
            if path.exists():
                return str(path)
        
        raise TransportError(
            "Codex CLI not found. Please install it or set CODEX_CLI_PATH environment variable."
        )