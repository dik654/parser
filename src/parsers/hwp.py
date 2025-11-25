"""
HWP document parser (Hangul Word Processor binary format).
"""

import struct
import uuid
import zlib
from pathlib import Path
from typing import Any, BinaryIO, Dict, List, Optional, Union

from src.document import Document, DocumentMetadata, DocumentType
from src.parsers.base import BaseParser
from src.parsers.registry import register_parser


@register_parser("hwp", extensions=["hwp"])
class HWPParser(BaseParser):
    """
    Parser for HWP documents (Hangul Word Processor binary format).

    HWP uses OLE Compound File format. This parser uses olefile library
    for extraction.
    """

    def __init__(
        self,
        extract_tables: bool = True,
        extract_images: bool = False,
        encoding: str = "utf-16-le",
    ):
        """
        Initialize HWP parser.

        Args:
            extract_tables: Whether to extract tables
            extract_images: Whether to extract embedded images
            encoding: Text encoding (HWP typically uses UTF-16-LE)
        """
        self.extract_tables = extract_tables
        self.extract_images = extract_images
        self.encoding = encoding

    @property
    def supported_extensions(self) -> List[str]:
        return [".hwp", ".HWP"]

    def supports(self, source: Union[str, Path]) -> bool:
        return self._get_extension(source) in [".hwp"]

    def parse(
        self,
        source: Union[str, Path, BinaryIO, bytes],
        **kwargs: Any,
    ) -> Document:
        """
        Parse a HWP document.

        Args:
            source: File path, file object, or raw bytes
            **kwargs: Additional options

        Returns:
            Document: Parsed document object
        """
        try:
            import olefile
        except ImportError:
            raise ImportError(
                "olefile is required for HWP parsing. Install with: pip install olefile"
            )

        import io

        # Open HWP file
        if isinstance(source, bytes):
            ole = olefile.OleFileIO(io.BytesIO(source))
        elif isinstance(source, (str, Path)):
            ole = olefile.OleFileIO(str(source))
        else:
            content = source.read()
            ole = olefile.OleFileIO(io.BytesIO(content))

        try:
            # Check if it's a valid HWP file
            if not self._is_valid_hwp(ole):
                raise ValueError("Not a valid HWP file")

            # Extract text
            content = self._extract_text(ole)

            # Extract metadata
            metadata = self._extract_metadata(ole)
            metadata.word_count = len(content.split())
            metadata.char_count = len(content)
            metadata.source_path = str(source) if isinstance(source, (str, Path)) else None

            # Extract tables
            tables = []
            if self.extract_tables:
                tables = self._extract_tables(ole)

            # Extract images
            images = []
            if self.extract_images:
                images = self._extract_images(ole)

        finally:
            ole.close()

        return Document(
            id=str(uuid.uuid4()),
            content=content,
            doc_type=DocumentType.HWP,
            metadata=metadata,
            tables=tables,
            images=images,
        )

    def _is_valid_hwp(self, ole) -> bool:
        """Check if OLE file is a valid HWP document."""
        # HWP files should have FileHeader stream
        return ole.exists("FileHeader")

    def _extract_text(self, ole) -> str:
        """Extract text content from HWP file."""
        text_parts = []

        # Get FileHeader to check compression
        file_header = ole.openstream("FileHeader").read()
        is_compressed = bool(file_header[36] & 1) if len(file_header) > 36 else False

        # Find all BodyText sections
        section_idx = 0
        while True:
            stream_name = f"BodyText/Section{section_idx}"
            if not ole.exists(stream_name):
                break

            try:
                section_data = ole.openstream(stream_name).read()

                # Decompress if needed
                if is_compressed:
                    try:
                        section_data = zlib.decompress(section_data, -15)
                    except zlib.error:
                        pass

                # Parse section data
                section_text = self._parse_section_data(section_data)
                if section_text:
                    text_parts.append(section_text)

            except Exception:
                pass

            section_idx += 1

        return "\n\n".join(text_parts)

    def _parse_section_data(self, data: bytes) -> str:
        """Parse binary section data to extract text."""
        text_parts = []
        pos = 0

        while pos < len(data) - 4:
            try:
                # Read record header
                header = struct.unpack("<I", data[pos:pos + 4])[0]
                tag_id = header & 0x3FF
                level = (header >> 10) & 0x3FF
                size = (header >> 20) & 0xFFF

                # Extended size
                if size == 0xFFF:
                    if pos + 8 > len(data):
                        break
                    size = struct.unpack("<I", data[pos + 4:pos + 8])[0]
                    pos += 8
                else:
                    pos += 4

                record_data = data[pos:pos + size]

                # Tag ID 67 is HWPTAG_PARA_TEXT (paragraph text)
                if tag_id == 67:
                    text = self._decode_para_text(record_data)
                    if text:
                        text_parts.append(text)

                pos += size

            except Exception:
                pos += 1

        return "\n".join(text_parts)

    def _decode_para_text(self, data: bytes) -> str:
        """Decode paragraph text data."""
        text_chars = []
        pos = 0

        while pos < len(data) - 1:
            # Read character code (2 bytes, UTF-16-LE)
            char_code = struct.unpack("<H", data[pos:pos + 2])[0]

            # Handle special characters
            if char_code < 32:
                # Control characters
                if char_code == 0:  # Null
                    break
                elif char_code == 10:  # Line break
                    text_chars.append("\n")
                elif char_code == 13:  # Carriage return
                    pass
                # Skip other control codes
                pos += 2

                # Some control codes have additional data
                if char_code in [1, 2, 3, 11, 12, 14, 15, 16, 17, 18, 21, 22, 23]:
                    # Variable length additional data
                    pos += 12  # Skip inline object info
            else:
                try:
                    char = chr(char_code)
                    text_chars.append(char)
                except ValueError:
                    pass
                pos += 2

        return "".join(text_chars)

    def _extract_metadata(self, ole) -> DocumentMetadata:
        """Extract metadata from HWP file."""
        metadata = DocumentMetadata()

        try:
            # Try to read SummaryInformation
            if ole.exists("\x05HwpSummaryInformation"):
                props = ole.getproperties("\x05HwpSummaryInformation")
                metadata.title = props.get(2)  # Title
                metadata.author = props.get(4)  # Author
                metadata.custom = {
                    "subject": props.get(3),
                    "keywords": props.get(5),
                    "comments": props.get(6),
                    "last_author": props.get(8),
                    "revision": props.get(9),
                }
        except Exception:
            pass

        return metadata

    def _extract_tables(self, ole) -> List[Dict[str, Any]]:
        """Extract tables from HWP file."""
        # Table extraction from binary HWP is complex
        # Basic implementation - returns empty for now
        return []

    def _extract_images(self, ole) -> List[Dict[str, Any]]:
        """Extract embedded images from HWP file."""
        images = []

        # Images are stored in BinData storage
        try:
            for entry in ole.listdir():
                path = "/".join(entry)
                if path.startswith("BinData/"):
                    try:
                        data = ole.openstream(path).read()
                        # Try to detect image type from magic bytes
                        img_type = self._detect_image_type(data)
                        if img_type:
                            images.append({
                                "path": path,
                                "size": len(data),
                                "format": img_type,
                            })
                    except Exception:
                        continue
        except Exception:
            pass

        return images

    def _detect_image_type(self, data: bytes) -> Optional[str]:
        """Detect image type from magic bytes."""
        if data.startswith(b"\x89PNG"):
            return "png"
        elif data.startswith(b"\xff\xd8\xff"):
            return "jpeg"
        elif data.startswith(b"GIF"):
            return "gif"
        elif data.startswith(b"BM"):
            return "bmp"
        return None
