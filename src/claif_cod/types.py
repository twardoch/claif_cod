"""Type definitions for CLAIF Codex wrapper."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union, List, Any

from ..claif.common import Message, MessageRole, TextBlock as ClaifTextBlock


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
    working_dir: Optional[Union[str, Path]] = None
    cwd: Optional[Union[str, Path]] = None  # Alias for working_dir
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None
    timeout: Optional[int] = None
    verbose: bool = False
    
    def __post_init__(self):
        # Handle cwd alias
        if self.cwd and not self.working_dir:
            self.working_dir = self.cwd


@dataclass
class CodexMessage:
    """A message from Codex."""
    role: str
    content: List[ContentBlock]
    
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
    duration: Optional[float] = None
    error: bool = False
    message: Optional[str] = None
    session_id: Optional[str] = None
    model: Optional[str] = None
    token_count: Optional[int] = None