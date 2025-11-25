"""
HWPX document parser (Hangul Word Processor XML format).
"""

import uuid
import zipfile
from pathlib import Path
from typing import Any, BinaryIO, Dict, List, Optional, Union
from xml.etree import ElementTree as ET

from src.document import Document, DocumentMetadata, DocumentType
from src.parsers.base import BaseParser
from src.parsers.registry import register_parser


@register_parser("hwpx", extensions=["hwpx"])
class HWPXParser(BaseParser):
    """
    Parser for HWPX documents (Hangul Word Processor XML format).

    HWPX is a ZIP-based XML format used by modern versions of
    Hangul Word Processor (한글).
    """

    # HWPX namespaces
    NAMESPACES = {
        "hp": "http://www.hancom.co.kr/hwpml/2011/paragraph",
        "hs": "http://www.hancom.co.kr/hwpml/2011/section",
        "hc": "http://www.hancom.co.kr/hwpml/2011/core",
        "odf": "urn:oasis:names:tc:opendocument:xmlns:container",
    }

    def __init__(
        self,
        extract_tables: bool = True,
        extract_images: bool = False,
        encoding: str = "utf-8",
    ):
        """
        Initialize HWPX parser.

        Args:
            extract_tables: Whether to extract tables
            extract_images: Whether to extract embedded images
            encoding: Default text encoding
        """
        self.extract_tables = extract_tables
        self.extract_images = extract_images
        self.encoding = encoding

    @property
    def supported_extensions(self) -> List[str]:
        return [".hwpx", ".HWPX"]

    def supports(self, source: Union[str, Path]) -> bool:
        return self._get_extension(source) in [".hwpx"]

    def parse(
        self,
        source: Union[str, Path, BinaryIO, bytes],
        **kwargs: Any,
    ) -> Document:
        """
        Parse a HWPX document.

        Args:
            source: File path, file object, or raw bytes
            **kwargs: Additional options

        Returns:
            Document: Parsed document object
        """
        import io

        # Open HWPX as ZIP
        if isinstance(source, bytes):
            hwpx_file = zipfile.ZipFile(io.BytesIO(source))
        elif isinstance(source, (str, Path)):
            hwpx_file = zipfile.ZipFile(str(source))
        else:
            hwpx_file = zipfile.ZipFile(source)

        try:
            # Extract text from section files
            text_parts = []
            tables = []

            # Find section files in Contents folder
            section_files = sorted([
                name for name in hwpx_file.namelist()
                if name.startswith("Contents/section") and name.endswith(".xml")
            ])

            for section_file in section_files:
                section_content = hwpx_file.read(section_file)
                section_text, section_tables = self._parse_section(section_content)
                text_parts.append(section_text)
                tables.extend(section_tables)

            content = "\n\n".join(text_parts)

            # Extract metadata
            metadata = self._extract_metadata(hwpx_file)
            metadata.word_count = len(content.split())
            metadata.char_count = len(content)
            metadata.source_path = str(source) if isinstance(source, (str, Path)) else None

            # Extract images if requested
            images = []
            if self.extract_images:
                images = self._extract_images(hwpx_file)

        finally:
            hwpx_file.close()

        return Document(
            id=str(uuid.uuid4()),
            content=content,
            doc_type=DocumentType.HWPX,
            metadata=metadata,
            tables=tables if self.extract_tables else [],
            images=images,
        )

    def _parse_section(self, xml_content: bytes) -> tuple:
        """Parse a section XML file."""
        text_parts = []
        tables = []

        try:
            root = ET.fromstring(xml_content)

            # Try multiple namespace patterns
            namespaces_to_try = [
                self.NAMESPACES,
                {"hp": "http://www.hancom.co.kr/hwpml/2016/paragraph"},
                {},  # No namespace
            ]

            for ns in namespaces_to_try:
                # Find all text elements (hp:t tags)
                text_elements = root.findall(".//hp:t", ns) if ns else root.findall(".//*")

                if text_elements:
                    for elem in text_elements:
                        if elem.text and elem.text.strip():
                            text_parts.append(elem.text.strip())
                    break

            # If namespace approach didn't work, try BeautifulSoup
            if not text_parts:
                text_parts, tables = self._parse_with_beautifulsoup(xml_content)

            # Extract tables
            if self.extract_tables and not tables:
                tables = self._extract_tables_from_xml(root)

        except ET.ParseError:
            # Fallback to BeautifulSoup
            text_parts, tables = self._parse_with_beautifulsoup(xml_content)

        return "\n".join(text_parts), tables

    def _parse_with_beautifulsoup(self, xml_content: bytes) -> tuple:
        """Fallback parsing using BeautifulSoup."""
        text_parts = []
        tables = []

        try:
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(xml_content, "lxml-xml")

            # Find text elements
            for t_elem in soup.find_all(["t", "hp:t", "run"]):
                text = t_elem.get_text(strip=True)
                if text:
                    text_parts.append(text)

            # Extract tables
            if self.extract_tables:
                for tbl in soup.find_all(["tbl", "hp:tbl", "table"]):
                    table_data = []
                    for row in tbl.find_all(["tr", "hp:tr", "row"]):
                        row_data = []
                        for cell in row.find_all(["tc", "hp:tc", "cell"]):
                            cell_text = cell.get_text(strip=True)
                            row_data.append(cell_text)
                        if row_data:
                            table_data.append(row_data)
                    if table_data:
                        tables.append({
                            "data": table_data,
                            "row_count": len(table_data),
                            "col_count": len(table_data[0]) if table_data else 0,
                        })

        except ImportError:
            pass

        return text_parts, tables

    def _extract_tables_from_xml(self, root: ET.Element) -> List[Dict[str, Any]]:
        """Extract tables from XML element."""
        tables = []

        # Find table elements
        for tbl in root.findall(".//hp:tbl", self.NAMESPACES):
            table_data = []
            for row in tbl.findall(".//hp:tr", self.NAMESPACES):
                row_data = []
                for cell in row.findall(".//hp:tc", self.NAMESPACES):
                    cell_text = "".join(cell.itertext()).strip()
                    row_data.append(cell_text)
                if row_data:
                    table_data.append(row_data)

            if table_data:
                tables.append({
                    "data": table_data,
                    "row_count": len(table_data),
                    "col_count": len(table_data[0]) if table_data else 0,
                })

        return tables

    def _extract_metadata(self, hwpx_file: zipfile.ZipFile) -> DocumentMetadata:
        """Extract metadata from HWPX file."""
        metadata = DocumentMetadata()

        # Try to read core properties
        try:
            if "META-INF/manifest.xml" in hwpx_file.namelist():
                manifest = hwpx_file.read("META-INF/manifest.xml")
                root = ET.fromstring(manifest)
                # Parse manifest for metadata

            # Try content.hpf for document info
            if "Contents/content.hpf" in hwpx_file.namelist():
                content_hpf = hwpx_file.read("Contents/content.hpf")
                root = ET.fromstring(content_hpf)

                # Extract page count from section info
                page_count = len([
                    name for name in hwpx_file.namelist()
                    if name.startswith("Contents/section") and name.endswith(".xml")
                ])
                metadata.page_count = page_count

        except Exception:
            pass

        return metadata

    def _extract_images(self, hwpx_file: zipfile.ZipFile) -> List[Dict[str, Any]]:
        """Extract embedded images from HWPX file."""
        images = []

        # Images are typically in BinData folder
        for name in hwpx_file.namelist():
            if name.startswith("BinData/") or "/BinData/" in name:
                ext = Path(name).suffix.lower()
                if ext in [".png", ".jpg", ".jpeg", ".gif", ".bmp"]:
                    try:
                        image_data = hwpx_file.read(name)
                        images.append({
                            "path": name,
                            "size": len(image_data),
                            "format": ext.lstrip("."),
                        })
                    except Exception:
                        continue

        return images
