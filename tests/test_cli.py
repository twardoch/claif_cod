"""Test suite for claif_cod CLI."""

import json
from io import StringIO
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from claif.common import Message, MessageRole

from claif_cod.cli import CodexCLI, main
from claif_cod.types import CodexOptions


class TestCodexCLI:
    """Test suite for CodexCLI class."""

    @pytest.fixture
    def cli(self):
        """Create a CLI instance."""
        return CodexCLI()

    @pytest.fixture
    def mock_query(self):
        """Mock the query function."""
        with patch("claif_cod.cli.query") as mock:
            yield mock

    @pytest.fixture
    def mock_print(self):
        """Mock print functions."""
        with patch("claif_cod.cli._print") as p, patch("claif_cod.cli._print_error") as pe:
            with patch("claif_cod.cli._print_success") as ps:
                with patch("claif_cod.cli._print_warning") as pw:
                    yield {"print": p, "error": pe, "success": ps, "warning": pw}

    @pytest.mark.asyncio
    async def test_query_basic(self, cli, mock_query, mock_print):
        """Test basic query functionality."""

        # Mock query response
        async def mock_query_impl(prompt, options):
            yield Message(role=MessageRole.ASSISTANT, content="Test response")

        mock_query.side_effect = mock_query_impl

        # Test with basic prompt
        await cli.query("Hello world")

        # Verify query was called
        mock_query.assert_called_once()
        call_args = mock_query.call_args
        assert call_args[0][0] == "Hello world"
        assert isinstance(call_args[1]["options"], CodexOptions)

        # Verify output
        mock_print["print"].assert_called()

    @pytest.mark.asyncio
    async def test_query_with_all_options(self, cli, mock_query):
        """Test query with all options specified."""

        async def mock_query_impl(prompt, options):
            # Verify options
            assert options.model == "o4"
            assert options.temperature == 0.8
            assert options.max_tokens == 1000
            assert options.timeout == 120
            assert options.working_dir == "/tmp"
            assert options.action_mode == "full-auto"
            assert options.auto_approve_everything is True
            assert options.full_auto is True
            assert options.verbose is True
            yield Message(role=MessageRole.ASSISTANT, content="Response")

        mock_query.side_effect = mock_query_impl

        await cli.query(
            "Test prompt",
            model="o4",
            temperature=0.8,
            max_tokens=1000,
            timeout=120,
            working_dir="/tmp",
            action_mode="full-auto",
            auto_approve=True,
            full_auto=True,
            verbose=True,
        )

        mock_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_query_json_format(self, cli, mock_query):
        """Test query with JSON output format."""

        async def mock_query_impl(prompt, options):
            yield Message(role=MessageRole.ASSISTANT, content="Test response")

        mock_query.side_effect = mock_query_impl

        # Capture output by mocking _print
        output_data = []
        with patch("claif_cod.cli._print", side_effect=lambda x: output_data.append(x)):
            await cli.query("Test", output_format="json")

        # Find JSON output
        json_output = None
        for output in output_data:
            try:
                json_output = json.loads(output)
                break
            except:
                continue

        # Verify JSON output
        assert json_output is not None
        assert json_output["prompt"] == "Test"
        assert json_output["response"] == "Test response"
        assert json_output["model"] == "o4-mini"
        assert "timestamp" in json_output

    @pytest.mark.asyncio
    async def test_query_code_format(self, cli, mock_query):
        """Test query with code output format."""
        code_response = """```python
def hello():
    print("Hello world")
```"""

        async def mock_query_impl(prompt, options):
            yield Message(role=MessageRole.ASSISTANT, content=code_response)

        mock_query.side_effect = mock_query_impl

        with patch("claif_cod.cli._print") as mock_print:
            await cli.query("Generate hello function", output_format="code")

            # Should print code with language indicator
            mock_print.assert_called()
            calls = [str(call[0][0]) for call in mock_print.call_args_list]
            assert any("[python]" in call for call in calls)
            assert any("def hello():" in call for call in calls)

    @pytest.mark.asyncio
    async def test_query_no_response(self, cli, mock_query, mock_print):
        """Test query with no response."""

        async def mock_query_impl(prompt, options):
            # Yield nothing
            return
            yield  # Make it a generator

        mock_query.side_effect = mock_query_impl

        await cli.query("Test")

        # Should print nothing (no response handling in current implementation)
        # The CLI just processes whatever messages come through

    @pytest.mark.asyncio
    async def test_query_error_handling(self, cli, mock_query, mock_print):
        """Test query error handling."""

        async def mock_query_impl(prompt, options):
            msg = "Test error"
            raise Exception(msg)

        mock_query.side_effect = mock_query_impl

        with pytest.raises(SystemExit):
            await cli.query("Test")

        # Should print error message
        mock_print["error"].assert_called()
        call_args = mock_print["error"].call_args
        assert "Test error" in str(call_args[0][0])

    @pytest.mark.asyncio
    async def test_query_with_images(self, cli, mock_query):
        """Test query with image paths."""

        async def mock_query_impl(prompt, options):
            # Test that _process_images correctly processes image paths
            assert isinstance(options.images, list)
            assert len(options.images) > 0
            yield Message(role=MessageRole.ASSISTANT, content="Image processed")

        mock_query.side_effect = mock_query_impl

        # Mock path exists
        with patch("pathlib.Path.exists", return_value=True), patch("pathlib.Path.expanduser") as mock_expand:
            with patch("pathlib.Path.resolve"):
                mock_expand.return_value.resolve.return_value = "/resolved/path/image.png"

                await cli.query("Analyze this", images="/path/to/image.png")

    def test_health_success(self, cli):
        """Test health check when service is healthy."""
        with patch.object(cli, "_health_check", new_callable=AsyncMock) as mock_health:
            mock_health.return_value = True

            with patch("claif_cod.cli._print_success") as mock_print_success:
                cli.health()
                mock_print_success.assert_called_with("Codex service is healthy")

    def test_health_failure(self, cli):
        """Test health check when service is not healthy."""
        with patch.object(cli, "_health_check", new_callable=AsyncMock) as mock_health:
            mock_health.return_value = False

            with patch("claif_cod.cli._print_error") as mock_print_error:
                with pytest.raises(SystemExit):
                    cli.health()
                mock_print_error.assert_called_with("Codex service is not responding")

    def test_install(self, cli):
        """Test install command."""
        with patch("claif_cod.cli.install_codex") as mock_install:
            mock_install.return_value = {"installed": ["codex"], "failed": []}

            with patch("claif_cod.cli._print_success") as mock_print_success:
                cli.install()

                mock_install.assert_called_once()
                mock_print_success.assert_any_call("Codex provider installed successfully!")

    def test_install_failure(self, cli):
        """Test install command failure."""
        with patch("claif_cod.cli.install_codex") as mock_install:
            mock_install.return_value = {
                "installed": [],
                "failed": ["codex"],
                "message": "Installation failed: No permission",
            }

            with patch("claif_cod.cli._print_error") as mock_print_error:
                with pytest.raises(SystemExit):
                    cli.install()

                mock_print_error.assert_any_call("Failed to install Codex provider: Installation failed: No permission")

    def test_models(self, cli):
        """Test models command."""
        with patch("claif_cod.cli._print") as mock_print:
            cli.models()

            # Should print available models
            mock_print.assert_any_call("Available Codex Models:")
            # Check that at least one model is printed
            assert any("o4-mini" in str(call[0][0]) for call in mock_print.call_args_list)

    def test_modes(self, cli):
        """Test modes command."""
        with patch("claif_cod.cli._print") as mock_print:
            cli.modes()

            # Should print available modes
            mock_print.assert_any_call("Codex Action Modes:")
            # Check that modes are printed
            assert any("review" in str(call[0][0]) for call in mock_print.call_args_list)
            assert any("interactive" in str(call[0][0]) for call in mock_print.call_args_list)
            assert any("full-auto" in str(call[0][0]) for call in mock_print.call_args_list)

    def test_config_show(self, cli):
        """Test config show action."""
        with patch("claif_cod.cli._print") as mock_print:
            cli.config(action="show")

            # Should print configuration
            mock_print.assert_any_call("Codex Configuration:")

    def test_config_set(self, cli):
        """Test config set action."""
        with patch("claif_cod.cli._print_success") as mock_success:
            with patch("claif_cod.cli._print_warning") as mock_warning:
                cli.config(action="set", model="o4", timeout=60)

                # Should print success messages
                mock_success.assert_any_call("Set model = o4")
                mock_success.assert_any_call("Set timeout = 60")
                mock_warning.assert_called()

    def test_status(self, cli):
        """Test status command."""
        with patch("claif_cod.cli._print_success") as mock_success:
            with patch("claif_cod.cli._print_warning") as mock_warning:
                with patch("pathlib.Path.exists", return_value=True):
                    cli.status()
                    # Should show some status
                    assert mock_success.called or mock_warning.called

    @pytest.mark.asyncio
    async def test_benchmark(self, cli, mock_query):
        """Test benchmark command."""

        async def mock_query_impl(prompt, options):
            yield Message(role=MessageRole.ASSISTANT, content="4")

        mock_query.side_effect = mock_query_impl

        with patch("claif_cod.cli._print") as mock_print:
            cli.benchmark(iterations=2)

            # Should print benchmark results
            assert any("Benchmarking Codex" in str(call[0][0]) for call in mock_print.call_args_list)
            assert any("Average:" in str(call[0][0]) for call in mock_print.call_args_list)


class TestMainFunctions:
    """Test main entry point functions."""

    def test_main(self):
        """Test main function."""
        with patch("claif_cod.cli.fire.Fire") as mock_fire:
            main()
            mock_fire.assert_called_once_with(CodexCLI)

    def test_main_with_args(self):
        """Test main with command line arguments."""
        test_args = ["query", "Hello world", "--model", "o4"]

        with patch("sys.argv", ["claif-cod", *test_args]), patch("claif_cod.cli.fire.Fire") as mock_fire:
            main()
            mock_fire.assert_called_once_with(CodexCLI)
