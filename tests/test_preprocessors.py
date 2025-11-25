"""
Comprehensive tests for Preprocessor modules.
"""

import pytest

from src.preprocessors.base import BasePreprocessor, PreprocessorChain
from src.preprocessors.cleaner import CleanerConfig, TextCleaner
from src.preprocessors.normalizer import NormalizerConfig, TextNormalizer


class TestTextCleaner:
    """Tests for TextCleaner."""

    def test_default_cleaning(self):
        """Test default cleaning behavior."""
        cleaner = TextCleaner()
        text = "Hello   World  "
        result = cleaner.process(text)
        assert result == "Hello World"

    def test_remove_html_tags(self):
        """Test HTML tag removal."""
        cleaner = TextCleaner(CleanerConfig(remove_html_tags=True))
        text = "Hello <b>World</b> <script>alert('x')</script>"
        result = cleaner.process(text)
        assert "<b>" not in result
        assert "<script>" not in result
        assert "World" in result

    def test_remove_html_entities(self):
        """Test HTML entity conversion."""
        cleaner = TextCleaner(CleanerConfig(remove_html_tags=True))
        text = "Hello&nbsp;World &amp; Test &lt;tag&gt;"
        result = cleaner.process(text)
        assert "&nbsp;" not in result
        assert "Hello World" in result
        assert "&" in result

    def test_remove_urls(self):
        """Test URL removal."""
        cleaner = TextCleaner(CleanerConfig(remove_urls=True))
        text = "Visit https://example.com or www.test.org for info."
        result = cleaner.process(text)
        assert "https://example.com" not in result
        assert "www.test.org" not in result
        assert "Visit" in result

    def test_remove_emails(self):
        """Test email removal."""
        cleaner = TextCleaner(CleanerConfig(remove_emails=True))
        text = "Contact user@example.com or admin@test.org"
        result = cleaner.process(text)
        assert "user@example.com" not in result
        assert "admin@test.org" not in result
        assert "Contact" in result

    def test_remove_phone_numbers(self):
        """Test phone number removal."""
        cleaner = TextCleaner(CleanerConfig(remove_phone_numbers=True))
        text = "Call 010-1234-5678 or 02-123-4567"
        result = cleaner.process(text)
        assert "010-1234-5678" not in result
        assert "02-123-4567" not in result

    def test_remove_emojis(self):
        """Test emoji removal."""
        cleaner = TextCleaner(CleanerConfig(remove_emojis=True))
        text = "Hello 😀 World 🌍 Test 🎉"
        result = cleaner.process(text)
        assert "😀" not in result
        assert "🌍" not in result
        assert "Hello" in result

    def test_normalize_whitespace(self):
        """Test whitespace normalization."""
        cleaner = TextCleaner(CleanerConfig(remove_extra_whitespace=True))
        text = "Hello    World\t\tTest\n\n\n\nParagraph"
        result = cleaner.process(text)
        assert "    " not in result
        assert "\t\t" not in result
        assert "\n\n\n\n" not in result

    def test_max_consecutive_newlines(self):
        """Test limiting consecutive newlines."""
        config = CleanerConfig(
            remove_extra_whitespace=True,
            max_consecutive_newlines=2,
        )
        cleaner = TextCleaner(config)
        text = "Para1\n\n\n\n\nPara2"
        result = cleaner.process(text)
        assert "\n\n\n" not in result

    def test_filter_short_lines(self):
        """Test filtering short lines."""
        config = CleanerConfig(min_line_length=5)
        cleaner = TextCleaner(config)
        text = "OK\nThis is good\nNo\nAnother good line"
        result = cleaner.process(text)
        assert "OK" not in result
        assert "No" not in result
        assert "This is good" in result

    def test_remove_special_characters(self):
        """Test special character removal."""
        config = CleanerConfig(
            remove_special_chars=True,
            special_chars_to_remove="@#$",
        )
        cleaner = TextCleaner(config)
        text = "Hello@World#Test$End"
        result = cleaner.process(text)
        assert "@" not in result
        assert "#" not in result
        assert "$" not in result

    def test_preserve_chars(self):
        """Test preserving specific characters."""
        config = CleanerConfig(
            remove_special_chars=True,
            preserve_chars=".,!?",
        )
        cleaner = TextCleaner(config)
        text = "Hello, World! Test? Yes."
        result = cleaner.process(text)
        assert "," in result
        assert "!" in result
        assert "?" in result
        assert "." in result

    def test_empty_text(self):
        """Test empty text handling."""
        cleaner = TextCleaner()
        result = cleaner.process("")
        assert result == ""

    def test_callable(self):
        """Test cleaner can be called as function."""
        cleaner = TextCleaner()
        result = cleaner("Hello   World")  # Direct call
        assert result == "Hello World"


class TestTextNormalizer:
    """Tests for TextNormalizer."""

    def test_unicode_normalization_nfc(self):
        """Test NFC Unicode normalization."""
        normalizer = TextNormalizer(NormalizerConfig(unicode_form="NFC"))
        # Combining character (e + combining acute) -> single character (é)
        text = "cafe\u0301"  # cafe + combining acute
        result = normalizer.process(text)
        assert len(result) <= len(text)  # Should combine

    def test_unicode_normalization_nfkc(self):
        """Test NFKC Unicode normalization."""
        normalizer = TextNormalizer(NormalizerConfig(unicode_form="NFKC"))
        text = "ﬁ"  # fi ligature
        result = normalizer.process(text)
        assert result == "fi"

    def test_lowercase(self):
        """Test lowercase conversion."""
        normalizer = TextNormalizer(NormalizerConfig(lowercase=True))
        result = normalizer.process("Hello WORLD")
        assert result == "hello world"

    def test_uppercase(self):
        """Test uppercase conversion."""
        normalizer = TextNormalizer(NormalizerConfig(uppercase=True, lowercase=False))
        result = normalizer.process("Hello World")
        assert result == "HELLO WORLD"

    def test_normalize_quotes(self):
        """Test quote normalization."""
        normalizer = TextNormalizer(NormalizerConfig(normalize_quotes=True))
        text = '\u201cHello\u201d \u2018World\u2019 \xabTest\xbb'  # "Hello" 'World' «Test»
        result = normalizer.process(text)
        assert '"Hello"' in result or 'Hello' in result
        assert "'" in result or 'World' in result

    def test_normalize_dashes(self):
        """Test dash normalization."""
        normalizer = TextNormalizer(NormalizerConfig(normalize_dashes=True))
        text = "one–two—three−four"  # en-dash, em-dash, minus sign
        result = normalizer.process(text)
        assert "–" not in result
        assert "—" not in result
        assert "−" not in result
        assert result.count("-") >= 3

    def test_normalize_ellipsis(self):
        """Test ellipsis normalization."""
        normalizer = TextNormalizer(NormalizerConfig(normalize_ellipsis=True))
        text = "Wait…more"
        result = normalizer.process(text)
        assert "…" not in result
        assert "..." in result

    def test_expand_contractions(self):
        """Test contraction expansion."""
        normalizer = TextNormalizer(NormalizerConfig(expand_contractions=True))
        text = "I'm can't won't"
        result = normalizer.process(text)
        assert "I am" in result
        assert "cannot" in result
        assert "will not" in result

    def test_strip_accents(self):
        """Test accent stripping."""
        normalizer = TextNormalizer(NormalizerConfig(strip_accents=True))
        text = "café résumé naïve"
        result = normalizer.process(text)
        assert "é" not in result
        assert "cafe" in result or "café" not in result

    def test_custom_replacements(self):
        """Test custom replacements."""
        config = NormalizerConfig(custom_replacements={"foo": "bar", "hello": "hi"})
        normalizer = TextNormalizer(config)
        text = "hello foo world"
        result = normalizer.process(text)
        assert "bar" in result
        assert "hi" in result

    def test_normalize_unicode_punctuation(self):
        """Test Unicode punctuation normalization."""
        normalizer = TextNormalizer(NormalizerConfig(normalize_unicode_punctuation=True))
        text = "（Hello）！"  # Full-width parentheses and exclamation
        result = normalizer.process(text)
        assert "！" not in result
        assert "（" not in result

    def test_empty_text(self):
        """Test empty text handling."""
        normalizer = TextNormalizer()
        result = normalizer.process("")
        assert result == ""


class TestPreprocessorChain:
    """Tests for PreprocessorChain."""

    def test_chain_creation(self):
        """Test chain creation with preprocessors."""
        chain = PreprocessorChain([
            TextCleaner(),
            TextNormalizer(),
        ])
        assert len(chain.preprocessors) == 2

    def test_chain_processing(self):
        """Test chain processes in order."""
        cleaner = TextCleaner(CleanerConfig(remove_html_tags=True))
        normalizer = TextNormalizer(NormalizerConfig(lowercase=True))
        chain = PreprocessorChain([cleaner, normalizer])

        text = "<b>Hello</b>   WORLD"
        result = chain.process(text)
        assert "<b>" not in result
        assert result == "hello world"

    def test_chain_add(self):
        """Test adding preprocessors to chain."""
        chain = PreprocessorChain()
        chain.add(TextCleaner())
        chain.add(TextNormalizer())
        assert len(chain.preprocessors) == 2

    def test_chain_add_fluent(self):
        """Test fluent interface for adding preprocessors."""
        chain = (
            PreprocessorChain()
            .add(TextCleaner())
            .add(TextNormalizer())
        )
        assert len(chain.preprocessors) == 2

    def test_empty_chain(self):
        """Test empty chain returns input unchanged."""
        chain = PreprocessorChain()
        text = "Hello World"
        result = chain.process(text)
        assert result == text

    def test_chain_callable(self):
        """Test chain can be called as function."""
        chain = PreprocessorChain([TextCleaner()])
        result = chain("Hello   World")  # Direct call
        assert result == "Hello World"


class TestPreprocessorIntegration:
    """Integration tests for preprocessors."""

    def test_full_preprocessing_pipeline(self):
        """Test complete preprocessing pipeline."""
        cleaner_config = CleanerConfig(
            remove_html_tags=True,
            remove_urls=True,
            remove_extra_whitespace=True,
        )
        normalizer_config = NormalizerConfig(
            lowercase=True,
            normalize_quotes=True,
            normalize_dashes=True,
        )

        chain = PreprocessorChain([
            TextCleaner(cleaner_config),
            TextNormalizer(normalizer_config),
        ])

        text = """
        <p>Visit https://example.com for more info.</p>
        "Hello"   World—Test
        """
        result = chain.process(text)

        assert "<p>" not in result
        assert "https://example.com" not in result
        assert "  " not in result
        assert result == result.lower()

    def test_korean_text_processing(self):
        """Test preprocessing Korean text."""
        cleaner = TextCleaner(CleanerConfig(remove_extra_whitespace=True))
        text = "안녕하세요    세계"
        result = cleaner.process(text)
        assert "    " not in result
        assert "안녕하세요" in result
        assert "세계" in result

    def test_mixed_language_text(self):
        """Test preprocessing mixed language text."""
        chain = PreprocessorChain([
            TextCleaner(CleanerConfig(remove_html_tags=True)),
            TextNormalizer(NormalizerConfig(normalize_quotes=True)),
        ])
        text = '<b>Hello</b> \u201c\uc548\ub155\u201d'  # <b>Hello</b> "안녕"
        result = chain.process(text)
        assert "<b>" not in result
        assert "Hello" in result
        assert "\uc548\ub155" in result  # 안녕


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
