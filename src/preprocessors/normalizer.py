"""
Text normalizer for standardizing text content.
"""

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from src.preprocessors.base import BasePreprocessor


@dataclass
class NormalizerConfig:
    """Configuration for text normalizer."""

    unicode_form: str = "NFC"  # NFC, NFKC, NFD, NFKD
    lowercase: bool = False
    uppercase: bool = False
    strip_accents: bool = False
    normalize_quotes: bool = True
    normalize_dashes: bool = True
    normalize_ellipsis: bool = True
    normalize_numbers: bool = False
    number_format: str = "digit"  # digit, word
    expand_contractions: bool = False
    custom_replacements: Dict[str, str] = field(default_factory=dict)
    normalize_unicode_punctuation: bool = True


class TextNormalizer(BasePreprocessor):
    """
    Text normalizer for standardizing text content.

    Supports Unicode normalization, case conversion, quote normalization, etc.
    """

    # Common contractions (English)
    CONTRACTIONS = {
        "ain't": "is not",
        "aren't": "are not",
        "can't": "cannot",
        "couldn't": "could not",
        "didn't": "did not",
        "doesn't": "does not",
        "don't": "do not",
        "hadn't": "had not",
        "hasn't": "has not",
        "haven't": "have not",
        "he'd": "he would",
        "he'll": "he will",
        "he's": "he is",
        "i'd": "I would",
        "i'll": "I will",
        "i'm": "I am",
        "i've": "I have",
        "isn't": "is not",
        "it'd": "it would",
        "it'll": "it will",
        "it's": "it is",
        "let's": "let us",
        "mightn't": "might not",
        "mustn't": "must not",
        "shan't": "shall not",
        "she'd": "she would",
        "she'll": "she will",
        "she's": "she is",
        "shouldn't": "should not",
        "that's": "that is",
        "there's": "there is",
        "they'd": "they would",
        "they'll": "they will",
        "they're": "they are",
        "they've": "they have",
        "we'd": "we would",
        "we're": "we are",
        "we've": "we have",
        "weren't": "were not",
        "what'll": "what will",
        "what're": "what are",
        "what's": "what is",
        "what've": "what have",
        "where's": "where is",
        "who'd": "who would",
        "who'll": "who will",
        "who're": "who are",
        "who's": "who is",
        "who've": "who have",
        "won't": "will not",
        "wouldn't": "would not",
        "you'd": "you would",
        "you'll": "you will",
        "you're": "you are",
        "you've": "you have",
    }

    # Quote normalization mappings
    QUOTE_MAPPINGS = {
        """: '"',
        """: '"',
        "'": "'",
        "'": "'",
        "«": '"',
        "»": '"',
        "‹": "'",
        "›": "'",
        "„": '"',
        "‚": "'",
    }

    # Dash normalization mappings
    DASH_MAPPINGS = {
        "–": "-",  # en dash
        "—": "-",  # em dash
        "−": "-",  # minus sign
        "‐": "-",  # hyphen
        "‑": "-",  # non-breaking hyphen
        "‒": "-",  # figure dash
        "⁃": "-",  # hyphen bullet
    }

    # Number words (for normalization)
    NUMBER_WORDS = {
        "0": "zero",
        "1": "one",
        "2": "two",
        "3": "three",
        "4": "four",
        "5": "five",
        "6": "six",
        "7": "seven",
        "8": "eight",
        "9": "nine",
    }

    def __init__(self, config: Optional[NormalizerConfig] = None):
        """
        Initialize text normalizer.

        Args:
            config: Normalizer configuration
        """
        self.config = config or NormalizerConfig()

    def process(self, text: str, **kwargs) -> str:
        """
        Normalize text according to configuration.

        Args:
            text: Input text to normalize
            **kwargs: Override config options

        Returns:
            str: Normalized text
        """
        if not text:
            return text

        config = self.config

        # Unicode normalization
        unicode_form = kwargs.get("unicode_form", config.unicode_form)
        if unicode_form:
            text = self.normalize_unicode(text, unicode_form)

        # Strip accents
        if kwargs.get("strip_accents", config.strip_accents):
            text = self.strip_accents(text)

        # Normalize Unicode punctuation
        if kwargs.get("normalize_unicode_punctuation", config.normalize_unicode_punctuation):
            text = self.normalize_unicode_punctuation(text)

        # Normalize quotes
        if kwargs.get("normalize_quotes", config.normalize_quotes):
            text = self.normalize_quotes(text)

        # Normalize dashes
        if kwargs.get("normalize_dashes", config.normalize_dashes):
            text = self.normalize_dashes(text)

        # Normalize ellipsis
        if kwargs.get("normalize_ellipsis", config.normalize_ellipsis):
            text = self.normalize_ellipsis(text)

        # Expand contractions
        if kwargs.get("expand_contractions", config.expand_contractions):
            text = self.expand_contractions(text)

        # Normalize numbers
        if kwargs.get("normalize_numbers", config.normalize_numbers):
            number_format = kwargs.get("number_format", config.number_format)
            text = self.normalize_numbers(text, number_format)

        # Case conversion
        if kwargs.get("lowercase", config.lowercase):
            text = text.lower()
        elif kwargs.get("uppercase", config.uppercase):
            text = text.upper()

        # Custom replacements
        replacements = kwargs.get("custom_replacements", config.custom_replacements)
        for old, new in replacements.items():
            text = text.replace(old, new)

        return text

    def normalize_unicode(self, text: str, form: str = "NFC") -> str:
        """
        Apply Unicode normalization.

        Args:
            text: Input text
            form: Normalization form (NFC, NFKC, NFD, NFKD)

        Returns:
            str: Normalized text
        """
        if form not in ("NFC", "NFKC", "NFD", "NFKD"):
            form = "NFC"
        return unicodedata.normalize(form, text)

    def strip_accents(self, text: str) -> str:
        """
        Remove accents/diacritics from text.

        Args:
            text: Input text

        Returns:
            str: Text without accents
        """
        # Decompose characters
        nfkd = unicodedata.normalize("NFKD", text)
        # Keep only non-combining characters
        return "".join(c for c in nfkd if not unicodedata.combining(c))

    def normalize_unicode_punctuation(self, text: str) -> str:
        """
        Normalize Unicode punctuation to ASCII equivalents.

        Args:
            text: Input text

        Returns:
            str: Text with normalized punctuation
        """
        # Full-width to half-width
        text = text.translate(str.maketrans(
            "！＂＃＄％＆＇（）＊＋，－．／：；＜＝＞？＠［＼］＾＿｀｛｜｝～",
            "!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~",
        ))
        return text

    def normalize_quotes(self, text: str) -> str:
        """
        Normalize various quote characters to standard ASCII.

        Args:
            text: Input text

        Returns:
            str: Text with normalized quotes
        """
        for old, new in self.QUOTE_MAPPINGS.items():
            text = text.replace(old, new)
        return text

    def normalize_dashes(self, text: str) -> str:
        """
        Normalize various dash characters to standard hyphen.

        Args:
            text: Input text

        Returns:
            str: Text with normalized dashes
        """
        for old, new in self.DASH_MAPPINGS.items():
            text = text.replace(old, new)
        return text

    def normalize_ellipsis(self, text: str) -> str:
        """
        Normalize ellipsis characters.

        Args:
            text: Input text

        Returns:
            str: Text with normalized ellipsis
        """
        # Replace Unicode ellipsis with three dots
        text = text.replace("…", "...")
        # Normalize multiple dots
        text = re.sub(r"\.{4,}", "...", text)
        return text

    def expand_contractions(self, text: str) -> str:
        """
        Expand English contractions.

        Args:
            text: Input text

        Returns:
            str: Text with expanded contractions
        """
        # Create pattern for case-insensitive matching
        pattern = re.compile(
            r"\b(" + "|".join(re.escape(k) for k in self.CONTRACTIONS.keys()) + r")\b",
            re.IGNORECASE,
        )

        def replace_contraction(match):
            word = match.group(0)
            lower = word.lower()
            replacement = self.CONTRACTIONS.get(lower, word)
            # Preserve case
            if word[0].isupper():
                replacement = replacement.capitalize()
            return replacement

        return pattern.sub(replace_contraction, text)

    def normalize_numbers(self, text: str, format: str = "digit") -> str:
        """
        Normalize numbers in text.

        Args:
            text: Input text
            format: "digit" or "word"

        Returns:
            str: Text with normalized numbers
        """
        if format == "word":
            # Convert single digits to words
            for digit, word in self.NUMBER_WORDS.items():
                text = re.sub(rf"\b{digit}\b", word, text)
        return text
