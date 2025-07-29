# this_file: claif_cod/src/claif_cod/cli.py
"""CLI interface for Codex with OpenAI-compatible API."""

import sys

import fire
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.spinner import Spinner

from claif_cod.client import CodexClient

console = Console()


class CLI:
    """Command-line interface for Codex."""

    def __init__(
        self,
        codex_path: str | None = None,
        working_dir: str | None = None,
        model: str | None = None,
        sandbox: str | None = None,
        approval: str | None = None,
    ):
        """Initialize CLI with optional parameters.

        Args:
            codex_path: Path to codex CLI binary
            working_dir: Working directory for codex operations
            model: Default model to use (e.g., "o4-mini", "o3")
            sandbox: Sandbox policy (read-only, workspace-write, danger-full-access)
            approval: Approval policy (untrusted, on-failure, never)
        """
        self._client = CodexClient(
            codex_path=codex_path,
            working_dir=working_dir,
            model=model,
            sandbox_mode=sandbox,
            approval_policy=approval,
        )

    def query(
        self,
        prompt: str,
        model: str = "o4-mini",
        stream: bool = False,
        system: str | None = None,
        json_output: bool = False,
    ):
        """Query Codex with a prompt.

        Args:
            prompt: The user prompt to send
            model: Codex model name to use
            stream: Whether to stream the response
            system: Optional system message
            json_output: Output raw JSON instead of formatted text
        """
        # Build messages
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        try:
            if stream:
                self._stream_response(messages, model, json_output)
            else:
                self._sync_response(messages, model, json_output)
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            sys.exit(1)

    def _sync_response(self, messages: list, model: str, json_output: bool):
        """Handle synchronous response."""
        with console.status("[bold green]Running Codex...", spinner="dots"):
            response = self._client.chat.completions.create(
                model=model,
                messages=messages,
            )

        if json_output:
            console.print_json(response.model_dump_json(indent=2))
        else:
            content = response.choices[0].message.content
            console.print(
                Panel(
                    Markdown(content),
                    title=f"[bold blue]Codex Response[/bold blue] (Model: {response.model})",
                    border_style="blue",
                )
            )

    def _stream_response(self, messages: list, model: str, json_output: bool):
        """Handle streaming response."""
        if json_output:
            # Stream JSON chunks
            for chunk in self._client.chat.completions.create(
                model=model,
                messages=messages,
                stream=True,
            ):
                console.print_json(chunk.model_dump_json())
        else:
            # Stream formatted text
            content = ""
            with Live(
                Panel(
                    Spinner("dots", text="Waiting for response..."),
                    title="[bold blue]Codex Response[/bold blue]",
                    border_style="blue",
                ),
                refresh_per_second=10,
                console=console,
            ) as live:
                for chunk in self._client.chat.completions.create(
                    model=model,
                    messages=messages,
                    stream=True,
                ):
                    if chunk.choices and chunk.choices[0].delta.content:
                        content += chunk.choices[0].delta.content
                        live.update(
                            Panel(
                                Markdown(content),
                                title=f"[bold blue]Codex Response[/bold blue] (Model: {model})",
                                border_style="blue",
                            )
                        )

    def exec(
        self,
        prompt: str,
        model: str = "o4-mini",
        sandbox: str | None = None,
        approval: str | None = None,
        working_dir: str | None = None,
    ):
        """Execute Codex non-interactively.

        Args:
            prompt: The prompt to execute
            model: Model to use
            sandbox: Override sandbox policy for this execution
            approval: Override approval policy for this execution
            working_dir: Override working directory for this execution
        """
        # Create a temporary client with overrides if provided
        client = CodexClient(
            codex_path=self._client.codex_path,
            working_dir=working_dir or self._client.working_dir,
            model=model,
            sandbox_mode=sandbox or self._client.sandbox_mode,
            approval_policy=approval or self._client.approval_policy,
        )

        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
            )
            content = response.choices[0].message.content
            console.print(content)
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            sys.exit(1)

    def models(self, json_output: bool = False):
        """List available Codex models.

        Args:
            json_output: Output as JSON instead of formatted table
        """
        models = [
            {"id": "o3", "name": "O3", "description": "Most capable model"},
            {"id": "o4", "name": "O4", "description": "Advanced reasoning model"},
            {"id": "o4-mini", "name": "O4 Mini", "description": "Fast reasoning model"},
        ]

        if json_output:
            console.print_json(data=models)
        else:
            from rich.table import Table

            table = Table(title="Available Codex Models")
            table.add_column("Model ID", style="cyan")
            table.add_column("Name", style="green")
            table.add_column("Description", style="yellow")

            for model in models:
                table.add_row(model["id"], model["name"], model["description"])

            console.print(table)

    def config(self):
        """Show current Codex configuration."""
        from rich.table import Table

        table = Table(title="Codex Configuration")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Codex Path", self._client.codex_path)
        table.add_row("Working Directory", self._client.working_dir)
        table.add_row("Default Model", self._client.default_model)
        table.add_row("Sandbox Mode", self._client.sandbox_mode)
        table.add_row("Approval Policy", self._client.approval_policy)
        table.add_row("Timeout", f"{self._client.timeout}s")

        console.print(table)

    def version(self):
        """Show version information."""
        from claif_cod._version import __version__

        console.print(f"claif-cod version {__version__}")


def main():
    """Main entry point for the CLI."""
    fire.Fire(CLI)
