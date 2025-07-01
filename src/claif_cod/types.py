"""Type definitions for CLAIF Codex wrapper."""

from dataclasses import dataclass
from pathlib import Path
from typing import Union

from claif.common import Message, MessageRole
from claif.common import TextBlock as ClaifTextBlock


@dataclass
class TextBlock:
    """Text output block."""

    type: str = "output_text"
    text: str = ""


@dataclass
class CodeBlock:
    """Code output block."""

    type: str = "code"
    language: str = ""
    content: str = ""


@dataclass
class ErrorBlock:
    """Error output block."""

    type: str = "error"
    error_message: str = ""


ContentBlock = Union[TextBlock, CodeBlock, ErrorBlock]


@dataclass
class CodexOptions:
    """Options for Codex queries."""

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

    def __post_init__(self):
        # Handle cwd alias
        if self.cwd and not self.working_dir:
            self.working_dir = self.cwd


@dataclass
class CodexMessage:
    """A message from Codex."""

    role: str
    content: list[ContentBlock]

    def to_claif_message(self) -> Message:
        """Convert to CLAIF message."""
        # Convert content blocks to text
        text_parts = []
        for block in self.content:
            if isinstance(block, TextBlock):
                text_parts.append(block.text)
            elif isinstance(block, CodeBlock):
                text_parts.append(f"```{block.language}\n{block.content}\n```")
            elif isinstance(block, ErrorBlock):
                text_parts.append(f"Error: {block.error_message}")

        content = "\n".join(text_parts) if text_parts else ""

        role = MessageRole.ASSISTANT if self.role == "assistant" else MessageRole.USER
        return Message(role=role, content=content)


@dataclass
class ResultMessage:
    """Result message with metadata."""

    type: str = "result"
    duration: float | None = None
    error: bool = False
    message: str | None = None
    session_id: str | None = None
    model: str | None = None
    token_count: int | None = None
