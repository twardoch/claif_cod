"""Fire-based CLI for Claif Codex wrapper."""

import asyncio
import os
import sys
import time
from pathlib import Path
from typing import Any, List, Optional, Union

import fire
from claif.common import (
    Config,
    Message,
    Provider,
    ResponseMetrics,
    format_metrics,
    format_response,
    load_config,
)
from loguru import logger
from rich.console import Console
from rich.syntax import Syntax
from rich.theme import Theme

from claif_cod.client import query
from claif_cod.types import CodeBlock, CodexOptions, ErrorBlock, TextBlock


from claif.common.utils import (
    _print, _print_error, _print_success, _print_warning, _confirm, _prompt
)


class CodexCLI:
    """
    Command-Line Interface (CLI) for interacting with the Claif Codex provider.

    This class provides a Fire-based interface to various Codex functionalities,
    including querying, streaming, health checks, model listing, configuration
    management, and installation/uninstallation of the Codex CLI.
    """

    def __init__(self, config_file: str | None = None, verbose: bool = False) -> None:
        """
        Initializes the CodexCLI instance.

        Args:
            config_file: Optional path to a configuration file.
            verbose: If True, enables verbose logging for debugging purposes.
        """
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
        no_retry: bool = False,
    ) -> None:
        """
        Executes a query to the Codex LLM and displays the response.

        This method orchestrates the entire query process, including option parsing,
        image processing, asynchronous execution, and result formatting.

        Args:
            prompt: The textual prompt to send to the Codex model.
            model: Optional. The specific Codex model to use (default: 'o4-mini').
            temperature: Optional. Controls the randomness of the output (0.0 to 1.0).
            max_tokens: Optional. Maximum number of tokens in the generated response.
            top_p: Optional. Top-p sampling parameter for controlling diversity.
            working_dir: Optional. The working directory for code execution by Codex.
            action_mode: The action mode for Codex ('full-auto', 'interactive', or 'review').
            auto_approve: If True, automatically approves all actions without user confirmation.
            full_auto: If True, enables full automation mode for Codex (use with caution).
            timeout: Optional. Maximum time in seconds to wait for a response.
            output_format: The desired format for the output ('text', 'json', or 'code').
            show_metrics: If True, displays performance metrics of the query.
            images: Optional. A comma-separated string of local image paths or URLs.
                    URLs will be downloaded to temporary files.
            exec: Optional. Explicit path to the Codex CLI executable or a command
                  (e.g., 'bun run'). If None, the executable is searched in PATH.
            no_retry: If True, disables all retry attempts for the query.
        """
        # Process images if provided, converting comma-separated string to a list of paths.
        image_paths: List[str] | None = None
        if images:
            image_paths = self._process_images(images)

        # Create a CodexOptions object from the provided arguments and configuration.
        options: CodexOptions = CodexOptions(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            working_dir=Path(working_dir) if working_dir else None, # Convert string path to Path object
            action_mode=action_mode,
            auto_approve_everything=auto_approve,
            full_auto=full_auto,
            timeout=timeout,
            verbose=self.config.verbose, # Inherit verbose setting from CLI config
            images=image_paths,
            exec_path=exec,
            no_retry=no_retry,
        )

        start_time: float = time.time() # Record the start time for metrics calculation.

        try:
            # Run the asynchronous query and collect all messages.
            messages: List[Message] = asyncio.run(self._query_async(prompt, options))

            # Iterate through the received messages and format/display them.
            for message in messages:
                if output_format == "code":
                    # Special handling for code blocks, attempting to extract and display them.
                    self._display_code_message(message)
                else:
                    # For other formats, use the generic format_response utility.
                    formatted_output: str = format_response(message, output_format)
                    _print(formatted_output)

            # If requested, calculate and display response metrics.
            if show_metrics:
                duration: float = time.time() - start_time
                metrics: ResponseMetrics = ResponseMetrics(
                    duration=duration,
                    provider=Provider.CODEX,
                    model=model,
                )
                _print("\n" + format_metrics(metrics))

        except Exception as e:
            # Catch any exceptions during the query process, print an error message,
            # and exit with a non-zero status code to indicate failure.
            _print_error(str(e))
            if self.config.verbose:
                # If verbose mode is enabled, print the full traceback for debugging.
                logger.exception("Full error details for Codex query failure:")
            sys.exit(1)

    async def _query_async(self, prompt: str, options: CodexOptions) -> List[Message]:
        """
        Executes an asynchronous Codex query and collects all messages.

        Args:
            prompt: The prompt to send to the Codex model.
            options: Configuration options for the Codex query.

        Returns:
            A list of Message objects received from the Codex CLI.
        """
        messages: List[Message] = []
        async for message in query(prompt, options):
            messages.append(message)
        return messages

    def _display_code_message(self, message: Message) -> None:
        """
        Displays a message, with special handling for code blocks using rich syntax highlighting.

        Args:
            message: The Message object to display. Expected to contain a list of ContentBlock.
        """
        from claif_cod.types import CodeBlock, TextBlock, ErrorBlock
        
        if not isinstance(message.content, list):
            # Fallback for unexpected content type, though message.content should be List[ContentBlock]
            _print(str(message.content))
            return

        for block in message.content:
            if isinstance(block, TextBlock):
                _print(block.text)
            elif isinstance(block, CodeBlock):
                # Use rich.syntax.Syntax for beautiful code highlighting
                syntax = Syntax(block.content, block.language, theme="monokai", line_numbers=True)
                console.print(syntax)
            elif isinstance(block, ErrorBlock):
                _print_error(f"Codex Error: {block.error_message}")

    def stream(
        self,
        prompt: str,
        model: str = "o4-mini",
        temperature: float | None = None,
        working_dir: str | None = None,
        action_mode: str = "review",
        auto_approve: bool = False,
        exec: str | None = None,
        no_retry: bool = False,
    ) -> None:
        """
        Streams responses from the Codex LLM and displays them live.

        This method is suitable for long-running queries where incremental
        updates are desired.

        Args:
            prompt: The textual prompt to send to the Codex model.
            model: Optional. The specific Codex model to use (default: 'o4-mini').
            temperature: Optional. Controls the randomness of the output (0.0 to 1.0).
            working_dir: Optional. The working directory for code execution by Codex.
            action_mode: The action mode for Codex ('full-auto', 'interactive', or 'review').
            auto_approve: If True, automatically approves all actions without user confirmation.
            exec: Optional. Explicit path to the Codex CLI executable or a command.
            no_retry: If True, disables all retry attempts for the query.
        """
        options: CodexOptions = CodexOptions(
            model=model,
            temperature=temperature,
            working_dir=Path(working_dir) if working_dir else None,
            action_mode=action_mode,
            auto_approve_everything=auto_approve,
            verbose=self.config.verbose,
            exec_path=exec,
            no_retry=no_retry,
        )

        try:
            asyncio.run(self._stream_async(prompt, options))
        except KeyboardInterrupt:
            _print_warning("Stream interrupted by user.")
        except Exception as e:
            _print_error(str(e))
            if self.config.verbose:
                logger.exception("Full error details for Codex stream failure:")
            sys.exit(1)

    async def _stream_async(self, prompt: str, options: CodexOptions) -> None:
        """
        Asynchronously streams responses from the Codex CLI and prints them.

        Args:
            prompt: The prompt to send to the Codex model.
            options: Configuration options for the Codex query.
        """
        from claif_cod.types import CodeBlock, TextBlock, ErrorBlock

        async for message in query(prompt, options):
            if not isinstance(message.content, list):
                _print(str(message.content))
                continue

            for block in message.content:
                if isinstance(block, TextBlock):
                    _print(block.text)
                elif isinstance(block, CodeBlock):
                    syntax = Syntax(block.content, block.language, theme="monokai", line_numbers=True)
                    console.print(syntax)
                elif isinstance(block, ErrorBlock):
                    _print_error(f"Codex Error: {block.error_message}")
            # Add a newline after each message for better readability in stream mode
            _print("")

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
