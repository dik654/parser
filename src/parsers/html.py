"""
HTML document parser using BeautifulSoup.
"""

import re
import uuid
from pathlib import Path
from typing import Any, BinaryIO, Dict, List, Optional, Union

from src.document import Document, DocumentMetadata, DocumentType
from src.parsers.base import BaseParser
from src.parsers.registry import register_parser


@register_parser("html", extensions=["html", "htm"])
class HTMLParser(BaseParser):
    """
    Parser for HTML documents.

    Uses BeautifulSoup for extraction.
    """

    def __init__(
        self,
        extract_links: bool = True,
        extract_images: bool = False,
        preserve_structure: bool = False,
        remove_scripts: bool = True,
        remove_styles: bool = True,
        encoding: Optional[str] = None,
    ):
        """
        Initialize HTML parser.

        Args:
            extract_links: Whether to extract links metadata
            extract_images: Whether to extract image metadata
            preserve_structure: Whether to preserve heading structure
            remove_scripts: Whether to remove script tags
            remove_styles: Whether to remove style tags
            encoding: Force specific encoding (auto-detect if None)
        """
        self.extract_links = extract_links
        self.extract_images = extract_images
        self.preserve_structure = preserve_structure
        self.remove_scripts = remove_scripts
        self.remove_styles = remove_styles
        self.encoding = encoding

    @property
    def supported_extensions(self) -> List[str]:
        return [".html", ".HTML", ".htm", ".HTM"]

    def supports(self, source: Union[str, Path]) -> bool:
        return self._get_extension(source) in [".html", ".htm"]

    def parse(
        self,
        source: Union[str, Path, BinaryIO, bytes],
        **kwargs: Any,
    ) -> Document:
        """
        Parse an HTML document.

        Args:
            source: File path, file object, raw bytes, or HTML string
            **kwargs: Additional options

        Returns:
            Document: Parsed document object
        """
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            raise ImportError(
                "beautifulsoup4 is required. Install with: pip install beautifulsoup4"
            )

        # Get HTML content
        html_content = self._load_content(source)

        # Parse with BeautifulSoup
        soup = BeautifulSoup(html_content, "lxml")

        # Remove unwanted elements
        if self.remove_scripts:
            for script in soup.find_all("script"):
                script.decompose()

        if self.remove_styles:
            for style in soup.find_all("style"):
                style.decompose()

        # Extract text
        if self.preserve_structure:
            content = self._extract_structured_text(soup)
        else:
            content = soup.get_text(separator="\n", strip=True)

        # Clean up whitespace
        content = re.sub(r"\n{3,}", "\n\n", content)
        content = content.strip()

        # Extract metadata
        title = None
        if soup.title:
            title = soup.title.string

        meta_tags = {}
        for meta in soup.find_all("meta"):
            name = meta.get("name") or meta.get("property")
            content_attr = meta.get("content")
            if name and content_attr:
                meta_tags[name] = content_attr

        metadata = DocumentMetadata(
            title=title or meta_tags.get("og:title"),
            author=meta_tags.get("author"),
            word_count=len(content.split()),
            char_count=len(content),
            source_path=str(source) if isinstance(source, (str, Path)) else None,
            custom={
                "description": meta_tags.get("description") or meta_tags.get("og:description"),
                "keywords": meta_tags.get("keywords"),
                "og:type": meta_tags.get("og:type"),
                "og:url": meta_tags.get("og:url"),
            },
        )

        # Extract links
        tables = []
        if self.extract_links:
            links = []
            for a in soup.find_all("a", href=True):
                links.append({
                    "text": a.get_text(strip=True),
                    "href": a["href"],
                })
            if links:
                metadata.custom["links"] = links

        # Extract images
        images = []
        if self.extract_images:
            for img in soup.find_all("img"):
                images.append({
                    "src": img.get("src"),
                    "alt": img.get("alt"),
                    "title": img.get("title"),
                })

        return Document(
            id=str(uuid.uuid4()),
            content=content,
            doc_type=DocumentType.HTML,
            metadata=metadata,
            images=images,
        )

    def _load_content(
        self,
        source: Union[str, Path, BinaryIO, bytes],
    ) -> str:
        """Load HTML content from various sources."""
        if isinstance(source, bytes):
            # Detect encoding
            encoding = self.encoding
            if not encoding:
                try:
                    import chardet
                    detected = chardet.detect(source)
                    encoding = detected.get("encoding", "utf-8")
                except ImportError:
                    encoding = "utf-8"
            return source.decode(encoding)

        elif isinstance(source, (str, Path)):
            path = Path(source)
            if path.exists():
                # Read from file
                encoding = self.encoding
                if not encoding:
                    try:
                        import chardet
                        with path.open("rb") as f:
                            detected = chardet.detect(f.read())
                        encoding = detected.get("encoding", "utf-8")
                    except ImportError:
                        encoding = "utf-8"
                return path.read_text(encoding=encoding)
            else:
                # Assume it's HTML string
                return str(source)

        else:
            # BinaryIO
            content = source.read()
            if isinstance(content, bytes):
                return content.decode(self.encoding or "utf-8")
            return content

    def _extract_structured_text(self, soup) -> str:
        """Extract text while preserving heading structure."""
        text_parts = []

        for element in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "li"]):
            tag_name = element.name
            text = element.get_text(strip=True)

            if not text:
                continue

            if tag_name.startswith("h"):
                level = int(tag_name[1])
                prefix = "#" * level
                text_parts.append(f"\n{prefix} {text}\n")
            elif tag_name == "li":
                text_parts.append(f"• {text}")
            else:
                text_parts.append(text)

        return "\n".join(text_parts)
