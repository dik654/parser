"""
Output formatters for document conversion.
"""

import csv
import json
from io import StringIO
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Union

from src.document import Document, TextChunk


class JSONFormatter:
    """Format documents as JSON."""

    def __init__(
        self,
        indent: int = 2,
        ensure_ascii: bool = False,
        include_raw: bool = False,
    ):
        """
        Initialize JSON formatter.

        Args:
            indent: JSON indentation
            ensure_ascii: Whether to escape non-ASCII characters
            include_raw: Whether to include raw content
        """
        self.indent = indent
        self.ensure_ascii = ensure_ascii
        self.include_raw = include_raw

    def format(self, document: Document) -> str:
        """
        Format document as JSON string.

        Args:
            document: Document to format

        Returns:
            JSON string
        """
        data = document.to_dict(include_raw=self.include_raw)
        return json.dumps(
            data,
            indent=self.indent,
            ensure_ascii=self.ensure_ascii,
        )

    def format_many(self, documents: List[Document]) -> str:
        """
        Format multiple documents as JSON array.

        Args:
            documents: Documents to format

        Returns:
            JSON array string
        """
        data = [doc.to_dict(include_raw=self.include_raw) for doc in documents]
        return json.dumps(
            data,
            indent=self.indent,
            ensure_ascii=self.ensure_ascii,
        )

    def save(
        self,
        document: Document,
        path: Union[str, Path],
    ) -> None:
        """Save document to JSON file."""
        path = Path(path)
        path.write_text(self.format(document))


class JSONLFormatter:
    """Format documents as JSON Lines (JSONL)."""

    def __init__(
        self,
        ensure_ascii: bool = False,
        include_raw: bool = False,
    ):
        """
        Initialize JSONL formatter.

        Args:
            ensure_ascii: Whether to escape non-ASCII characters
            include_raw: Whether to include raw content
        """
        self.ensure_ascii = ensure_ascii
        self.include_raw = include_raw

    def format(self, document: Document) -> str:
        """
        Format document as single JSON line.

        Args:
            document: Document to format

        Returns:
            JSON line string
        """
        data = document.to_dict(include_raw=self.include_raw)
        return json.dumps(data, ensure_ascii=self.ensure_ascii)

    def format_many(self, documents: List[Document]) -> str:
        """
        Format multiple documents as JSONL.

        Args:
            documents: Documents to format

        Returns:
            JSONL string
        """
        lines = [self.format(doc) for doc in documents]
        return "\n".join(lines)

    def iter_format(self, documents: Iterator[Document]) -> Iterator[str]:
        """
        Iterate formatted lines (memory efficient).

        Args:
            documents: Document iterator

        Yields:
            JSON line strings
        """
        for doc in documents:
            yield self.format(doc)

    def save(
        self,
        documents: List[Document],
        path: Union[str, Path],
    ) -> None:
        """Save documents to JSONL file."""
        path = Path(path)
        with path.open("w") as f:
            for doc in documents:
                f.write(self.format(doc) + "\n")


class CSVFormatter:
    """Format document metadata as CSV."""

    DEFAULT_COLUMNS = [
        "id",
        "title",
        "author",
        "doc_type",
        "word_count",
        "char_count",
        "chunk_count",
        "source_path",
    ]

    def __init__(
        self,
        columns: Optional[List[str]] = None,
        include_custom: bool = False,
    ):
        """
        Initialize CSV formatter.

        Args:
            columns: Columns to include (default set if None)
            include_custom: Whether to include custom metadata fields
        """
        self.columns = columns or self.DEFAULT_COLUMNS
        self.include_custom = include_custom

    def format(self, documents: List[Document]) -> str:
        """
        Format documents as CSV string.

        Args:
            documents: Documents to format

        Returns:
            CSV string
        """
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=self._get_columns(documents))
        writer.writeheader()

        for doc in documents:
            row = self._document_to_row(doc)
            writer.writerow(row)

        return output.getvalue()

    def _get_columns(self, documents: List[Document]) -> List[str]:
        """Get columns including custom fields if enabled."""
        columns = list(self.columns)

        if self.include_custom and documents:
            for doc in documents:
                if doc.metadata.custom:
                    for key in doc.metadata.custom.keys():
                        if key not in columns:
                            columns.append(key)

        return columns

    def _document_to_row(self, doc: Document) -> Dict[str, Any]:
        """Convert document to CSV row."""
        row = {}

        for col in self.columns:
            if col == "id":
                row[col] = doc.id
            elif col == "doc_type":
                row[col] = doc.doc_type.value
            elif col == "word_count":
                row[col] = doc.word_count
            elif col == "char_count":
                row[col] = doc.char_count
            elif col == "chunk_count":
                row[col] = doc.chunk_count
            elif hasattr(doc.metadata, col):
                value = getattr(doc.metadata, col)
                row[col] = value if value is not None else ""

        if self.include_custom and doc.metadata.custom:
            for key, value in doc.metadata.custom.items():
                if key not in row:
                    row[key] = str(value) if value is not None else ""

        return row

    def save(
        self,
        documents: List[Document],
        path: Union[str, Path],
    ) -> None:
        """Save documents metadata to CSV file."""
        path = Path(path)
        path.write_text(self.format(documents))


class LangChainFormatter:
    """Format documents for LangChain compatibility."""

    def format(self, document: Document) -> List[Dict[str, Any]]:
        """
        Format document as LangChain Document format.

        Args:
            document: Document to format

        Returns:
            List of LangChain-compatible document dicts
        """
        if document.chunks:
            # Return one document per chunk
            return [
                {
                    "page_content": chunk.content,
                    "metadata": {
                        "source": document.metadata.source_path,
                        "doc_id": document.id,
                        "chunk_index": chunk.index,
                        "start_char": chunk.start_char,
                        "end_char": chunk.end_char,
                        "page_number": chunk.page_number,
                        **chunk.metadata,
                    },
                }
                for chunk in document.chunks
            ]
        else:
            # Return whole document
            return [
                {
                    "page_content": document.content,
                    "metadata": {
                        "source": document.metadata.source_path,
                        "doc_id": document.id,
                        **document.metadata.to_dict(),
                    },
                }
            ]

    def format_many(self, documents: List[Document]) -> List[Dict[str, Any]]:
        """
        Format multiple documents.

        Args:
            documents: Documents to format

        Returns:
            List of LangChain-compatible document dicts
        """
        result = []
        for doc in documents:
            result.extend(self.format(doc))
        return result

    def to_langchain_documents(self, document: Document):
        """
        Convert to actual LangChain Document objects.

        Args:
            document: Document to convert

        Returns:
            List of LangChain Document objects
        """
        try:
            from langchain_core.documents import Document as LCDocument
        except ImportError:
            raise ImportError(
                "langchain-core is required. "
                "Install with: pip install langchain-core"
            )

        formatted = self.format(document)
        return [
            LCDocument(
                page_content=d["page_content"],
                metadata=d["metadata"],
            )
            for d in formatted
        ]


class LlamaIndexFormatter:
    """Format documents for LlamaIndex compatibility."""

    def format(self, document: Document) -> List[Dict[str, Any]]:
        """
        Format document as LlamaIndex Document format.

        Args:
            document: Document to format

        Returns:
            List of LlamaIndex-compatible document dicts
        """
        if document.chunks:
            return [
                {
                    "text": chunk.content,
                    "doc_id": f"{document.id}_{chunk.index}",
                    "extra_info": {
                        "source": document.metadata.source_path,
                        "parent_doc_id": document.id,
                        "chunk_index": chunk.index,
                        "start_char": chunk.start_char,
                        "end_char": chunk.end_char,
                    },
                }
                for chunk in document.chunks
            ]
        else:
            return [
                {
                    "text": document.content,
                    "doc_id": document.id,
                    "extra_info": document.metadata.to_dict(),
                }
            ]

    def to_llama_documents(self, document: Document):
        """
        Convert to actual LlamaIndex Document objects.

        Args:
            document: Document to convert

        Returns:
            List of LlamaIndex Document objects
        """
        try:
            from llama_index.core import Document as LIDocument
        except ImportError:
            raise ImportError(
                "llama-index is required. "
                "Install with: pip install llama-index"
            )

        formatted = self.format(document)
        return [
            LIDocument(
                text=d["text"],
                doc_id=d["doc_id"],
                extra_info=d.get("extra_info", {}),
            )
            for d in formatted
        ]
