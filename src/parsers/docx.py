"""
DOCX document parser using python-docx.
"""

import uuid
from pathlib import Path
from typing import Any, BinaryIO, Dict, List, Optional, Union

from src.document import Document, DocumentMetadata, DocumentType
from src.parsers.base import BaseParser
from src.parsers.registry import register_parser


@register_parser("docx", extensions=["docx", "doc"])
class DOCXParser(BaseParser):
    """
    Parser for Microsoft Word documents (.docx).

    Uses python-docx for extraction.
    """

    def __init__(
        self,
        extract_tables: bool = True,
        extract_images: bool = False,
        include_headers_footers: bool = True,
        preserve_formatting: bool = False,
    ):
        """
        Initialize DOCX parser.

        Args:
            extract_tables: Whether to extract tables
            extract_images: Whether to extract embedded images
            include_headers_footers: Whether to include headers/footers
            preserve_formatting: Whether to preserve text formatting info
        """
        self.extract_tables = extract_tables
        self.extract_images = extract_images
        self.include_headers_footers = include_headers_footers
        self.preserve_formatting = preserve_formatting

    @property
    def supported_extensions(self) -> List[str]:
        return [".docx", ".DOCX"]

    def supports(self, source: Union[str, Path]) -> bool:
        return self._get_extension(source) in [".docx"]

    def parse(
        self,
        source: Union[str, Path, BinaryIO, bytes],
        **kwargs: Any,
    ) -> Document:
        """
        Parse a DOCX document.

        Args:
            source: File path, file object, or raw bytes
            **kwargs: Additional options

        Returns:
            Document: Parsed document object
        """
        try:
            from docx import Document as DocxDocument
            from docx.opc.exceptions import PackageNotFoundError
        except ImportError:
            raise ImportError(
                "python-docx is required. Install with: pip install python-docx"
            )

        try:
            import io

            if isinstance(source, bytes):
                doc = DocxDocument(io.BytesIO(source))
            elif isinstance(source, (str, Path)):
                doc = DocxDocument(str(source))
            else:
                doc = DocxDocument(source)
        except PackageNotFoundError:
            raise ValueError("Invalid or corrupted DOCX file")

        # Extract text from paragraphs
        text_parts: List[str] = []

        # Headers
        if self.include_headers_footers:
            for section in doc.sections:
                header = section.header
                if header:
                    for para in header.paragraphs:
                        if para.text.strip():
                            text_parts.append(para.text)

        # Main body
        for para in doc.paragraphs:
            if para.text.strip():
                text_parts.append(para.text)

        # Footers
        if self.include_headers_footers:
            for section in doc.sections:
                footer = section.footer
                if footer:
                    for para in footer.paragraphs:
                        if para.text.strip():
                            text_parts.append(para.text)

        content = "\n\n".join(text_parts)

        # Extract metadata
        core_props = doc.core_properties
        metadata = DocumentMetadata(
            title=core_props.title,
            author=core_props.author,
            created_at=core_props.created,
            modified_at=core_props.modified,
            word_count=len(content.split()),
            char_count=len(content),
            source_path=str(source) if isinstance(source, (str, Path)) else None,
            custom={
                "subject": core_props.subject,
                "keywords": core_props.keywords,
                "category": core_props.category,
                "comments": core_props.comments,
                "last_modified_by": core_props.last_modified_by,
            },
        )

        # Extract tables
        tables = []
        if self.extract_tables:
            tables = self._extract_tables(doc)

        # Extract images
        images = []
        if self.extract_images:
            images = self._extract_images(doc)

        return Document(
            id=str(uuid.uuid4()),
            content=content,
            doc_type=DocumentType.DOCX,
            metadata=metadata,
            tables=tables,
            images=images,
        )

    def _extract_tables(self, doc) -> List[Dict[str, Any]]:
        """Extract tables from document."""
        tables = []

        for table_idx, table in enumerate(doc.tables):
            table_data = []
            for row in table.rows:
                row_data = []
                for cell in row.cells:
                    row_data.append(cell.text)
                table_data.append(row_data)

            tables.append({
                "table_index": table_idx,
                "data": table_data,
                "row_count": len(table_data),
                "col_count": len(table_data[0]) if table_data else 0,
            })

        return tables

    def _extract_images(self, doc) -> List[Dict[str, Any]]:
        """Extract embedded images from document."""
        images = []

        for rel_id, rel in doc.part.rels.items():
            if "image" in rel.target_ref:
                try:
                    image_part = rel.target_part
                    images.append({
                        "rel_id": rel_id,
                        "content_type": image_part.content_type,
                        "blob_size": len(image_part.blob),
                    })
                except Exception:
                    continue

        return images
