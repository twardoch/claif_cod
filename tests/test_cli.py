"""Test suite for claif_cod CLI."""

import json
from unittest.mock import AsyncMock, Mock, patch

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

    @pytest.mark.asyncio
    async def test_display_code_message_with_text_block(self, cli):
        """Test _display_code_message with TextBlock."""
        from claif_cod.types import TextBlock

        message = Message(role=MessageRole.ASSISTANT, content=[TextBlock(text="Hello world")])

        with patch("claif_cod.cli._print") as mock_print:
            cli._display_code_message(message)
            mock_print.assert_called_once_with("Hello world")

    @pytest.mark.asyncio
    async def test_display_code_message_with_code_block(self, cli):
        """Test _display_code_message with CodeBlock."""
        from claif_cod.types import CodeBlock

        message = Message(role=MessageRole.ASSISTANT, content=[CodeBlock(language="python", content="print('hello')")])

        with patch("claif_cod.cli.console") as mock_console:
            cli._display_code_message(message)
            mock_console.print.assert_called_once()
            # Verify Syntax object was created
            call_args = mock_console.print.call_args[0][0]
            assert hasattr(call_args, "code")
            assert call_args.code == "print('hello')"

    @pytest.mark.asyncio
    async def test_display_code_message_with_error_block(self, cli):
        """Test _display_code_message with ErrorBlock."""
        from claif_cod.types import ErrorBlock

        message = Message(role=MessageRole.ASSISTANT, content=[ErrorBlock(error_message="Something went wrong")])

        with patch("claif_cod.cli._print_error") as mock_print_error:
            cli._display_code_message(message)
            mock_print_error.assert_called_once_with("Codex Error: Something went wrong")

    @pytest.mark.asyncio
    async def test_display_code_message_with_mixed_blocks(self, cli):
        """Test _display_code_message with mixed content blocks."""
        from claif_cod.types import CodeBlock, ErrorBlock, TextBlock

        message = Message(
            role=MessageRole.ASSISTANT,
            content=[
                TextBlock(text="Here's the code:"),
                CodeBlock(language="python", content="print('hello')"),
                ErrorBlock(error_message="Warning: deprecated function"),
            ],
        )

        with patch("claif_cod.cli._print") as mock_print:
            with patch("claif_cod.cli._print_error") as mock_print_error:
                with patch("claif_cod.cli.console") as mock_console:
                    cli._display_code_message(message)

                    mock_print.assert_called_once_with("Here's the code:")
                    mock_console.print.assert_called_once()
                    mock_print_error.assert_called_once_with("Codex Error: Warning: deprecated function")

    @pytest.mark.asyncio
    async def test_display_code_message_with_non_list_content(self, cli):
        """Test _display_code_message with non-list content (fallback)."""
        message = Message(role=MessageRole.ASSISTANT, content="Plain string content")

        with patch("claif_cod.cli._print") as mock_print:
            cli._display_code_message(message)
            mock_print.assert_called_once_with("Plain string content")

    @pytest.mark.asyncio
    async def test_stream_basic_functionality(self, cli, mock_query):
        """Test basic stream functionality."""

        async def mock_query_impl(prompt, options):
            yield Message(role=MessageRole.ASSISTANT, content="Stream response 1")
            yield Message(role=MessageRole.ASSISTANT, content="Stream response 2")

        mock_query.side_effect = mock_query_impl

        with patch("claif_cod.cli._print") as mock_print:
            await cli.stream("Test stream prompt")

            # Should print each message plus newlines
            assert mock_print.call_count >= 2
            printed_messages = [call[0][0] for call in mock_print.call_args_list if call[0][0] != ""]
            assert "Stream response 1" in printed_messages
            assert "Stream response 2" in printed_messages

    @pytest.mark.asyncio
    async def test_stream_with_options(self, cli, mock_query):
        """Test stream with various options."""

        async def mock_query_impl(prompt, options):
            assert options.model == "o4"
            assert options.temperature == 0.7
            assert options.action_mode == "full-auto"
            assert options.auto_approve_everything is True
            yield Message(role=MessageRole.ASSISTANT, content="Response")

        mock_query.side_effect = mock_query_impl

        with patch("claif_cod.cli._print"):
            await cli.stream("Test", model="o4", temperature=0.7, action_mode="full-auto", auto_approve=True)

    @pytest.mark.asyncio
    async def test_stream_keyboard_interrupt(self, cli, mock_query):
        """Test stream handling keyboard interrupt."""

        async def mock_query_impl(prompt, options):
            raise KeyboardInterrupt

        mock_query.side_effect = mock_query_impl

        with patch("claif_cod.cli._print_warning") as mock_warning:
            await cli.stream("Test")
            mock_warning.assert_called_once_with("Stream interrupted by user.")

    @pytest.mark.asyncio
    async def test_stream_exception_handling(self, cli, mock_query):
        """Test stream exception handling."""

        async def mock_query_impl(prompt, options):
            msg = "Stream error"
            raise Exception(msg)

        mock_query.side_effect = mock_query_impl

        with patch("claif_cod.cli._print_error") as mock_error:
            with pytest.raises(SystemExit):
                await cli.stream("Test")
            mock_error.assert_called_once_with("Stream error")

    @pytest.mark.asyncio
    async def test_stream_async_implementation(self, cli, mock_query):
        """Test _stream_async implementation."""
        from claif_cod.types import CodeBlock, ErrorBlock, TextBlock

        async def mock_query_impl(prompt, options):
            yield Message(role=MessageRole.ASSISTANT, content=[TextBlock(text="Text")])
            yield Message(role=MessageRole.ASSISTANT, content=[CodeBlock(language="python", content="print('code')")])
            yield Message(role=MessageRole.ASSISTANT, content=[ErrorBlock(error_message="Error")])

        mock_query.side_effect = mock_query_impl

        with patch("claif_cod.cli._print") as mock_print:
            with patch("claif_cod.cli._print_error") as mock_print_error:
                with patch("claif_cod.cli.console") as mock_console:
                    await cli._stream_async("Test", CodexOptions())

                    # Should print text, code, and error
                    assert mock_print.call_count >= 2  # Text + newlines
                    mock_console.print.assert_called_once()
                    mock_print_error.assert_called_once_with("Codex Error: Error")

    @pytest.mark.asyncio
    async def test_stream_async_with_non_list_content(self, cli, mock_query):
        """Test _stream_async with non-list content."""

        async def mock_query_impl(prompt, options):
            yield Message(role=MessageRole.ASSISTANT, content="Plain string")

        mock_query.side_effect = mock_query_impl

        with patch("claif_cod.cli._print") as mock_print:
            await cli._stream_async("Test", CodexOptions())

            # Should print the string content
            printed_calls = [call[0][0] for call in mock_print.call_args_list]
            assert "Plain string" in printed_calls

    @pytest.mark.asyncio
    async def test_health_check_implementation(self, cli, mock_query):
        """Test _health_check implementation."""

        async def mock_query_impl(prompt, options):
            # Verify health check uses proper settings
            assert options.timeout == 10
            assert options.max_tokens == 10
            assert options.action_mode == "review"
            yield Message(role=MessageRole.ASSISTANT, content="OK")

        mock_query.side_effect = mock_query_impl

        result = await cli._health_check()
        assert result is True

    @pytest.mark.asyncio
    async def test_health_check_no_response(self, cli, mock_query):
        """Test _health_check with no response."""

        async def mock_query_impl(prompt, options):
            # Yield nothing
            return
            yield  # Make it a generator

        mock_query.side_effect = mock_query_impl

        result = await cli._health_check()
        assert result is False

    @pytest.mark.asyncio
    async def test_health_check_exception(self, cli, mock_query):
        """Test _health_check with exception."""

        async def mock_query_impl(prompt, options):
            msg = "Health check failed"
            raise Exception(msg)

        mock_query.side_effect = mock_query_impl

        result = await cli._health_check()
        assert result is False

    def test_config_show_with_dict_config(self, cli):
        """Test config show with dictionary configuration."""
        # Mock config with dictionary provider config
        cli.config.providers = {"codex": {"enabled": True, "model": "o4-mini", "timeout": 300}}

        with patch("claif_cod.cli._print") as mock_print:
            with patch("claif_cod.cli.os.environ.get", return_value="/path/to/codex"):
                cli.config(action="show")

                # Should print configuration items
                print_calls = [str(call[0][0]) for call in mock_print.call_args_list]
                assert any("Codex Configuration:" in call for call in print_calls)
                assert any("enabled: True" in call for call in print_calls)
                assert any("model: o4-mini" in call for call in print_calls)
                assert any("timeout: 300" in call for call in print_calls)

    def test_config_show_with_object_config(self, cli):
        """Test config show with object configuration."""
        # Mock config with object provider config
        mock_config = Mock()
        mock_config.enabled = True
        mock_config.model = "o4"
        mock_config.timeout = 120

        cli.config.providers = {"codex": mock_config}

        with patch("claif_cod.cli._print") as mock_print:
            with patch("claif_cod.cli.os.environ.get", return_value="Not set"):
                cli.config(action="show")

                print_calls = [str(call[0][0]) for call in mock_print.call_args_list]
                assert any("enabled: True" in call for call in print_calls)
                assert any("model: o4" in call for call in print_calls)
                assert any("timeout: 120" in call for call in print_calls)

    def test_config_set_no_values(self, cli):
        """Test config set with no values provided."""
        with patch("claif_cod.cli._print_error") as mock_error:
            cli.config(action="set")
            mock_error.assert_called_once_with("No configuration values provided")

    def test_config_unknown_action(self, cli):
        """Test config with unknown action."""
        with patch("claif_cod.cli._print_error") as mock_error, patch("claif_cod.cli._print") as mock_print:
            cli.config(action="unknown")
            mock_error.assert_called_once_with("Unknown action: unknown")
            mock_print.assert_called_once_with("Available actions: show, set")

    def test_uninstall_success(self, cli):
        """Test successful uninstall."""
        with patch("claif_cod.cli.uninstall_codex") as mock_uninstall:
            mock_uninstall.return_value = {"uninstalled": True}

            with patch("claif_cod.cli._print_success") as mock_success:
                cli.uninstall()
                mock_success.assert_called_once_with("Codex provider uninstalled successfully!")

    def test_uninstall_failure(self, cli):
        """Test uninstall failure."""
        with patch("claif_cod.cli.uninstall_codex") as mock_uninstall:
            mock_uninstall.return_value = {
                "uninstalled": False,
                "message": "Uninstall failed",
                "failed": ["component1", "component2"],
            }

            with patch("claif_cod.cli._print_error") as mock_error:
                with pytest.raises(SystemExit):
                    cli.uninstall()

                mock_error.assert_any_call("Failed to uninstall Codex provider: Uninstall failed")
                mock_error.assert_any_call("Failed components: component1, component2")

    def test_status_with_bundled_executable(self, cli):
        """Test status with bundled executable present."""
        with patch("claif_cod.cli.get_install_dir") as mock_get_dir:
            mock_install_dir = Mock()
            mock_install_dir.__truediv__ = lambda self, other: Mock(exists=lambda: True)
            mock_get_dir.return_value = mock_install_dir

            with patch("claif_cod.cli.find_executable", return_value="/usr/bin/codex"):
                with patch("claif_cod.cli._print_success") as mock_success:
                    with patch("claif_cod.cli.os.environ.get", return_value="/path/bin"):
                        cli.status()

                        # Should show success messages
                        success_calls = [str(call[0][0]) for call in mock_success.call_args_list]
                        assert any("Bundled executable:" in call for call in success_calls)
                        assert any("Found executable:" in call for call in success_calls)

    def test_status_without_bundled_executable(self, cli):
        """Test status without bundled executable."""
        with patch("claif_cod.cli.get_install_dir") as mock_get_dir:
            mock_install_dir = Mock()
            mock_install_dir.__truediv__ = lambda self, other: Mock(exists=lambda: False)
            mock_get_dir.return_value = mock_install_dir

            with patch("claif_cod.cli.find_executable", side_effect=Exception("Not found")):
                with patch("claif_cod.cli._print_warning") as mock_warning:
                    with patch("claif_cod.cli._print_error") as mock_error:
                        cli.status()

                        mock_warning.assert_called()
                        mock_error.assert_called()

    @pytest.mark.asyncio
    async def test_benchmark_success(self, cli, mock_query):
        """Test successful benchmark run."""

        async def mock_query_impl(prompt, options):
            yield Message(role=MessageRole.ASSISTANT, content="Benchmark response")

        mock_query.side_effect = mock_query_impl

        with patch("claif_cod.cli._print") as mock_print:
            cli.benchmark(prompt="Test prompt", iterations=2, model="o4")

            # Should print benchmark info and results
            print_calls = [str(call[0][0]) for call in mock_print.call_args_list]
            assert any("Benchmarking Codex" in call for call in print_calls)
            assert any("Test prompt" in call for call in print_calls)
            assert any("Average:" in call for call in print_calls)
            assert any("Min:" in call for call in print_calls)
            assert any("Max:" in call for call in print_calls)

    @pytest.mark.asyncio
    async def test_benchmark_with_failures(self, cli, mock_query):
        """Test benchmark with some failures."""
        call_count = 0

        async def mock_query_impl(prompt, options):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                msg = "First iteration failed"
                raise Exception(msg)
            yield Message(role=MessageRole.ASSISTANT, content="Success")

        mock_query.side_effect = mock_query_impl

        with patch("claif_cod.cli._print"), patch("claif_cod.cli._print_error") as mock_error:
            cli.benchmark(iterations=2)

            # Should print error for failed iteration
            mock_error.assert_called()
            error_calls = [str(call[0][0]) for call in mock_error.call_args_list]
            assert any("failed" in call for call in error_calls)

    @pytest.mark.asyncio
    async def test_benchmark_all_failures(self, cli, mock_query):
        """Test benchmark when all iterations fail."""

        async def mock_query_impl(prompt, options):
            msg = "All iterations failed"
            raise Exception(msg)

        mock_query.side_effect = mock_query_impl

        with patch("claif_cod.cli._print") as mock_print, patch("claif_cod.cli._print_error"):
            cli.benchmark(iterations=2)

            # Should print "No successful iterations"
            print_calls = [str(call[0][0]) for call in mock_print.call_args_list]
            assert any("No successful iterations" in call for call in print_calls)

    @pytest.mark.asyncio
    async def test_benchmark_iteration_implementation(self, cli, mock_query):
        """Test _benchmark_iteration implementation."""

        async def mock_query_impl(prompt, options):
            yield Message(role=MessageRole.ASSISTANT, content="Benchmark result")

        mock_query.side_effect = mock_query_impl

        # Should not raise exception
        await cli._benchmark_iteration("Test", CodexOptions())

    @pytest.mark.asyncio
    async def test_benchmark_iteration_no_response(self, cli, mock_query):
        """Test _benchmark_iteration with no response."""

        async def mock_query_impl(prompt, options):
            # Yield nothing
            return
            yield  # Make it a generator

        mock_query.side_effect = mock_query_impl

        with pytest.raises(Exception, match="No response received"):
            await cli._benchmark_iteration("Test", CodexOptions())

    @pytest.mark.asyncio
    async def test_query_with_show_metrics(self, cli, mock_query):
        """Test query with show_metrics enabled."""

        async def mock_query_impl(prompt, options):
            yield Message(role=MessageRole.ASSISTANT, content="Response")

        mock_query.side_effect = mock_query_impl

        with patch("claif_cod.cli._print") as mock_print:
            cli.query("Test", show_metrics=True)

            # Should print metrics information
            print_calls = [str(call[0][0]) for call in mock_print.call_args_list]
            # Look for metrics output (contains timing info)
            assert any("Duration:" in call or "Model:" in call for call in print_calls)

    @pytest.mark.asyncio
    async def test_query_with_images_processing(self, cli, mock_query):
        """Test query with images parameter processing."""

        async def mock_query_impl(prompt, options):
            # Should have processed images
            assert options.images is not None
            assert len(options.images) > 0
            yield Message(role=MessageRole.ASSISTANT, content="Image processed")

        mock_query.side_effect = mock_query_impl

        with patch("claif_cod.cli.process_images") as mock_process:
            mock_process.return_value = ["/path/to/image1.png", "/path/to/image2.jpg"]

            cli.query("Analyze images", images="image1.png,image2.jpg")

            mock_process.assert_called_once_with("image1.png,image2.jpg")

    @pytest.mark.asyncio
    async def test_query_verbose_mode(self, cli, mock_query):
        """Test query in verbose mode."""
        cli.config.verbose = True

        async def mock_query_impl(prompt, options):
            # Should inherit verbose setting
            assert options.verbose is True
            yield Message(role=MessageRole.ASSISTANT, content="Verbose response")

        mock_query.side_effect = mock_query_impl

        with patch("claif_cod.cli._print"):
            cli.query("Test verbose")

    def test_cli_initialization_with_config_file(self):
        """Test CLI initialization with custom config file."""
        with patch("claif_cod.cli.load_config") as mock_load:
            mock_config = Mock()
            mock_config.verbose = False
            mock_load.return_value = mock_config

            cli = CodexCLI(config_file="/custom/config.yaml", verbose=True)

            mock_load.assert_called_once_with("/custom/config.yaml")
            assert cli.config.verbose is True  # Should be overridden

    def test_cli_initialization_default(self):
        """Test CLI initialization with defaults."""
        with patch("claif_cod.cli.load_config") as mock_load:
            mock_config = Mock()
            mock_config.verbose = False
            mock_load.return_value = mock_config

            cli = CodexCLI()

            mock_load.assert_called_once_with(None)
            assert cli.config.verbose is False
