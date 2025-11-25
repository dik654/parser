"""
Text cleaner for removing unwanted content.
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Pattern, Set

from src.preprocessors.base import BasePreprocessor


@dataclass
class CleanerConfig:
    """Configuration for text cleaner."""

    remove_html_tags: bool = True
    remove_urls: bool = False
    remove_emails: bool = False
    remove_phone_numbers: bool = False
    remove_extra_whitespace: bool = True
    remove_line_numbers: bool = False
    remove_page_numbers: bool = False
    remove_headers_footers: bool = False
    remove_special_chars: bool = False
    special_chars_to_remove: str = ""
    preserve_chars: str = ""
    remove_emojis: bool = False
    min_line_length: int = 0
    max_consecutive_newlines: int = 2
    custom_patterns_to_remove: List[str] = field(default_factory=list)


class TextCleaner(BasePreprocessor):
    """
    Text cleaner for removing unwanted content.

    Supports various cleaning operations like HTML tag removal,
    URL removal, whitespace normalization, etc.
    """

    # Precompiled regex patterns
    HTML_TAG_PATTERN = re.compile(r"<[^>]+>")
    URL_PATTERN = re.compile(
        r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[^\s]*|"
        r"www\.[-\w.]+[^\s]*"
    )
    EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
    PHONE_PATTERN = re.compile(
        r"(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}|"  # US format
        r"0\d{1,2}[-.\s]?\d{3,4}[-.\s]?\d{4}"  # Korean format
    )
    EMOJI_PATTERN = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "]+",
        flags=re.UNICODE,
    )
    LINE_NUMBER_PATTERN = re.compile(r"^\s*\d+[\s|:.]", re.MULTILINE)
    PAGE_NUMBER_PATTERN = re.compile(
        r"^\s*[-—]\s*\d+\s*[-—]\s*$|"
        r"^\s*Page\s+\d+\s*(?:of\s+\d+)?\s*$|"
        r"^\s*\d+\s*$",
        re.MULTILINE | re.IGNORECASE,
    )

    def __init__(self, config: Optional[CleanerConfig] = None):
        """
        Initialize text cleaner.

        Args:
            config: Cleaner configuration
        """
        self.config = config or CleanerConfig()
        self._compile_custom_patterns()

    def _compile_custom_patterns(self) -> None:
        """Compile custom regex patterns."""
        self.custom_patterns: List[Pattern] = []
        for pattern_str in self.config.custom_patterns_to_remove:
            try:
                self.custom_patterns.append(re.compile(pattern_str))
            except re.error:
                continue

    def process(self, text: str, **kwargs) -> str:
        """
        Clean text by removing unwanted content.

        Args:
            text: Input text to clean
            **kwargs: Override config options

        Returns:
            str: Cleaned text
        """
        if not text:
            return text

        # Apply overrides from kwargs
        config = self.config

        # Remove HTML tags
        if kwargs.get("remove_html_tags", config.remove_html_tags):
            text = self.remove_html_tags(text)

        # Remove URLs
        if kwargs.get("remove_urls", config.remove_urls):
            text = self.remove_urls(text)

        # Remove emails
        if kwargs.get("remove_emails", config.remove_emails):
            text = self.remove_emails(text)

        # Remove phone numbers
        if kwargs.get("remove_phone_numbers", config.remove_phone_numbers):
            text = self.remove_phone_numbers(text)

        # Remove emojis
        if kwargs.get("remove_emojis", config.remove_emojis):
            text = self.remove_emojis(text)

        # Remove line numbers
        if kwargs.get("remove_line_numbers", config.remove_line_numbers):
            text = self.remove_line_numbers(text)

        # Remove page numbers
        if kwargs.get("remove_page_numbers", config.remove_page_numbers):
            text = self.remove_page_numbers(text)

        # Remove special characters
        if kwargs.get("remove_special_chars", config.remove_special_chars):
            chars_to_remove = kwargs.get(
                "special_chars_to_remove", config.special_chars_to_remove
            )
            preserve_chars = kwargs.get("preserve_chars", config.preserve_chars)
            text = self.remove_special_characters(text, chars_to_remove, preserve_chars)

        # Remove custom patterns
        for pattern in self.custom_patterns:
            text = pattern.sub("", text)

        # Normalize whitespace
        if kwargs.get("remove_extra_whitespace", config.remove_extra_whitespace):
            max_newlines = kwargs.get(
                "max_consecutive_newlines", config.max_consecutive_newlines
            )
            text = self.normalize_whitespace(text, max_newlines)

        # Filter short lines
        min_length = kwargs.get("min_line_length", config.min_line_length)
        if min_length > 0:
            text = self.filter_short_lines(text, min_length)

        return text.strip()

    def remove_html_tags(self, text: str) -> str:
        """Remove HTML tags from text."""
        # Also handle common HTML entities
        text = self.HTML_TAG_PATTERN.sub("", text)
        text = text.replace("&nbsp;", " ")
        text = text.replace("&amp;", "&")
        text = text.replace("&lt;", "<")
        text = text.replace("&gt;", ">")
        text = text.replace("&quot;", '"')
        text = text.replace("&#39;", "'")
        return text

    def remove_urls(self, text: str, replacement: str = "") -> str:
        """Remove URLs from text."""
        return self.URL_PATTERN.sub(replacement, text)

    def remove_emails(self, text: str, replacement: str = "") -> str:
        """Remove email addresses from text."""
        return self.EMAIL_PATTERN.sub(replacement, text)

    def remove_phone_numbers(self, text: str, replacement: str = "") -> str:
        """Remove phone numbers from text."""
        return self.PHONE_PATTERN.sub(replacement, text)

    def remove_emojis(self, text: str) -> str:
        """Remove emojis from text."""
        return self.EMOJI_PATTERN.sub("", text)

    def remove_line_numbers(self, text: str) -> str:
        """Remove line numbers from text."""
        return self.LINE_NUMBER_PATTERN.sub("", text)

    def remove_page_numbers(self, text: str) -> str:
        """Remove page numbers from text."""
        return self.PAGE_NUMBER_PATTERN.sub("", text)

    def remove_special_characters(
        self,
        text: str,
        chars_to_remove: str = "",
        preserve_chars: str = "",
    ) -> str:
        """
        Remove special characters from text.

        Args:
            text: Input text
            chars_to_remove: Specific characters to remove
            preserve_chars: Characters to preserve

        Returns:
            str: Text with special characters removed
        """
        if chars_to_remove:
            # Remove specific characters
            for char in chars_to_remove:
                text = text.replace(char, "")
        else:
            # Remove all non-alphanumeric except preserved
            preserved = set(preserve_chars)
            result = []
            for char in text:
                if char.isalnum() or char.isspace() or char in preserved:
                    result.append(char)
            text = "".join(result)
        return text

    def normalize_whitespace(self, text: str, max_consecutive_newlines: int = 2) -> str:
        """
        Normalize whitespace in text.

        Args:
            text: Input text
            max_consecutive_newlines: Maximum allowed consecutive newlines

        Returns:
            str: Text with normalized whitespace
        """
        # Replace tabs with spaces
        text = text.replace("\t", " ")

        # Normalize line endings
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        # Remove trailing whitespace from lines
        text = "\n".join(line.rstrip() for line in text.split("\n"))

        # Collapse multiple spaces
        text = re.sub(r" +", " ", text)

        # Limit consecutive newlines
        if max_consecutive_newlines > 0:
            pattern = r"\n{" + str(max_consecutive_newlines + 1) + r",}"
            replacement = "\n" * max_consecutive_newlines
            text = re.sub(pattern, replacement, text)

        return text

    def filter_short_lines(self, text: str, min_length: int) -> str:
        """
        Filter out lines shorter than minimum length.

        Args:
            text: Input text
            min_length: Minimum line length

        Returns:
            str: Text with short lines removed
        """
        lines = text.split("\n")
        filtered_lines = [line for line in lines if len(line.strip()) >= min_length]
        return "\n".join(filtered_lines)
