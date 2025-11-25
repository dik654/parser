"""
PPTX document parser using python-pptx.
"""

import uuid
from pathlib import Path
from typing import Any, BinaryIO, Dict, List, Optional, Union

from src.document import Document, DocumentMetadata, DocumentType
from src.parsers.base import BaseParser
from src.parsers.registry import register_parser


@register_parser("pptx", extensions=["pptx", "ppt"])
class PPTXParser(BaseParser):
    """
    Parser for Microsoft PowerPoint presentations (.pptx).

    Uses python-pptx for extraction.
    """

    def __init__(
        self,
        extract_notes: bool = True,
        extract_tables: bool = True,
        extract_images: bool = False,
        slide_separator: str = "\n\n---\n\n",
    ):
        """
        Initialize PPTX parser.

        Args:
            extract_notes: Whether to extract speaker notes
            extract_tables: Whether to extract tables
            extract_images: Whether to extract embedded images
            slide_separator: Separator between slides
        """
        self.extract_notes = extract_notes
        self.extract_tables = extract_tables
        self.extract_images = extract_images
        self.slide_separator = slide_separator

    @property
    def supported_extensions(self) -> List[str]:
        return [".pptx", ".PPTX"]

    def supports(self, source: Union[str, Path]) -> bool:
        return self._get_extension(source) in [".pptx"]

    def parse(
        self,
        source: Union[str, Path, BinaryIO, bytes],
        **kwargs: Any,
    ) -> Document:
        """
        Parse a PPTX document.

        Args:
            source: File path, file object, or raw bytes
            **kwargs: Additional options

        Returns:
            Document: Parsed document object
        """
        try:
            from pptx import Presentation
        except ImportError:
            raise ImportError(
                "python-pptx is required. Install with: pip install python-pptx"
            )

        import io

        if isinstance(source, bytes):
            prs = Presentation(io.BytesIO(source))
        elif isinstance(source, (str, Path)):
            prs = Presentation(str(source))
        else:
            prs = Presentation(source)

        slide_texts: List[str] = []
        tables: List[Dict[str, Any]] = []
        images: List[Dict[str, Any]] = []

        for slide_idx, slide in enumerate(prs.slides, 1):
            slide_content: List[str] = []
            slide_content.append(f"[Slide {slide_idx}]")

            # Extract text from shapes
            for shape in slide.shapes:
                if shape.has_text_frame:
                    for paragraph in shape.text_frame.paragraphs:
                        text = paragraph.text.strip()
                        if text:
                            slide_content.append(text)

                # Extract tables
                if self.extract_tables and shape.has_table:
                    table_data = self._extract_table(shape.table)
                    tables.append({
                        "slide": slide_idx,
                        "data": table_data,
                        "row_count": len(table_data),
                        "col_count": len(table_data[0]) if table_data else 0,
                    })

            # Extract speaker notes
            if self.extract_notes and slide.has_notes_slide:
                notes_frame = slide.notes_slide.notes_text_frame
                if notes_frame:
                    notes_text = notes_frame.text.strip()
                    if notes_text:
                        slide_content.append(f"\n[Notes]\n{notes_text}")

            slide_texts.append("\n".join(slide_content))

        content = self.slide_separator.join(slide_texts)

        # Extract metadata
        core_props = prs.core_properties
        metadata = DocumentMetadata(
            title=core_props.title,
            author=core_props.author,
            created_at=core_props.created,
            modified_at=core_props.modified,
            page_count=len(prs.slides),
            word_count=len(content.split()),
            char_count=len(content),
            source_path=str(source) if isinstance(source, (str, Path)) else None,
            custom={
                "subject": core_props.subject,
                "keywords": core_props.keywords,
                "category": core_props.category,
                "slide_count": len(prs.slides),
            },
        )

        # Extract images if enabled
        if self.extract_images:
            images = self._extract_images(prs)

        return Document(
            id=str(uuid.uuid4()),
            content=content,
            doc_type=DocumentType.PPTX,
            metadata=metadata,
            tables=tables,
            images=images,
        )

    def _extract_table(self, table) -> List[List[str]]:
        """Extract data from a table shape."""
        table_data = []
        for row in table.rows:
            row_data = []
            for cell in row.cells:
                row_data.append(cell.text)
            table_data.append(row_data)
        return table_data

    def _extract_images(self, prs) -> List[Dict[str, Any]]:
        """Extract embedded images from presentation."""
        images = []

        for slide_idx, slide in enumerate(prs.slides, 1):
            for shape_idx, shape in enumerate(slide.shapes):
                if shape.shape_type == 13:  # MSO_SHAPE_TYPE.PICTURE
                    try:
                        image = shape.image
                        images.append({
                            "slide": slide_idx,
                            "shape_index": shape_idx,
                            "content_type": image.content_type,
                            "size": len(image.blob),
                            "ext": image.ext,
                        })
                    except Exception:
                        continue

        return images
