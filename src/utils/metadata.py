"""
Metadata extraction and processing utilities.
"""

import re
from collections import Counter
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set

from src.document import Document, DocumentMetadata


@dataclass
class ExtractedMetadata:
    """Container for extracted metadata."""

    title: Optional[str] = None
    author: Optional[str] = None
    language: Optional[str] = None
    keywords: List[str] = None
    summary: Optional[str] = None
    word_count: int = 0
    char_count: int = 0
    sentence_count: int = 0
    paragraph_count: int = 0
    reading_time_minutes: float = 0.0
    custom: Dict[str, Any] = None

    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []
        if self.custom is None:
            self.custom = {}


class MetadataExtractor:
    """
    Extract and enhance document metadata.
    """

    # Average reading speed (words per minute)
    READING_SPEED_WPM = 200

    def __init__(
        self,
        detect_language: bool = True,
        extract_keywords: bool = True,
        max_keywords: int = 10,
    ):
        """
        Initialize metadata extractor.

        Args:
            detect_language: Whether to detect document language
            extract_keywords: Whether to extract keywords
            max_keywords: Maximum number of keywords to extract
        """
        self.detect_language = detect_language
        self.extract_keywords = extract_keywords
        self.max_keywords = max_keywords

    def extract(self, document: Document) -> ExtractedMetadata:
        """
        Extract metadata from document.

        Args:
            document: Document to analyze

        Returns:
            ExtractedMetadata: Extracted metadata
        """
        content = document.content

        # Basic counts
        word_count = len(content.split())
        char_count = len(content)
        sentence_count = self._count_sentences(content)
        paragraph_count = self._count_paragraphs(content)

        # Reading time
        reading_time = word_count / self.READING_SPEED_WPM

        # Language detection
        language = None
        if self.detect_language:
            language = self._detect_language(content)

        # Keyword extraction
        keywords = []
        if self.extract_keywords:
            keywords = self._extract_keywords(content, self.max_keywords)

        # Title extraction
        title = document.metadata.title
        if not title:
            title = self._extract_title(content)

        return ExtractedMetadata(
            title=title,
            author=document.metadata.author,
            language=language,
            keywords=keywords,
            word_count=word_count,
            char_count=char_count,
            sentence_count=sentence_count,
            paragraph_count=paragraph_count,
            reading_time_minutes=reading_time,
        )

    def _count_sentences(self, text: str) -> int:
        """Count sentences in text."""
        # Simple sentence counting based on punctuation
        sentences = re.split(r"[.!?]+\s+", text)
        return len([s for s in sentences if s.strip()])

    def _count_paragraphs(self, text: str) -> int:
        """Count paragraphs in text."""
        paragraphs = re.split(r"\n\s*\n", text)
        return len([p for p in paragraphs if p.strip()])

    def _detect_language(self, text: str) -> Optional[str]:
        """Detect text language."""
        try:
            from langdetect import detect, LangDetectException

            # Use sample for efficiency
            sample = text[:5000]
            return detect(sample)
        except ImportError:
            return None
        except LangDetectException:
            return None

    def _extract_keywords(self, text: str, max_keywords: int) -> List[str]:
        """Extract keywords using simple frequency analysis."""
        # Tokenize and filter
        words = re.findall(r"\b[a-zA-Z가-힣]{3,}\b", text.lower())

        # Remove common stop words
        stop_words = self._get_stop_words()
        words = [w for w in words if w not in stop_words]

        # Count frequencies
        word_freq = Counter(words)

        # Return top keywords
        return [word for word, _ in word_freq.most_common(max_keywords)]

    def _extract_title(self, text: str) -> Optional[str]:
        """Try to extract title from text content."""
        lines = text.split("\n")

        for line in lines[:10]:  # Check first 10 lines
            line = line.strip()
            if not line:
                continue

            # Skip very long lines
            if len(line) > 200:
                continue

            # Check for markdown heading
            if line.startswith("#"):
                return line.lstrip("#").strip()

            # First substantial line might be title
            if len(line) > 10 and not line.endswith(":"):
                return line[:100]

        return None

    def _get_stop_words(self) -> Set[str]:
        """Get common stop words."""
        # Basic English stop words
        english = {
            "the", "be", "to", "of", "and", "a", "in", "that", "have", "i",
            "it", "for", "not", "on", "with", "he", "as", "you", "do", "at",
            "this", "but", "his", "by", "from", "they", "we", "say", "her",
            "she", "or", "an", "will", "my", "one", "all", "would", "there",
            "their", "what", "so", "up", "out", "if", "about", "who", "get",
            "which", "go", "me", "when", "make", "can", "like", "time", "no",
            "just", "him", "know", "take", "people", "into", "year", "your",
            "good", "some", "could", "them", "see", "other", "than", "then",
            "now", "look", "only", "come", "its", "over", "think", "also",
            "back", "after", "use", "two", "how", "our", "work", "first",
            "well", "way", "even", "new", "want", "because", "any", "these",
            "give", "day", "most", "us", "is", "are", "was", "were", "been",
            "being", "has", "had", "does", "did", "doing", "done",
        }

        # Basic Korean stop words
        korean = {
            "의", "가", "이", "은", "는", "에", "를", "을", "로", "으로",
            "와", "과", "도", "만", "에서", "에게", "한", "하는", "하다",
            "있다", "없다", "되다", "수", "것", "등", "및", "또는",
        }

        return english | korean

    def update_document_metadata(
        self,
        document: Document,
        extracted: ExtractedMetadata,
    ) -> Document:
        """
        Update document with extracted metadata.

        Args:
            document: Document to update
            extracted: Extracted metadata

        Returns:
            Updated document
        """
        if extracted.title and not document.metadata.title:
            document.metadata.title = extracted.title

        if extracted.language:
            document.metadata.language = extracted.language

        document.metadata.word_count = extracted.word_count
        document.metadata.char_count = extracted.char_count

        if not document.metadata.custom:
            document.metadata.custom = {}

        document.metadata.custom.update({
            "keywords": extracted.keywords,
            "sentence_count": extracted.sentence_count,
            "paragraph_count": extracted.paragraph_count,
            "reading_time_minutes": extracted.reading_time_minutes,
        })

        return document


def merge_metadata(
    *metadata_list: DocumentMetadata,
) -> DocumentMetadata:
    """
    Merge multiple metadata objects.

    Later values override earlier ones for non-None fields.

    Args:
        *metadata_list: Metadata objects to merge

    Returns:
        Merged metadata
    """
    result = DocumentMetadata()

    for meta in metadata_list:
        if meta.title:
            result.title = meta.title
        if meta.author:
            result.author = meta.author
        if meta.created_at:
            result.created_at = meta.created_at
        if meta.modified_at:
            result.modified_at = meta.modified_at
        if meta.page_count:
            result.page_count = meta.page_count
        if meta.word_count:
            result.word_count = meta.word_count
        if meta.char_count:
            result.char_count = meta.char_count
        if meta.language:
            result.language = meta.language
        if meta.source_path:
            result.source_path = meta.source_path
        if meta.file_size:
            result.file_size = meta.file_size
        if meta.mime_type:
            result.mime_type = meta.mime_type
        if meta.encoding:
            result.encoding = meta.encoding

        # Merge custom fields
        if meta.custom:
            result.custom.update(meta.custom)

    return result
