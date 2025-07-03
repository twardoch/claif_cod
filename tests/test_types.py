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
        assert len(block.content) == 1
        assert block.content[0].text == "print('hello')"

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

        assert len(response.content) == 1
        assert response.content[0].text == "Test response"
        assert response.role == "assistant"
        assert response.model == "o4-mini"
        assert response.usage == {"tokens": 100}
        assert response.raw_response == {"raw": "data"}

    def test_response_defaults(self):
        """Test response default values."""
        response = CodexResponse(content="Hello")
        assert len(response.content) == 1
        assert response.content[0].text == "Hello"
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
