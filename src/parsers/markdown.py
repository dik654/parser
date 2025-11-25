"""
Markdown document parser using markdown-it-py.
"""

import re
import uuid
from pathlib import Path
from typing import Any, BinaryIO, Dict, List, Optional, Union

from src.document import Document, DocumentMetadata, DocumentType
from src.parsers.base import BaseParser
from src.parsers.registry import register_parser


@register_parser("markdown", extensions=["md", "markdown"])
class MarkdownParser(BaseParser):
    """
    Parser for Markdown documents.

    Uses markdown-it-py for parsing.
    """

    def __init__(
        self,
        extract_code_blocks: bool = True,
        preserve_structure: bool = True,
        extract_links: bool = True,
        extract_images: bool = False,
        encoding: str = "utf-8",
    ):
        """
        Initialize Markdown parser.

        Args:
            extract_code_blocks: Whether to include code blocks
            preserve_structure: Whether to preserve markdown structure
            extract_links: Whether to extract links metadata
            extract_images: Whether to extract image metadata
            encoding: File encoding
        """
        self.extract_code_blocks = extract_code_blocks
        self.preserve_structure = preserve_structure
        self.extract_links = extract_links
        self.extract_images = extract_images
        self.encoding = encoding

    @property
    def supported_extensions(self) -> List[str]:
        return [".md", ".MD", ".markdown", ".MARKDOWN"]

    def supports(self, source: Union[str, Path]) -> bool:
        return self._get_extension(source) in [".md", ".markdown"]

    def parse(
        self,
        source: Union[str, Path, BinaryIO, bytes],
        **kwargs: Any,
    ) -> Document:
        """
        Parse a Markdown document.

        Args:
            source: File path, file object, raw bytes, or markdown string
            **kwargs: Additional options

        Returns:
            Document: Parsed document object
        """
        # Load content
        content = self._load_content(source)

        # Extract metadata from YAML frontmatter if present
        frontmatter, content_body = self._extract_frontmatter(content)

        # Process markdown
        if self.preserve_structure:
            processed_content = content_body
        else:
            processed_content = self._strip_markdown(content_body)

        # Remove code blocks if not wanted
        if not self.extract_code_blocks:
            processed_content = self._remove_code_blocks(processed_content)

        # Extract links
        links = []
        if self.extract_links:
            links = self._extract_links(content_body)

        # Extract images
        images = []
        if self.extract_images:
            images = self._extract_images(content_body)

        # Extract title from first H1
        title = frontmatter.get("title")
        if not title:
            h1_match = re.search(r"^#\s+(.+)$", content_body, re.MULTILINE)
            if h1_match:
                title = h1_match.group(1).strip()

        # Build metadata
        metadata = DocumentMetadata(
            title=title,
            author=frontmatter.get("author"),
            word_count=len(processed_content.split()),
            char_count=len(processed_content),
            source_path=str(source) if isinstance(source, (str, Path)) else None,
            custom={
                "frontmatter": frontmatter,
                "links": links if links else None,
            },
        )

        return Document(
            id=str(uuid.uuid4()),
            content=processed_content,
            doc_type=DocumentType.MARKDOWN,
            metadata=metadata,
            images=images,
        )

    def _load_content(
        self,
        source: Union[str, Path, BinaryIO, bytes],
    ) -> str:
        """Load markdown content from various sources."""
        if isinstance(source, bytes):
            return source.decode(self.encoding)

        elif isinstance(source, (str, Path)):
            path = Path(source)
            if path.exists():
                return path.read_text(encoding=self.encoding)
            else:
                # Assume it's markdown string
                return str(source)

        else:
            # BinaryIO
            content = source.read()
            if isinstance(content, bytes):
                return content.decode(self.encoding)
            return content

    def _extract_frontmatter(self, content: str) -> tuple:
        """Extract YAML frontmatter from markdown content."""
        frontmatter = {}

        # Check for YAML frontmatter
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                try:
                    import yaml
                    frontmatter = yaml.safe_load(parts[1]) or {}
                    content = parts[2].strip()
                except Exception:
                    pass

        return frontmatter, content

    def _strip_markdown(self, content: str) -> str:
        """Strip markdown formatting to get plain text."""
        # Remove headers
        text = re.sub(r"^#{1,6}\s+", "", content, flags=re.MULTILINE)

        # Remove bold/italic
        text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
        text = re.sub(r"\*(.+?)\*", r"\1", text)
        text = re.sub(r"__(.+?)__", r"\1", text)
        text = re.sub(r"_(.+?)_", r"\1", text)

        # Remove links but keep text
        text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)

        # Remove images
        text = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"\1", text)

        # Remove inline code
        text = re.sub(r"`([^`]+)`", r"\1", text)

        # Remove blockquotes
        text = re.sub(r"^>\s+", "", text, flags=re.MULTILINE)

        # Remove horizontal rules
        text = re.sub(r"^[-*_]{3,}\s*$", "", text, flags=re.MULTILINE)

        return text.strip()

    def _remove_code_blocks(self, content: str) -> str:
        """Remove fenced code blocks."""
        # Remove fenced code blocks
        content = re.sub(r"```[\s\S]*?```", "", content)
        content = re.sub(r"~~~[\s\S]*?~~~", "", content)
        return content

    def _extract_links(self, content: str) -> List[Dict[str, str]]:
        """Extract links from markdown content."""
        links = []

        # Find [text](url) pattern
        pattern = r"\[([^\]]+)\]\(([^)]+)\)"
        for match in re.finditer(pattern, content):
            links.append({
                "text": match.group(1),
                "url": match.group(2),
            })

        return links

    def _extract_images(self, content: str) -> List[Dict[str, Any]]:
        """Extract image references from markdown content."""
        images = []

        # Find ![alt](url) pattern
        pattern = r"!\[([^\]]*)\]\(([^)]+)\)"
        for match in re.finditer(pattern, content):
            images.append({
                "alt": match.group(1),
                "src": match.group(2),
            })

        return images
