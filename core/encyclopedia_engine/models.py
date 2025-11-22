"""Encyclopedia models"""
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel


class BlockType(str, Enum):
    """Content block types"""
    TEXT = "text"
    IMAGE = "image"
    HINT = "hint"
    WARNING = "warning"
    EXAMPLE = "example"
    QUOTE = "quote"


class ContentBlock(BaseModel):
    """Single content block in a page"""
    type: BlockType
    value: str
    caption: Optional[str] = None


class Page(BaseModel):
    """Encyclopedia page"""
    id: str
    title: str
    roles: List[str]  # List of roles that can access this page
    blocks: List[ContentBlock]
    description: Optional[str] = None
    tags: Optional[List[str]] = None
