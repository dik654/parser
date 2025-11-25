"""
PDF document parser using PyMuPDF and pdfplumber.
"""

import io
import uuid
from pathlib import Path
from typing import Any, BinaryIO, Dict, List, Optional, Union

from src.document import Document, DocumentMetadata, DocumentType
from src.parsers.base import BaseParser
from src.parsers.registry import register_parser


@register_parser("pdf", extensions=["pdf"])
class PDFParser(BaseParser):
    """
    Parser for PDF documents.

    Uses PyMuPDF (fitz) for text extraction and pdfplumber for tables.
    """

    def __init__(
        self,
        extract_tables: bool = True,
        extract_images: bool = False,
        ocr_enabled: bool = False,
        ocr_language: str = "eng",
    ):
        """
        Initialize PDF parser.

        Args:
            extract_tables: Whether to extract tables from PDF
            extract_images: Whether to extract embedded images
            ocr_enabled: Whether to use OCR for scanned pages
            ocr_language: Language for OCR (e.g., "eng", "kor", "eng+kor")
        """
        self.extract_tables = extract_tables
        self.extract_images = extract_images
        self.ocr_enabled = ocr_enabled
        self.ocr_language = ocr_language

    @property
    def supported_extensions(self) -> List[str]:
        return [".pdf", ".PDF"]

    def supports(self, source: Union[str, Path]) -> bool:
        return self._get_extension(source) in [".pdf"]

    def parse(
        self,
        source: Union[str, Path, BinaryIO, bytes],
        **kwargs: Any,
    ) -> Document:
        """
        Parse a PDF document.

        Args:
            source: File path, file object, or raw bytes
            **kwargs: Additional options (password for encrypted PDFs)

        Returns:
            Document: Parsed document object
        """
        try:
            import fitz  # PyMuPDF
        except ImportError:
            raise ImportError("PyMuPDF is required. Install with: pip install pymupdf")

        password = kwargs.get("password", None)

        # Open PDF
        if isinstance(source, bytes):
            pdf_doc = fitz.open(stream=source, filetype="pdf")
        elif isinstance(source, (str, Path)):
            pdf_doc = fitz.open(str(source))
        else:
            # BinaryIO
            content = source.read()
            pdf_doc = fitz.open(stream=content, filetype="pdf")

        # Handle encrypted PDFs
        if pdf_doc.is_encrypted:
            if password:
                if not pdf_doc.authenticate(password):
                    raise ValueError("Invalid password for encrypted PDF")
            else:
                raise ValueError("PDF is encrypted. Provide password.")

        # Extract text
        text_parts: List[str] = []
        page_texts: Dict[int, str] = {}

        for page_num in range(len(pdf_doc)):
            page = pdf_doc[page_num]
            page_text = page.get_text()

            # If no text and OCR enabled, try OCR
            if not page_text.strip() and self.ocr_enabled:
                page_text = self._ocr_page(page)

            text_parts.append(page_text)
            page_texts[page_num + 1] = page_text

        content = "\n\n".join(text_parts)

        # Extract metadata
        meta = pdf_doc.metadata or {}
        metadata = DocumentMetadata(
            title=meta.get("title"),
            author=meta.get("author"),
            page_count=len(pdf_doc),
            word_count=len(content.split()),
            char_count=len(content),
            source_path=str(source) if isinstance(source, (str, Path)) else None,
            custom={
                "producer": meta.get("producer"),
                "creator": meta.get("creator"),
                "subject": meta.get("subject"),
                "keywords": meta.get("keywords"),
            },
        )

        # Extract tables if enabled
        tables = []
        if self.extract_tables:
            tables = self._extract_tables(source)

        # Extract images if enabled
        images = []
        if self.extract_images:
            images = self._extract_images(pdf_doc)

        pdf_doc.close()

        return Document(
            id=str(uuid.uuid4()),
            content=content,
            doc_type=DocumentType.PDF,
            metadata=metadata,
            tables=tables,
            images=images,
        )

    def _extract_tables(
        self,
        source: Union[str, Path, BinaryIO, bytes],
    ) -> List[Dict[str, Any]]:
        """Extract tables using pdfplumber."""
        try:
            import pdfplumber
        except ImportError:
            return []

        tables = []

        try:
            if isinstance(source, bytes):
                pdf = pdfplumber.open(io.BytesIO(source))
            elif isinstance(source, (str, Path)):
                pdf = pdfplumber.open(str(source))
            else:
                source.seek(0)
                pdf = pdfplumber.open(source)

            for page_num, page in enumerate(pdf.pages, 1):
                page_tables = page.extract_tables()
                for table_idx, table in enumerate(page_tables):
                    if table:
                        tables.append({
                            "page": page_num,
                            "table_index": table_idx,
                            "data": table,
                            "row_count": len(table),
                            "col_count": len(table[0]) if table else 0,
                        })

            pdf.close()
        except Exception:
            pass

        return tables

    def _extract_images(self, pdf_doc) -> List[Dict[str, Any]]:
        """Extract embedded images from PDF."""
        images = []

        for page_num in range(len(pdf_doc)):
            page = pdf_doc[page_num]
            image_list = page.get_images()

            for img_idx, img in enumerate(image_list):
                xref = img[0]
                try:
                    base_image = pdf_doc.extract_image(xref)
                    images.append({
                        "page": page_num + 1,
                        "image_index": img_idx,
                        "width": base_image.get("width"),
                        "height": base_image.get("height"),
                        "format": base_image.get("ext"),
                        "xref": xref,
                    })
                except Exception:
                    continue

        return images

    def _ocr_page(self, page) -> str:
        """Perform OCR on a page."""
        try:
            import pytesseract
            from PIL import Image

            # Render page to image
            pix = page.get_pixmap(matrix=page.matrix * 2)  # 2x zoom for better OCR
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            # Perform OCR
            text = pytesseract.image_to_string(img, lang=self.ocr_language)
            return text
        except ImportError:
            return ""
        except Exception:
            return ""
