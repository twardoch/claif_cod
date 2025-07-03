# this_file: src/claif_cod/types.py
"""
Type definitions for the Claif Codex provider.

This module defines the data structures used for configuring Codex queries,
representing various types of content blocks from the Codex CLI, and
encapsulating response and result metadata.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from claif.common import Message, MessageRole
from claif.common import TextBlock as ClaifTextBlock  # Alias to avoid name collision


@dataclass
class TextBlock:
    """
    Represents a block of plain text output from the Codex CLI.

    Attributes:
        type: A string indicating the type of the block, always "output_text".
        text: The actual text content.
    """

    type: str = "output_text"
    text: str = ""


@dataclass
class CodeBlock:
    """
    Represents a block of code output from the Codex CLI.

    Attributes:
        type: A string indicating the type of the block, always "code".
        language: The programming language of the code (e.g., "python", "javascript").
        content: The actual code content.
    """

    type: str = "code"
    language: str = ""
    content: str = ""


@dataclass
class ErrorBlock:
    """
    Represents an error message block from the Codex CLI.

    Attributes:
        type: A string indicating the type of the block, always "error".
        error_message: The descriptive error message.
    """

    type: str = "error"
    error_message: str = ""


# A Union type representing any possible content block from the Codex CLI.
ContentBlock = Union[TextBlock, CodeBlock, ErrorBlock]


@dataclass
class CodexOptions:
    """
    Configuration options for interacting with the Codex CLI.

    Attributes:
        model: The specific Codex model to use (e.g., 'o4-mini').
        auto_approve_everything: If True, automatically approves all actions.
        full_auto: If True, enables full-auto action mode.
        action_mode: The action mode for Codex ('review', 'full-auto', or 'interactive').
        working_dir: The working directory for the Codex CLI process.
        cwd: Alias for `working_dir` for convenience.
        temperature: Controls the randomness of the output (0.0 to 1.0).
        max_tokens: The maximum number of tokens in the generated response.
        top_p: Controls diversity via nucleus sampling.
        timeout: Maximum time in seconds to wait for a response from the CLI.
        verbose: If True, enables verbose logging for the Codex CLI process.
        exec_path: Explicit path to the Codex CLI executable. If None, it will be searched in PATH.
        images: A list of paths to image files to be included in the prompt (multimodal input).
        retry_count: Number of times to retry a failed query.
        retry_delay: Initial delay in seconds before retrying a failed query.
        no_retry: If True, disables all retry attempts for the query.
    """

    model: str = "o4-mini"
    auto_approve_everything: bool = False
    full_auto: bool = False
    action_mode: str = "review"  # "full-auto", "interactive", or "review"
    working_dir: str | Path | None = None
    cwd: str | Path | None = None  # Alias for working_dir
    temperature: float | None = None
    max_tokens: int | None = None
    top_p: float | None = None
    timeout: int | None = None
    verbose: bool = False
    exec_path: str | None = None
    images: list[str] | None = None
    retry_count: int = 3
    retry_delay: float = 1.0
    no_retry: bool = False

    def __post_init__(self) -> None:
        """
        Post-initialization hook to handle the `cwd` alias for `working_dir`.
        If `cwd` is provided and `working_dir` is not, `working_dir` is set to `cwd`.
        """
        if self.cwd and not self.working_dir:
            self.working_dir = self.cwd


@dataclass
class CodexMessage:
    """
    Represents a message received from the Codex CLI, composed of various content blocks.

    Attributes:
        role: The role of the sender (e.g., 'assistant', 'user').
        content: A list of `ContentBlock` objects, representing different types of output.
    """

    role: str
    content: list[ContentBlock]

    def to_claif_message(self) -> Message:
        """
        Converts the CodexMessage to a generic Claif Message format.

        This method iterates through the content blocks and concatenates their
        textual representation into a single string for the Claif Message.

        Returns:
            A Message object compatible with the core Claif framework.
        """
        text_parts: list[str] = []
        for block in self.content:
            if isinstance(block, TextBlock):
                text_parts.append(block.text)
            elif isinstance(block, CodeBlock):
                # Format code blocks with markdown syntax for readability.
                text_parts.append(f"``` {block.language}\n{block.content}\n```")
            elif isinstance(block, ErrorBlock):
                text_parts.append(f"Error: {block.error_message}")

        # Join all text parts to form the final content string.
        content: str = "\n".join(text_parts) if text_parts else ""

        # Map Codex's role string to Claif's MessageRole enum.
        claif_role: MessageRole = MessageRole.ASSISTANT if self.role == "assistant" else MessageRole.USER
        return Message(role=claif_role, content=content)


@dataclass
class CodexResponse:
    """
    Represents a structured response from the Codex CLI, including metadata.

    NOTE: This dataclass appears to overlap in functionality with `CodexMessage`.
    `CodexMessage` handles structured content blocks, while this class holds
    a single string `content`. Depending on the actual usage, one might be
    redundant or serve a different purpose (e.g., `CodexMessage` for streaming
    intermediate outputs, `CodexResponse` for final, summarized output).
    Further analysis is needed to confirm optimal cohesion.

    Attributes:
        content: The main textual content of the response.
        role: The role of the sender (e.g., 'assistant', 'user'). Defaults to 'assistant'.
        model: The specific Codex model that generated the response.
        usage: A dictionary containing usage statistics (e.g., token counts).
        raw_response: The raw, unparsed response from the Codex CLI, typically a dictionary.
    """

    content: str
    role: str = "assistant"
    model: str | None = None
    usage: dict[str, Any] | None = None
    raw_response: dict[str, Any] | None = None

    def to_claif_message(self) -> Message:
        """
        Converts the CodexResponse to a generic Claif Message format.

        Returns:
            A Message object compatible with the core Claif framework.
        """
        # Map Codex's role string to Claif's MessageRole enum.
        claif_role: MessageRole = MessageRole.ASSISTANT if self.role == "assistant" else MessageRole.USER
        return Message(role=claif_role, content=self.content)


@dataclass
class ResultMessage:
    """
    Represents a result message containing metadata about a query's execution.

    This is typically used to convey information about the success or failure
    of a query, its duration, and any associated error messages.

    Attributes:
        type: The type of the message, typically 'result'.
        duration: The duration of the query execution in seconds.
        error: A boolean indicating if an error occurred during the query.
        message: An optional descriptive message, especially useful for errors.
        session_id: A unique identifier for the session associated with the query.
        model: The model used for the query.
        token_count: The number of tokens processed in the query.
    """

    type: str = "result"
    duration: float | None = None
    error: bool = False
    message: str | None = None
    session_id: str | None = None
    model: str | None = None
    token_count: int | None = None
