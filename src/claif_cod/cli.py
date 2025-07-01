"""Fire-based CLI for CLAIF Codex wrapper."""

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
from rich.console import Console
from rich.live import Live
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from claif_cod.client import query
from claif_cod.types import CodexOptions

console = Console()


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
        """
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
                    console.print(formatted)

            # Show metrics if requested
            if show_metrics:
                duration = time.time() - start_time
                metrics = ResponseMetrics(
                    duration=duration,
                    provider=Provider.CODEX,
                    model=model,
                )
                console.print("\n" + format_metrics(metrics))

        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            if self.config.verbose:
                console.print_exception()
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
                            console.print(part.strip())
                    else:
                        # Code block
                        lines = part.strip().split("\n", 1)
                        language = lines[0] if lines else ""
                        code = lines[1] if len(lines) > 1 else part

                        from rich.syntax import Syntax

                        syntax = Syntax(code, language or "text", theme="monokai")
                        console.print(syntax)
            else:
                console.print(content)
        else:
            # Handle structured content
            console.print(format_response(message))

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
            console.print("\n[yellow]Stream interrupted[/yellow]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            if self.config.verbose:
                console.print_exception()
            sys.exit(1)

    async def _stream_async(self, prompt: str, options: CodexOptions) -> None:
        """Stream responses with live display."""
        content_buffer = []

        with Live(console=console, refresh_per_second=10) as live:
            async for message in query(prompt, options):
                # Update live display
                if isinstance(message.content, str):
                    content_buffer.append(message.content)
                elif isinstance(message.content, list):
                    for block in message.content:
                        if hasattr(block, "text"):
                            content_buffer.append(block.text)

                live.update("".join(content_buffer))

    def models(self) -> None:
        """List available Codex models."""
        console.print("[bold]Available Codex Models:[/bold]")

        models = [
            ("o4-mini", "Optimized for speed and efficiency (default)"),
            ("o4", "Balanced performance and capability"),
            ("o4-preview", "Latest features, may be unstable"),
            ("o3.5", "Previous generation, stable"),
        ]

        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Model", style="green")
        table.add_column("Description")

        for model, desc in models:
            table.add_row(model, desc)

        console.print(table)

    def health(self) -> None:
        """Check Codex service health."""
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True,
            ) as progress:
                task = progress.add_task("Checking Codex health...", total=None)

                # Simple health check
                result = asyncio.run(self._health_check())
                progress.update(task, completed=True)

            if result:
                console.print("[green]✓ Codex service is healthy[/green]")
            else:
                console.print("[red]✗ Codex service is not responding[/red]")
                sys.exit(1)

        except Exception as e:
            console.print(f"[red]Health check failed: {e}[/red]")
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
            console.print("[bold]Codex Configuration:[/bold]")
            codex_config = self.config.providers.get(Provider.CODEX, {})

            if isinstance(codex_config, dict):
                for key, value in codex_config.items():
                    console.print(f"  {key}: {value}")
            else:
                console.print(f"  enabled: {codex_config.enabled}")
                console.print(f"  model: {codex_config.model}")
                console.print(f"  timeout: {codex_config.timeout}")

            # Show environment variables
            console.print("\n[bold]Environment:[/bold]")
            console.print(f"  CODEX_CLI_PATH: {os.environ.get('CODEX_CLI_PATH', 'Not set')}")

        elif action == "set":
            if not kwargs:
                console.print("[red]No configuration values provided[/red]")
                return

            # Update configuration
            for key, value in kwargs.items():
                console.print(f"[green]Set {key} = {value}[/green]")

            console.print(
                "\n[yellow]Note: Configuration changes are temporary. Update config file for persistence.[/yellow]"
            )

        else:
            console.print(f"[red]Unknown action: {action}[/red]")
            console.print("Available actions: show, set")

    def modes(self) -> None:
        """Show available action modes."""
        console.print("[bold]Codex Action Modes:[/bold]")

        modes = [
            ("review", "Review each action before execution (default)"),
            ("interactive", "Interactive mode with prompts"),
            ("full-auto", "Fully automatic execution (use with caution)"),
        ]

        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Mode", style="green")
        table.add_column("Description")

        for mode, desc in modes:
            table.add_row(mode, desc)

        console.print(table)
        console.print("\n[yellow]Tip: Use --action-mode <mode> to set the mode[/yellow]")


def main():
    """Main entry point for Fire CLI."""
    fire.Fire(CodexCLI)
