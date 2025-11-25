"""
Base preprocessor interface for text preprocessing.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class BasePreprocessor(ABC):
    """Abstract base class for all text preprocessors."""

    @abstractmethod
    def process(self, text: str, **kwargs) -> str:
        """
        Process and transform text.

        Args:
            text: Input text to process
            **kwargs: Preprocessor-specific options

        Returns:
            str: Processed text
        """
        pass

    @property
    def name(self) -> str:
        """Get the preprocessor name."""
        return self.__class__.__name__

    def __call__(self, text: str, **kwargs) -> str:
        """Allow calling preprocessor as a function."""
        return self.process(text, **kwargs)


class PreprocessorChain:
    """Chain multiple preprocessors together."""

    def __init__(self, preprocessors: list[BasePreprocessor] | None = None):
        """
        Initialize preprocessor chain.

        Args:
            preprocessors: List of preprocessors to chain
        """
        self.preprocessors = preprocessors or []

    def add(self, preprocessor: BasePreprocessor) -> "PreprocessorChain":
        """Add a preprocessor to the chain."""
        self.preprocessors.append(preprocessor)
        return self

    def process(self, text: str, **kwargs) -> str:
        """
        Process text through all preprocessors in chain.

        Args:
            text: Input text
            **kwargs: Options passed to all preprocessors

        Returns:
            str: Processed text
        """
        result = text
        for preprocessor in self.preprocessors:
            result = preprocessor.process(result, **kwargs)
        return result

    def __call__(self, text: str, **kwargs) -> str:
        """Allow calling chain as a function."""
        return self.process(text, **kwargs)
