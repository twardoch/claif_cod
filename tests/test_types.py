"""Test suite for claif_cod types."""

import pytest
from claif.common import Message, MessageRole

from claif_cod.types import (
    CodeBlock,
    CodexMessage,
    CodexOptions,
    CodexResponse,
    ErrorBlock,
    ResultMessage,
    TextBlock,
)


class TestContentBlocks:
    """Test content block types."""

    def test_text_block(self):
        """Test TextBlock creation."""
        block = TextBlock(text="Hello world")
        assert block.type == "output_text"
        assert block.text == "Hello world"

    def test_code_block(self):
        """Test CodeBlock creation."""
        block = CodeBlock(language="python", content="print('hello')")
        assert block.type == "code"
        assert block.language == "python"
        assert block.content == "print('hello')"

    def test_error_block(self):
        """Test ErrorBlock creation."""
        block = ErrorBlock(error_message="Something went wrong")
        assert block.type == "error"
        assert block.error_message == "Something went wrong"


class TestCodexOptions:
    """Test CodexOptions dataclass."""

    def test_default_options(self):
        """Test default option values."""
        options = CodexOptions()
        assert options.model == "o4-mini"
        assert options.auto_approve_everything is False
        assert options.full_auto is False
        assert options.action_mode == "review"
        assert options.working_dir is None
        assert options.cwd is None
        assert options.temperature is None
        assert options.max_tokens is None
        assert options.top_p is None
        assert options.timeout is None
        assert options.verbose is False
        assert options.exec_path is None
        assert options.images is None
        assert options.retry_count == 3
        assert options.retry_delay == 1.0
        assert options.no_retry is False

    def test_custom_options(self):
        """Test custom option values."""
        options = CodexOptions(
            model="o4",
            auto_approve_everything=True,
            full_auto=True,
            action_mode="full-auto",
            working_dir="/tmp/work",
            temperature=0.8,
            max_tokens=2000,
            timeout=120,
            verbose=True,
            images=["/img1.png", "/img2.jpg"],
            retry_count=5,
            retry_delay=2.0,
            no_retry=True,
        )

        assert options.model == "o4"
        assert options.auto_approve_everything is True
        assert options.full_auto is True
        assert options.action_mode == "full-auto"
        assert options.working_dir == "/tmp/work"
        assert options.temperature == 0.8
        assert options.max_tokens == 2000
        assert options.timeout == 120
        assert options.verbose is True
        assert options.images == ["/img1.png", "/img2.jpg"]
        assert options.retry_count == 5
        assert options.retry_delay == 2.0
        assert options.no_retry is True

    def test_cwd_alias(self):
        """Test that cwd is properly aliased to working_dir."""
        # Test cwd sets working_dir
        options1 = CodexOptions(cwd="/home/user")
        assert options1.working_dir == "/home/user"
        assert options1.cwd == "/home/user"

        # Test working_dir takes precedence
        options2 = CodexOptions(working_dir="/work", cwd="/home")
        assert options2.working_dir == "/work"
        assert options2.cwd == "/home"

        # Test both None
        options3 = CodexOptions()
        assert options3.working_dir is None
        assert options3.cwd is None


class TestCodexMessage:
    """Test CodexMessage class."""

    def test_message_creation(self):
        """Test basic message creation."""
        msg = CodexMessage(role="assistant", content=[TextBlock(text="Hello")])
        assert msg.role == "assistant"
        assert len(msg.content) == 1
        assert msg.content[0].text == "Hello"

    def test_to_claif_message_text_only(self):
        """Test conversion to Claif message with text blocks."""
        msg = CodexMessage(
            role="assistant", content=[TextBlock(text="Part 1"), TextBlock(text="Part 2"), TextBlock(text="Part 3")]
        )

        claif_msg = msg.to_claif_message()
        assert isinstance(claif_msg, Message)
        assert claif_msg.role == MessageRole.ASSISTANT
        assert len(claif_msg.content) == 1
        assert claif_msg.content[0].text == "Part 1\nPart 2\nPart 3"

    def test_to_claif_message_mixed_content(self):
        """Test conversion with mixed content types."""
        msg = CodexMessage(
            role="assistant",
            content=[
                TextBlock(text="Here's the code:"),
                CodeBlock(language="python", content="def hello():\n    print('Hi')"),
                TextBlock(text="That's it!"),
                ErrorBlock(error_message="Warning: deprecated"),
            ],
        )

        claif_msg = msg.to_claif_message()
        expected = (
            "Here's the code:\n```python\ndef hello():\n    print('Hi')\n```\nThat's it!\nError: Warning: deprecated"
        )
        assert len(claif_msg.content) == 1
        assert claif_msg.content[0].text == expected

    def test_to_claif_message_user_role(self):
        """Test conversion with user role."""
        msg = CodexMessage(role="user", content=[TextBlock(text="User input")])

        claif_msg = msg.to_claif_message()
        assert claif_msg.role == MessageRole.USER
        assert len(claif_msg.content) == 1
        assert claif_msg.content[0].text == "User input"

    def test_to_claif_message_empty_content(self):
        """Test conversion with empty content."""
        msg = CodexMessage(role="assistant", content=[])
        claif_msg = msg.to_claif_message()
        assert len(claif_msg.content) == 1
        assert claif_msg.content[0].text == ""

    def test_to_claif_message_unknown_role(self):
        """Test conversion with unknown role defaults to user."""
        msg = CodexMessage(
            role="system",  # Not assistant
            content=[TextBlock(text="System message")],
        )

        claif_msg = msg.to_claif_message()
        assert claif_msg.role == MessageRole.USER


class TestCodexResponse:
    """Test CodexResponse class."""

    def test_response_creation(self):
        """Test basic response creation."""
        response = CodexResponse(
            content="Test response",
            role="assistant",
            model="o4-mini",
            usage={"tokens": 100},
            raw_response={"raw": "data"},
        )

        assert response.content == "Test response"
        assert response.role == "assistant"
        assert response.model == "o4-mini"
        assert response.usage == {"tokens": 100}
        assert response.raw_response == {"raw": "data"}

    def test_response_defaults(self):
        """Test response default values."""
        response = CodexResponse(content="Hello")
        assert response.content == "Hello"
        assert response.role == "assistant"
        assert response.model is None
        assert response.usage is None
        assert response.raw_response is None

    def test_to_claif_message_assistant(self):
        """Test conversion to Claif message with assistant role."""
        response = CodexResponse(content="Assistant response", role="assistant")

        claif_msg = response.to_claif_message()
        assert isinstance(claif_msg, Message)
        assert claif_msg.role == MessageRole.ASSISTANT
        assert len(claif_msg.content) == 1
        assert claif_msg.content[0].text == "Assistant response"

    def test_to_claif_message_user(self):
        """Test conversion to Claif message with user role."""
        response = CodexResponse(content="User response", role="user")

        claif_msg = response.to_claif_message()
        assert claif_msg.role == MessageRole.USER
        assert len(claif_msg.content) == 1
        assert claif_msg.content[0].text == "User response"


class TestResultMessage:
    """Test ResultMessage class."""

    def test_result_message_defaults(self):
        """Test default values."""
        msg = ResultMessage()
        assert msg.type == "result"
        assert msg.duration is None
        assert msg.error is False
        assert msg.message is None
        assert msg.session_id is None
        assert msg.model is None
        assert msg.token_count is None

    def test_result_message_success(self):
        """Test success result message."""
        msg = ResultMessage(duration=1.5, session_id="test-123", model="o4-mini", token_count=150)

        assert msg.type == "result"
        assert msg.duration == 1.5
        assert msg.error is False
        assert msg.session_id == "test-123"
        assert msg.model == "o4-mini"
        assert msg.token_count == 150

    def test_result_message_error(self):
        """Test error result message."""
        msg = ResultMessage(error=True, message="API rate limit exceeded", session_id="test-456")

        assert msg.type == "result"
        assert msg.error is True
        assert msg.message == "API rate limit exceeded"
        assert msg.session_id == "test-456"


class TestContentBlockDefaults:
    """Test content block default values."""

    def test_text_block_defaults(self):
        """Test TextBlock default values."""
        block = TextBlock()
        assert block.type == "output_text"
        assert block.text == ""

    def test_code_block_defaults(self):
        """Test CodeBlock default values."""
        block = CodeBlock()
        assert block.type == "code"
        assert block.language == ""
        assert block.content == ""

    def test_error_block_defaults(self):
        """Test ErrorBlock default values."""
        block = ErrorBlock()
        assert block.type == "error"
        assert block.error_message == ""

    def test_text_block_with_custom_type(self):
        """Test TextBlock with custom type (should still be output_text)."""
        block = TextBlock(type="custom", text="Hello")
        assert block.type == "output_text"  # type is set in the field default
        assert block.text == "Hello"

    def test_code_block_with_custom_type(self):
        """Test CodeBlock with custom type (should still be code)."""
        block = CodeBlock(type="custom", language="python", content="print('test')")
        assert block.type == "code"  # type is set in the field default
        assert block.language == "python"
        assert block.content == "print('test')"

    def test_error_block_with_custom_type(self):
        """Test ErrorBlock with custom type (should still be error)."""
        block = ErrorBlock(type="custom", error_message="Error occurred")
        assert block.type == "error"  # type is set in the field default
        assert block.error_message == "Error occurred"


class TestCodexOptionsAdvanced:
    """Test advanced CodexOptions functionality."""

    def test_post_init_cwd_priority(self):
        """Test __post_init__ logic for cwd and working_dir."""
        # Test that cwd is used when working_dir is None
        options1 = CodexOptions(cwd="/home/user", working_dir=None)
        assert options1.working_dir == "/home/user"
        assert options1.cwd == "/home/user"

        # Test that working_dir is preserved when both are set
        options2 = CodexOptions(cwd="/home/user", working_dir="/work")
        assert options2.working_dir == "/work"
        assert options2.cwd == "/home/user"

        # Test that working_dir is preserved when cwd is None
        options3 = CodexOptions(cwd=None, working_dir="/work")
        assert options3.working_dir == "/work"
        assert options3.cwd is None

    def test_path_object_support(self):
        """Test CodexOptions with Path objects."""
        from pathlib import Path

        working_path = Path("/work/directory")
        cwd_path = Path("/current/directory")

        options = CodexOptions(working_dir=working_path, cwd=cwd_path)
        assert options.working_dir == working_path
        assert options.cwd == cwd_path

    def test_boolean_options(self):
        """Test all boolean options."""
        options = CodexOptions(auto_approve_everything=True, full_auto=True, verbose=True, no_retry=True)

        assert options.auto_approve_everything is True
        assert options.full_auto is True
        assert options.verbose is True
        assert options.no_retry is True

    def test_numeric_options(self):
        """Test numeric options with edge cases."""
        options = CodexOptions(temperature=0.0, max_tokens=1, top_p=1.0, timeout=0, retry_count=0, retry_delay=0.0)

        assert options.temperature == 0.0
        assert options.max_tokens == 1
        assert options.top_p == 1.0
        assert options.timeout == 0
        assert options.retry_count == 0
        assert options.retry_delay == 0.0

    def test_list_options(self):
        """Test list options."""
        images = ["/path/to/image1.png", "/path/to/image2.jpg"]
        options = CodexOptions(images=images)

        assert options.images == images
        assert len(options.images) == 2

    def test_string_options(self):
        """Test string options."""
        options = CodexOptions(model="custom-model", action_mode="interactive", exec_path="/custom/path/to/codex")

        assert options.model == "custom-model"
        assert options.action_mode == "interactive"
        assert options.exec_path == "/custom/path/to/codex"


class TestCodexMessageAdvanced:
    """Test advanced CodexMessage functionality."""

    def test_message_with_single_content_block(self):
        """Test message with single content block."""
        msg = CodexMessage(role="assistant", content=[TextBlock(text="Single block")])

        claif_msg = msg.to_claif_message()
        assert claif_msg.role == MessageRole.ASSISTANT
        assert len(claif_msg.content) == 1
        assert claif_msg.content[0].text == "Single block"

    def test_message_with_code_block_no_language(self):
        """Test message with code block that has no language."""
        msg = CodexMessage(role="assistant", content=[CodeBlock(language="", content="some code")])

        claif_msg = msg.to_claif_message()
        assert "``` \nsome code\n```" in claif_msg.content[0].text

    def test_message_with_code_block_multiline(self):
        """Test message with multi-line code block."""
        code_content = "def hello():\n    print('Hello')\n    return 'world'"
        msg = CodexMessage(role="assistant", content=[CodeBlock(language="python", content=code_content)])

        claif_msg = msg.to_claif_message()
        expected = f"```python\n{code_content}\n```"
        assert claif_msg.content[0].text == expected

    def test_message_with_error_block_empty_message(self):
        """Test message with error block that has empty message."""
        msg = CodexMessage(role="assistant", content=[ErrorBlock(error_message="")])

        claif_msg = msg.to_claif_message()
        assert claif_msg.content[0].text == "Error: "

    def test_message_with_all_block_types(self):
        """Test message with all types of content blocks."""
        msg = CodexMessage(
            role="assistant",
            content=[
                TextBlock(text="Here's the analysis:"),
                CodeBlock(language="python", content="x = 1 + 2"),
                TextBlock(text="Result calculated."),
                ErrorBlock(error_message="Warning: deprecated API"),
                CodeBlock(language="bash", content="echo 'done'"),
                TextBlock(text="Process complete."),
            ],
        )

        claif_msg = msg.to_claif_message()
        expected_parts = [
            "Here's the analysis:",
            "```python\nx = 1 + 2\n```",
            "Result calculated.",
            "Error: Warning: deprecated API",
            "```bash\necho 'done'\n```",
            "Process complete.",
        ]
        expected = "\n".join(expected_parts)
        assert claif_msg.content[0].text == expected

    def test_message_role_mapping(self):
        """Test role mapping from string to MessageRole."""
        # Test assistant role
        msg1 = CodexMessage(role="assistant", content=[TextBlock(text="Assistant")])
        assert msg1.to_claif_message().role == MessageRole.ASSISTANT

        # Test user role
        msg2 = CodexMessage(role="user", content=[TextBlock(text="User")])
        assert msg2.to_claif_message().role == MessageRole.USER

        # Test unknown role (should default to USER)
        msg3 = CodexMessage(role="system", content=[TextBlock(text="System")])
        assert msg3.to_claif_message().role == MessageRole.USER

        # Test empty role (should default to USER)
        msg4 = CodexMessage(role="", content=[TextBlock(text="Empty")])
        assert msg4.to_claif_message().role == MessageRole.USER


class TestCodexResponseAdvanced:
    """Test advanced CodexResponse functionality."""

    def test_response_with_complex_usage(self):
        """Test response with complex usage data."""
        usage_data = {"prompt_tokens": 50, "completion_tokens": 100, "total_tokens": 150, "model": "o4-mini"}

        response = CodexResponse(content="Complex response", usage=usage_data)

        assert response.usage == usage_data
        assert response.usage["prompt_tokens"] == 50
        assert response.usage["completion_tokens"] == 100

    def test_response_with_raw_response_data(self):
        """Test response with raw response data."""
        raw_data = {
            "id": "chatcmpl-123",
            "object": "chat.completion",
            "created": 1677652288,
            "choices": [{"message": {"content": "Hello"}}],
        }

        response = CodexResponse(content="Hello", raw_response=raw_data)

        assert response.raw_response == raw_data
        assert response.raw_response["id"] == "chatcmpl-123"

    def test_response_role_mapping(self):
        """Test role mapping in CodexResponse."""
        # Test assistant role
        response1 = CodexResponse(content="Assistant", role="assistant")
        assert response1.to_claif_message().role == MessageRole.ASSISTANT

        # Test user role
        response2 = CodexResponse(content="User", role="user")
        assert response2.to_claif_message().role == MessageRole.USER

        # Test unknown role defaults to USER
        response3 = CodexResponse(content="System", role="system")
        assert response3.to_claif_message().role == MessageRole.USER

    def test_response_with_empty_content(self):
        """Test response with empty content."""
        response = CodexResponse(content="")
        claif_msg = response.to_claif_message()
        assert claif_msg.content[0].text == ""

    def test_response_with_multiline_content(self):
        """Test response with multiline content."""
        content = "Line 1\nLine 2\nLine 3"
        response = CodexResponse(content=content)
        claif_msg = response.to_claif_message()
        assert claif_msg.content[0].text == content


class TestResultMessageAdvanced:
    """Test advanced ResultMessage functionality."""

    def test_result_message_with_all_fields(self):
        """Test ResultMessage with all fields set."""
        msg = ResultMessage(
            type="custom_result",
            duration=2.5,
            error=True,
            message="Custom error message",
            session_id="session-789",
            model="o4-turbo",
            token_count=250,
        )

        assert msg.type == "custom_result"
        assert msg.duration == 2.5
        assert msg.error is True
        assert msg.message == "Custom error message"
        assert msg.session_id == "session-789"
        assert msg.model == "o4-turbo"
        assert msg.token_count == 250

    def test_result_message_zero_duration(self):
        """Test ResultMessage with zero duration."""
        msg = ResultMessage(duration=0.0)
        assert msg.duration == 0.0

    def test_result_message_negative_duration(self):
        """Test ResultMessage with negative duration."""
        msg = ResultMessage(duration=-1.0)
        assert msg.duration == -1.0

    def test_result_message_zero_token_count(self):
        """Test ResultMessage with zero token count."""
        msg = ResultMessage(token_count=0)
        assert msg.token_count == 0

    def test_result_message_large_token_count(self):
        """Test ResultMessage with large token count."""
        msg = ResultMessage(token_count=1000000)
        assert msg.token_count == 1000000

    def test_result_message_empty_strings(self):
        """Test ResultMessage with empty string values."""
        msg = ResultMessage(message="", session_id="", model="")
        assert msg.message == ""
        assert msg.session_id == ""
        assert msg.model == ""

    def test_result_message_boolean_error_states(self):
        """Test ResultMessage with different boolean error states."""
        msg_success = ResultMessage(error=False)
        msg_error = ResultMessage(error=True)

        assert msg_success.error is False
        assert msg_error.error is True
