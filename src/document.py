"""
Document data models for AI Document Preprocessing Parser.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class DocumentType(Enum):
    """Supported document types."""

    PDF = "pdf"
    DOCX = "docx"
    PPTX = "pptx"
    XLSX = "xlsx"
    HTML = "html"
    MARKDOWN = "markdown"
    IMAGE = "image"
    TEXT = "text"
    UNKNOWN = "unknown"

    @classmethod
    def from_extension(cls, ext: str) -> "DocumentType":
        """Get document type from file extension."""
        ext = ext.lower().lstrip(".")
        mapping = {
            "pdf": cls.PDF,
            "docx": cls.DOCX,
            "doc": cls.DOCX,
            "pptx": cls.PPTX,
            "ppt": cls.PPTX,
            "xlsx": cls.XLSX,
            "xls": cls.XLSX,
            "html": cls.HTML,
            "htm": cls.HTML,
            "md": cls.MARKDOWN,
            "markdown": cls.MARKDOWN,
            "png": cls.IMAGE,
            "jpg": cls.IMAGE,
            "jpeg": cls.IMAGE,
            "gif": cls.IMAGE,
            "bmp": cls.IMAGE,
            "tiff": cls.IMAGE,
            "txt": cls.TEXT,
        }
        return mapping.get(ext, cls.UNKNOWN)


@dataclass
class DocumentMetadata:
    """Document metadata container."""

    title: Optional[str] = None
    author: Optional[str] = None
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
    page_count: Optional[int] = None
    word_count: Optional[int] = None
    char_count: Optional[int] = None
    language: Optional[str] = None
    source_path: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    encoding: Optional[str] = None
    custom: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary."""
        result = {}
        for key, value in self.__dict__.items():
            if value is not None:
                if isinstance(value, datetime):
                    result[key] = value.isoformat()
                else:
                    result[key] = value
        return result


@dataclass
class TextChunk:
    """A chunk of text from a document."""

    content: str
    index: int
    start_char: int
    end_char: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    page_number: Optional[int] = None
    section: Optional[str] = None
    embedding: Optional[List[float]] = None

    @property
    def length(self) -> int:
        """Get the length of the chunk content."""
        return len(self.content)

    def to_dict(self) -> Dict[str, Any]:
        """Convert chunk to dictionary."""
        return {
            "content": self.content,
            "index": self.index,
            "start_char": self.start_char,
            "end_char": self.end_char,
            "length": self.length,
            "metadata": self.metadata,
            "page_number": self.page_number,
            "section": self.section,
        }


@dataclass
class Document:
    """Parsed document container."""

    id: str
    content: str
    doc_type: DocumentType
    metadata: DocumentMetadata = field(default_factory=DocumentMetadata)
    chunks: List[TextChunk] = field(default_factory=list)
    raw_content: Optional[bytes] = None
    tables: List[Dict[str, Any]] = field(default_factory=list)
    images: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def word_count(self) -> int:
        """Get word count of the document."""
        return len(self.content.split())

    @property
    def char_count(self) -> int:
        """Get character count of the document."""
        return len(self.content)

    @property
    def chunk_count(self) -> int:
        """Get number of chunks."""
        return len(self.chunks)

    def to_dict(self, include_raw: bool = False) -> Dict[str, Any]:
        """Convert document to dictionary."""
        result = {
            "id": self.id,
            "content": self.content,
            "doc_type": self.doc_type.value,
            "metadata": self.metadata.to_dict(),
            "chunks": [chunk.to_dict() for chunk in self.chunks],
            "tables": self.tables,
            "images": self.images,
            "word_count": self.word_count,
            "char_count": self.char_count,
            "chunk_count": self.chunk_count,
        }
        if include_raw and self.raw_content:
            result["raw_content"] = self.raw_content.hex()
        return result
