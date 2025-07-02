"""Fire-based CLI forClaif Codex wrapper."""

import asyncio
import os
import sys
import time
from pathlib import Path

import fire
from claif.common import (
    Config,
    Provider,
    ResponseMetrics,
    format_metrics,
    format_response,
    load_config,
)
from loguru import logger

from claif_cod.client import query
from claif_cod.types import CodexOptions


def _print(message: str) -> None:
    """Simple print function for output."""


def _print_error(message: str) -> None:
    """Print error message."""


def _print_success(message: str) -> None:
    """Print success message."""


def _print_warning(message: str) -> None:
    """Print warning message."""


class CodexCLI:
    """CLAIF Codex CLI with Fire interface."""

    def __init__(self, config_file: str | None = None, verbose: bool = False):
        """Initialize CLI with optional config file."""
        self.config: Config = load_config(config_file)
        if verbose:
            self.config.verbose = True
        logger.debug("Initialized Codex CLI")

    def query(
        self,
        prompt: str,
        model: str = "o4-mini",
        temperature: float | None = None,
        max_tokens: int | None = None,
        top_p: float | None = None,
        working_dir: str | None = None,
        action_mode: str = "review",
        auto_approve: bool = False,
        full_auto: bool = False,
        timeout: int | None = None,
        output_format: str = "text",
        show_metrics: bool = False,
        images: str | None = None,
        exec: str | None = None,
    ) -> None:
        """Execute a query to Codex.

        Args:
            prompt: The prompt to send
            model: Model to use (default: o4-mini)
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens in response
            top_p: Top-p sampling parameter
            working_dir: Working directory for code execution
            action_mode: Action mode (full-auto, interactive, review)
            auto_approve: Auto-approve all actions
            full_auto: Full automation mode
            timeout: Timeout in seconds
            output_format: Output format (text, json, code)
            show_metrics: Show response metrics
            images: Comma-separated image paths or URLs
            exec: Executable path or method (bun/deno/npx)
        """
        # Process images
        image_paths = None
        if images:
            image_paths = self._process_images(images)

        options = CodexOptions(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            working_dir=Path(working_dir) if working_dir else None,
            action_mode=action_mode,
            auto_approve_everything=auto_approve,
            full_auto=full_auto,
            timeout=timeout,
            verbose=self.config.verbose,
            images=image_paths,
            exec_path=exec,
        )

        start_time = time.time()

        try:
            # Run async query
            messages = asyncio.run(self._query_async(prompt, options))

            # Format and display response
            for message in messages:
                if output_format == "code":
                    # Special handling for code blocks
                    self._display_code_message(message)
                else:
                    formatted = format_response(message, output_format)
                    _print(formatted)

            # Show metrics if requested
            if show_metrics:
                duration = time.time() - start_time
                metrics = ResponseMetrics(
                    duration=duration,
                    provider=Provider.CODEX,
                    model=model,
                )
                _print("\n" + format_metrics(metrics))

        except Exception as e:
            _print_error(str(e))
            if self.config.verbose:
                logger.exception("Full error details")
            sys.exit(1)

    async def _query_async(self, prompt: str, options: CodexOptions) -> list:
        """Execute async query and collect messages."""
        messages = []
        async for message in query(prompt, options):
            messages.append(message)
        return messages

    def _display_code_message(self, message) -> None:
        """Display message with code block highlighting."""
        content = message.content
        if isinstance(content, str):
            # Check for code blocks in markdown format
            if "```" in content:
                parts = content.split("```")
                for i, part in enumerate(parts):
                    if i % 2 == 0:
                        # Regular text
                        if part.strip():
                            _print(part.strip())
                    else:
                        # Code block
                        lines = part.strip().split("\n", 1)
                        language = lines[0] if lines else ""
                        code = lines[1] if len(lines) > 1 else part

                        # Simple code display without syntax highlighting
                        if language:
                            _print(f"[{language}]")
                        _print(code)
            else:
                _print(content)
        else:
            # Handle structured content
            _print(format_response(message))

    def stream(
        self,
        prompt: str,
        model: str = "o4-mini",
        temperature: float | None = None,
        working_dir: str | None = None,
        action_mode: str = "review",
        auto_approve: bool = False,
    ) -> None:
        """Stream responses from Codex with live display.

        Args:
            prompt: The prompt to send
            model: Model to use
            temperature: Sampling temperature (0-1)
            working_dir: Working directory for code execution
            action_mode: Action mode (full-auto, interactive, review)
            auto_approve: Auto-approve all actions
        """
        options = CodexOptions(
            model=model,
            temperature=temperature,
            working_dir=Path(working_dir) if working_dir else None,
            action_mode=action_mode,
            auto_approve_everything=auto_approve,
            verbose=self.config.verbose,
        )

        try:
            asyncio.run(self._stream_async(prompt, options))
        except KeyboardInterrupt:
            _print_warning("Stream interrupted")
        except Exception as e:
            _print_error(str(e))
            if self.config.verbose:
                logger.exception("Full error details")
            sys.exit(1)

    async def _stream_async(self, prompt: str, options: CodexOptions) -> None:
        """Stream responses with live display."""
        async for message in query(prompt, options):
            # Print content for streaming display
            if isinstance(message.content, str):
                pass
            elif isinstance(message.content, list):
                for block in message.content:
                    if hasattr(block, "text"):
                        pass

    def models(self) -> None:
        """List available Codex models."""
        _print("Available Codex Models:")

        models = [
            ("o4-mini", "Optimized for speed and efficiency (default)"),
            ("o4", "Balanced performance and capability"),
            ("o4-preview", "Latest features, may be unstable"),
            ("o3.5", "Previous generation, stable"),
        ]

        for model, desc in models:
            _print(f"  • {model}: {desc}")

    def health(self) -> None:
        """Check Codex service health."""
        try:
            _print("Checking Codex health...")

            # Simple health check
            result = asyncio.run(self._health_check())

            if result:
                _print_success("Codex service is healthy")
            else:
                _print_error("Codex service is not responding")
                sys.exit(1)

        except Exception as e:
            _print_error(f"Health check failed: {e}")
            sys.exit(1)

    async def _health_check(self) -> bool:
        """Perform health check."""
        try:
            options = CodexOptions(
                timeout=10,
                max_tokens=10,
                action_mode="review",
            )
            message_count = 0

            async for _ in query("Hello", options):
                message_count += 1
                if message_count > 0:
                    return True

            return message_count > 0
        except Exception:
            return False

    def config(self, action: str = "show", **kwargs) -> None:
        """Manage Codex configuration.

        Args:
            action: Action to perform (show, set)
            **kwargs: Configuration values for 'set' action
        """
        if action == "show":
            _print("Codex Configuration:")
            codex_config = self.config.providers.get(Provider.CODEX, {})

            if isinstance(codex_config, dict):
                for key, value in codex_config.items():
                    _print(f"  {key}: {value}")
            else:
                _print(f"  enabled: {codex_config.enabled}")
                _print(f"  model: {codex_config.model}")
                _print(f"  timeout: {codex_config.timeout}")

            # Show environment variables
            _print("\nEnvironment:")
            codex_path = os.environ.get("CODEX_CLI_PATH", "Not set")
            _print(f"  CODEX_CLI_PATH: {codex_path}")

        elif action == "set":
            if not kwargs:
                _print_error("No configuration values provided")
                return

            # Update configuration
            for key, value in kwargs.items():
                _print_success(f"Set {key} = {value}")

            msg = "Note: Configuration changes are temporary. Update config file for persistence."
            _print_warning(msg)

        else:
            _print_error(f"Unknown action: {action}")
            _print("Available actions: show, set")

    def _process_images(self, images: str) -> list[str]:
        """Process comma-separated image paths or URLs.

        Args:
            images: Comma-separated image paths or URLs

        Returns:
            List of image file paths (downloads URLs to temp files)
        """
        import tempfile
        import urllib.request
        from pathlib import Path

        image_list = [img.strip() for img in images.split(",") if img.strip()]
        processed_paths = []

        for img in image_list:
            if img.startswith(("http://", "https://")):
                # Download URL to temp file
                try:
                    suffix = Path(img).suffix or ".jpg"
                    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
                        logger.debug(f"Downloading image from {img}")
                        with urllib.request.urlopen(img) as response:
                            tmp_file.write(response.read())
                        processed_paths.append(tmp_file.name)
                        logger.debug(f"Downloaded to {tmp_file.name}")
                except Exception as e:
                    _print_error(f"Failed to download image {img}: {e}")
                    continue
            else:
                # Local file path
                path = Path(img).expanduser().resolve()
                if path.exists():
                    processed_paths.append(str(path))
                else:
                    _print_error(f"Image file not found: {img}")
                    continue

        return processed_paths

    def modes(self) -> None:
        """Show available action modes."""
        _print("Codex Action Modes:")

        modes = [
            ("review", "Review each action before execution (default)"),
            ("interactive", "Interactive mode with prompts"),
            ("full-auto", "Fully automatic execution (use with caution)"),
        ]

        for mode, desc in modes:
            _print(f"  • {mode}: {desc}")

        _print("\nTip: Use --action-mode <mode> to set the mode")

    def benchmark(
        self,
        prompt: str = "What is 2+2?",
        iterations: int = 5,
        model: str = "o4-mini",
    ) -> None:
        """Benchmark Codex performance.

        Args:
            prompt: Prompt to use for benchmarking
            iterations: Number of iterations
            model: Model to benchmark
        """
        _print("Benchmarking Codex")
        _print(f"Prompt: {prompt}")
        _print(f"Iterations: {iterations}")
        _print(f"Model: {model}")
        _print("")

        times = []
        options = CodexOptions(model=model, timeout=30)

        for i in range(iterations):
            _print(f"Running iteration {i + 1}/{iterations}...")
            start = time.time()
            try:
                asyncio.run(self._benchmark_iteration(prompt, options))
                duration = time.time() - start
                times.append(duration)
                _print(f"  Completed in {duration:.3f}s")
            except Exception as e:
                _print_error(f"Iteration {i + 1} failed: {e}")

        if times:
            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)

            _print("\nResults:")
            _print(f"Average: {avg_time:.3f}s")
            _print(f"Min: {min_time:.3f}s")
            _print(f"Max: {max_time:.3f}s")
        else:
            _print_error("No successful iterations")

    async def _benchmark_iteration(self, prompt: str, options: CodexOptions) -> None:
        """Run a single benchmark iteration."""
        message_count = 0
        async for _ in query(prompt, options):
            message_count += 1
        if message_count == 0:
            msg = "No response received"
            raise Exception(msg)

    def install(self) -> None:
        """Install Codex provider (npm package + bundling + installation).

        This will:
        1. Install bun if not available
        2. Install the latest @openai/codex package
        3. Bundle it into a standalone executable
        4. Install the executable to ~/.local/bin (or equivalent)
        """
        from claif_cod.install import install_codex

        _print("Installing Codex provider...")
        result = install_codex()

        if result["installed"]:
            _print_success("Codex provider installed successfully!")
            _print_success("You can now use the 'codex' command from anywhere")
        else:
            error_msg = result.get("message", "Unknown error")
            _print_error(f"Failed to install Codex provider: {error_msg}")
            if result.get("failed"):
                failed_str = ", ".join(result["failed"])
                _print_error(f"Failed components: {failed_str}")
            sys.exit(1)

    def uninstall(self) -> None:
        """Uninstall Codex provider (remove bundled executable).

        This will remove the bundled Codex executable from the install
        directory.
        """
        from claif_cod.install import uninstall_codex

        _print("Uninstalling Codex provider...")
        result = uninstall_codex()

        if result["uninstalled"]:
            _print_success("Codex provider uninstalled successfully!")
        else:
            error_msg = result.get("message", "Unknown error")
            _print_error(f"Failed to uninstall Codex provider: {error_msg}")
            if result.get("failed"):
                failed_str = ", ".join(result["failed"])
                _print_error(f"Failed components: {failed_str}")
            sys.exit(1)

    def status(self) -> None:
        """Show Codex provider installation status."""
        from claif.common.install import find_executable, get_install_dir

        _print("Codex Provider Status")
        _print("")

        # Check bundled executable
        install_dir = get_install_dir()
        bundled_path = install_dir / "codex"

        if bundled_path.exists():
            _print_success(f"Bundled executable: {bundled_path}")
        else:
            _print_warning("Bundled executable: Not installed")

        # Check external executable
        try:
            external_path = find_executable("codex")
            _print_success(f"Found executable: {external_path}")
        except Exception:
            _print_error("No external codex executable found")

        # Show install directory in PATH status
        path_env = os.environ.get("PATH", "")
        if str(install_dir) in path_env:
            _print_success("Install directory in PATH")
        else:
            _print_warning(f"Install directory not in PATH: {install_dir}")
            path_cmd = 'export PATH="$HOME/.local/bin:$PATH"'
            _print(f"  Add to PATH with: {path_cmd}")


def main():
    """Main entry point for Fire CLI."""
    fire.Fire(CodexCLI)
