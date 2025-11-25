"""
Image document parser with OCR support.
"""

import uuid
from pathlib import Path
from typing import Any, BinaryIO, Dict, List, Optional, Union

from src.document import Document, DocumentMetadata, DocumentType
from src.parsers.base import BaseParser
from src.parsers.registry import register_parser


@register_parser("image", extensions=["png", "jpg", "jpeg", "gif", "bmp", "tiff", "tif", "webp"])
class ImageParser(BaseParser):
    """
    Parser for image files using OCR.

    Supports pytesseract and EasyOCR for text extraction.
    """

    def __init__(
        self,
        ocr_engine: str = "tesseract",
        language: str = "eng",
        preprocess: bool = True,
        dpi: int = 300,
        confidence_threshold: float = 0.0,
    ):
        """
        Initialize Image parser.

        Args:
            ocr_engine: OCR engine to use ("tesseract" or "easyocr")
            language: Language(s) for OCR (e.g., "eng", "kor", "eng+kor")
            preprocess: Whether to preprocess image before OCR
            dpi: DPI for image processing
            confidence_threshold: Minimum confidence for OCR results
        """
        self.ocr_engine = ocr_engine
        self.language = language
        self.preprocess = preprocess
        self.dpi = dpi
        self.confidence_threshold = confidence_threshold

    @property
    def supported_extensions(self) -> List[str]:
        return [
            ".png", ".PNG",
            ".jpg", ".JPG", ".jpeg", ".JPEG",
            ".gif", ".GIF",
            ".bmp", ".BMP",
            ".tiff", ".TIFF", ".tif", ".TIF",
            ".webp", ".WEBP",
        ]

    def supports(self, source: Union[str, Path]) -> bool:
        ext = self._get_extension(source)
        return ext in [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".tif", ".webp"]

    def parse(
        self,
        source: Union[str, Path, BinaryIO, bytes],
        **kwargs: Any,
    ) -> Document:
        """
        Parse an image file using OCR.

        Args:
            source: File path, file object, or raw bytes
            **kwargs: Additional options

        Returns:
            Document: Parsed document object
        """
        try:
            from PIL import Image
        except ImportError:
            raise ImportError("Pillow is required. Install with: pip install Pillow")

        import io

        # Load image
        if isinstance(source, bytes):
            img = Image.open(io.BytesIO(source))
        elif isinstance(source, (str, Path)):
            img = Image.open(str(source))
        else:
            img = Image.open(source)

        # Preprocess if enabled
        if self.preprocess:
            img = self._preprocess_image(img)

        # Perform OCR
        if self.ocr_engine == "easyocr":
            content, ocr_data = self._ocr_easyocr(img)
        else:
            content, ocr_data = self._ocr_tesseract(img)

        # Build metadata
        metadata = DocumentMetadata(
            word_count=len(content.split()),
            char_count=len(content),
            source_path=str(source) if isinstance(source, (str, Path)) else None,
            custom={
                "width": img.width,
                "height": img.height,
                "format": img.format,
                "mode": img.mode,
                "ocr_engine": self.ocr_engine,
                "ocr_language": self.language,
                "ocr_data": ocr_data,
            },
        )

        img.close()

        return Document(
            id=str(uuid.uuid4()),
            content=content,
            doc_type=DocumentType.IMAGE,
            metadata=metadata,
        )

    def _preprocess_image(self, img):
        """Preprocess image for better OCR results."""
        from PIL import Image, ImageEnhance, ImageFilter

        # Convert to RGB if necessary
        if img.mode != "RGB":
            img = img.convert("RGB")

        # Convert to grayscale
        img = img.convert("L")

        # Enhance contrast
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.5)

        # Apply slight sharpening
        img = img.filter(ImageFilter.SHARPEN)

        # Binarization (simple threshold)
        threshold = 128
        img = img.point(lambda x: 255 if x > threshold else 0, "1")

        # Convert back to grayscale for OCR
        img = img.convert("L")

        return img

    def _ocr_tesseract(self, img) -> tuple:
        """Perform OCR using pytesseract."""
        try:
            import pytesseract
        except ImportError:
            raise ImportError(
                "pytesseract is required. Install with: pip install pytesseract"
            )

        # Get detailed OCR data
        ocr_data = pytesseract.image_to_data(
            img,
            lang=self.language,
            output_type=pytesseract.Output.DICT,
        )

        # Filter by confidence
        text_parts = []
        for i, conf in enumerate(ocr_data["conf"]):
            try:
                conf_value = float(conf)
                if conf_value >= self.confidence_threshold:
                    text = ocr_data["text"][i]
                    if text.strip():
                        text_parts.append(text)
            except (ValueError, TypeError):
                continue

        content = " ".join(text_parts)

        # Simplified OCR data for metadata
        simplified_data = {
            "word_count": len(text_parts),
            "avg_confidence": sum(
                float(c) for c in ocr_data["conf"] if str(c).replace("-", "").isdigit()
            ) / max(len(ocr_data["conf"]), 1),
        }

        return content, simplified_data

    def _ocr_easyocr(self, img) -> tuple:
        """Perform OCR using EasyOCR."""
        try:
            import easyocr
        except ImportError:
            raise ImportError(
                "easyocr is required. Install with: pip install easyocr"
            )

        import numpy as np

        # Convert PIL image to numpy array
        img_array = np.array(img)

        # Parse language codes
        lang_list = self.language.replace("+", ",").split(",")
        lang_mapping = {
            "eng": "en",
            "kor": "ko",
            "jpn": "ja",
            "chi_sim": "ch_sim",
            "chi_tra": "ch_tra",
        }
        lang_list = [lang_mapping.get(l.strip(), l.strip()) for l in lang_list]

        # Initialize reader
        reader = easyocr.Reader(lang_list, gpu=False)

        # Perform OCR
        results = reader.readtext(img_array)

        # Extract text with confidence filtering
        text_parts = []
        confidences = []

        for bbox, text, conf in results:
            if conf >= self.confidence_threshold:
                text_parts.append(text)
                confidences.append(conf)

        content = " ".join(text_parts)

        # Simplified OCR data
        simplified_data = {
            "word_count": len(text_parts),
            "avg_confidence": sum(confidences) / max(len(confidences), 1),
            "detection_count": len(results),
        }

        return content, simplified_data
