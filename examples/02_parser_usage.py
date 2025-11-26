#!/usr/bin/env python3
"""
Parser Usage Example - AI Document Preprocessing Parser

This example demonstrates:
1. Parser Registry usage
2. Markdown Parser
3. HTML Parser (if beautifulsoup4 is available)
4. Creating custom parsers
"""

import sys
sys.path.insert(0, '/home/user/parser')

from pathlib import Path
from src.parsers.registry import ParserRegistry
from src.parsers.base import BaseParser
from src.document import Document, DocumentMetadata, DocumentType

# =============================================================================
# 1. Parser Registry Usage
# =============================================================================
print("=" * 60)
print("1. Parser Registry Usage")
print("=" * 60)

# List available parsers
registry = ParserRegistry()
print("Available parsers:", registry.list_parsers())
print("Supported extensions:", registry.list_supported_extensions())
print()

# Check if specific extensions are supported (pass as file path)
for ext in ["test.md", "test.html", "test.pdf", "test.docx", "test.unknown"]:
    supported = registry.is_supported(ext)
    print(f"  {ext}: {'Supported' if supported else 'Not supported'}")
print()

# =============================================================================
# 2. Markdown Parser
# =============================================================================
print("=" * 60)
print("2. Markdown Parser")
print("=" * 60)

from src.parsers.markdown import MarkdownParser

# Create sample markdown content (as bytes to avoid path detection)
markdown_content = """# Sample Document

This is a sample markdown document.

## Section 1

This section contains **bold** and *italic* text.

### Subsection 1.1

- Item 1
- Item 2
- Item 3

## Section 2

Here's a code block:

```python
def hello():
    print("Hello, World!")
```

## Links and Images

Check out [this link](https://example.com) for more info.
"""

# Parse markdown (use bytes to avoid path detection)
md_parser = MarkdownParser()
print(f"Parser name: {md_parser.name}")
print(f"Supported extensions: {md_parser.supported_extensions}")
print()

doc = md_parser.parse(markdown_content.encode('utf-8'))
print(f"Document type: {doc.doc_type}")
print(f"Word count: {doc.word_count}")
print(f"Title: {doc.metadata.title}")
print()
print("Parsed content (first 300 chars):")
print(doc.content[:300])
print("...")
print()

# =============================================================================
# 3. HTML Parser (conditional)
# =============================================================================
print("=" * 60)
print("3. HTML Parser")
print("=" * 60)

try:
    import bs4
    from src.parsers.html import HTMLParser

    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Page</title>
    </head>
    <body>
        <h1>Welcome</h1>
        <p>This is a paragraph with <strong>bold</strong> text.</p>
        <ul>
            <li>Item 1</li>
            <li>Item 2</li>
        </ul>
        <script>console.log('This should be removed');</script>
    </body>
    </html>
    """

    html_parser = HTMLParser(remove_scripts=True, remove_styles=True)
    print(f"Parser name: {html_parser.name}")

    doc = html_parser.parse(html_content.encode('utf-8'))
    print(f"Document type: {doc.doc_type}")
    print(f"Title: {doc.metadata.title}")
    print()
    print("Parsed content:")
    print(doc.content)
    print()

except ImportError:
    print("beautifulsoup4 is not installed. Skipping HTML parser example.")
    print("Install with: pip install beautifulsoup4")
    print()

# =============================================================================
# 4. Custom Parser Example
# =============================================================================
print("=" * 60)
print("4. Custom Parser Example")
print("=" * 60)

from typing import Any, BinaryIO, Union
import uuid

class CSVTextParser(BaseParser):
    """Custom parser for CSV files that extracts text."""

    name = "CSVTextParser"

    def __init__(self, delimiter: str = ","):
        super().__init__()
        self.delimiter = delimiter

    @property
    def supported_extensions(self) -> list:
        """Supported file extensions."""
        return [".csv", ".CSV"]

    def supports(self, source: Union[str, Path]) -> bool:
        """Check if this parser supports the given file."""
        path = Path(source)
        return path.suffix.lower() in [".csv"]

    def parse(
        self,
        source: Union[str, Path, BinaryIO, bytes],
        **kwargs: Any,
    ) -> Document:
        """Parse CSV and return as text document."""
        # Handle different input types
        if isinstance(source, bytes):
            content = source.decode("utf-8")
        elif isinstance(source, (str, Path)):
            path = Path(source)
            if path.exists():
                content = path.read_text()
            else:
                content = source if isinstance(source, str) else ""
        else:
            content = source.read().decode("utf-8")

        # Parse CSV lines
        lines = content.strip().split("\n")
        text_lines = []

        for line in lines:
            cells = line.split(self.delimiter)
            text_lines.append(" | ".join(cells))

        parsed_content = "\n".join(text_lines)

        return Document(
            id=str(uuid.uuid4()),
            content=parsed_content,
            doc_type=DocumentType.TEXT,
            metadata=DocumentMetadata(
                title="CSV Document",
                word_count=len(parsed_content.split()),
            ),
        )

# Register custom parser (using class method)
ParserRegistry.register("csv", CSVTextParser, extensions=[".csv"])
print(f"Registered custom parser: CSVTextParser")
print(f"Available parsers: {registry.list_parsers()}")
print()

# Use custom parser
csv_content = "name,age,city\nAlice,30,Seoul\nBob,25,Busan"
csv_parser = CSVTextParser()
doc = csv_parser.parse(csv_content)
print("Parsed CSV content:")
print(doc.content)
print()

# =============================================================================
# 5. Auto Parser Selection
# =============================================================================
print("=" * 60)
print("5. Auto Parser Selection")
print("=" * 60)

# Get parser for file extension
for name in ["markdown", "csv"]:
    try:
        parser = registry.get_parser(name)
        print(f"{name}: {parser.name}")
    except KeyError:
        print(f"{name}: No parser found")

print()
print("=" * 60)
print("Parser Usage Example Complete!")
print("=" * 60)
