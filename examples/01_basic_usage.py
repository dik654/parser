#!/usr/bin/env python3
"""
Basic Usage Example - AI Document Preprocessing Parser

This example demonstrates:
1. Document model usage
2. Text preprocessing (cleaning, normalizing)
3. Text chunking strategies
4. Output formatting
"""

import sys
sys.path.insert(0, '/home/user/parser')

from src.document import Document, DocumentMetadata, DocumentType, TextChunk

# =============================================================================
# 1. Document Model Usage
# =============================================================================
print("=" * 60)
print("1. Document Model Usage")
print("=" * 60)

# Create a document
doc = Document(
    id="doc-001",
    content="This is a sample document.\n\nIt has multiple paragraphs.\n\nThird paragraph here.",
    doc_type=DocumentType.TEXT,
    metadata=DocumentMetadata(
        title="Sample Document",
        author="Test Author",
        source_path="example.txt",
    )
)

print(f"Document Type: {doc.doc_type}")
print(f"Title: {doc.metadata.title}")
print(f"Author: {doc.metadata.author}")
print(f"Content length: {len(doc.content)} characters")
print(f"Word count: {doc.word_count}")
print()

# Serialization
json_str = doc.to_json()
print("JSON serialization:")
print(json_str[:200] + "..." if len(json_str) > 200 else json_str)
print()

# =============================================================================
# 2. Text Preprocessing
# =============================================================================
print("=" * 60)
print("2. Text Preprocessing")
print("=" * 60)

from src.preprocessors.cleaner import TextCleaner, CleanerConfig
from src.preprocessors.normalizer import TextNormalizer, NormalizerConfig
from src.preprocessors.base import PreprocessorChain

# Sample text with various issues
dirty_text = """
<p>Hello World!</p>

Contact us at test@example.com or visit https://example.com

Phone: 123-456-7890

This has   multiple   spaces and	tabs.

"""

print("Original text:")
print(repr(dirty_text[:100]))
print()

# Clean the text
cleaner = TextCleaner(CleanerConfig(
    remove_html_tags=True,
    remove_urls=True,
    remove_emails=True,
    remove_extra_whitespace=True,
    max_consecutive_newlines=2,
))

cleaned_text = cleaner.process(dirty_text)
print("After cleaning:")
print(repr(cleaned_text))
print()

# Normalize the text
normalizer = TextNormalizer(NormalizerConfig(
    unicode_form="NFC",
    lowercase=True,
))

normalized_text = normalizer.process(cleaned_text)
print("After normalization:")
print(repr(normalized_text))
print()

# Use a preprocessing chain
chain = PreprocessorChain([cleaner, normalizer])
result = chain.process(dirty_text)
print("Using PreprocessorChain (combined):")
print(repr(result))
print()

# =============================================================================
# 3. Text Chunking
# =============================================================================
print("=" * 60)
print("3. Text Chunking Strategies")
print("=" * 60)

from src.chunkers.fixed import FixedSizeChunker
from src.chunkers.recursive import RecursiveChunker
from src.chunkers.sentence import SentenceChunker, ParagraphChunker
from src.chunkers.semantic import SlidingWindowChunker

sample_text = """
Natural language processing (NLP) is a subfield of linguistics, computer science, and artificial intelligence concerned with the interactions between computers and human language.

In particular, NLP is concerned with how to program computers to process and analyze large amounts of natural language data. The result is a computer capable of understanding the contents of documents.

Challenges in natural language processing frequently involve speech recognition, natural language understanding, and natural language generation. Natural language processing has overlap with computational linguistics.
"""

print("Original text length:", len(sample_text), "characters")
print()

# Fixed-size chunker
print("--- Fixed Size Chunker (100 chars, 20 overlap) ---")
fixed_chunker = FixedSizeChunker(chunk_size=100, chunk_overlap=20, min_chunk_size=10)
chunks = fixed_chunker.chunk(sample_text)
print(f"Number of chunks: {len(chunks)}")
for i, chunk in enumerate(chunks[:3]):
    print(f"  Chunk {i}: {chunk.length} chars - '{chunk.content[:50]}...'")
print()

# Recursive chunker
print("--- Recursive Chunker (150 chars) ---")
recursive_chunker = RecursiveChunker(chunk_size=150, chunk_overlap=30, min_chunk_size=20)
chunks = recursive_chunker.chunk(sample_text)
print(f"Number of chunks: {len(chunks)}")
for i, chunk in enumerate(chunks[:3]):
    print(f"  Chunk {i}: {chunk.length} chars - '{chunk.content[:50]}...'")
print()

# Sentence chunker
print("--- Sentence Chunker ---")
sentence_chunker = SentenceChunker(chunk_size=200, chunk_overlap=0, min_chunk_size=10)
chunks = sentence_chunker.chunk(sample_text)
print(f"Number of chunks: {len(chunks)}")
for i, chunk in enumerate(chunks[:3]):
    print(f"  Chunk {i}: {chunk.length} chars - '{chunk.content[:50]}...'")
print()

# Paragraph chunker
print("--- Paragraph Chunker ---")
paragraph_chunker = ParagraphChunker(chunk_size=500, chunk_overlap=0, min_chunk_size=10)
chunks = paragraph_chunker.chunk(sample_text)
print(f"Number of chunks: {len(chunks)}")
for i, chunk in enumerate(chunks):
    print(f"  Chunk {i}: {chunk.length} chars - '{chunk.content[:50]}...'")
print()

# Sliding window chunker
print("--- Sliding Window Chunker (80 window, 40 step) ---")
sliding_chunker = SlidingWindowChunker(window_size=80, step_size=40)
chunks = sliding_chunker.chunk(sample_text)
print(f"Number of chunks: {len(chunks)}")
for i, chunk in enumerate(chunks[:3]):
    print(f"  Chunk {i}: {chunk.length} chars - '{chunk.content[:40]}...'")
print()

# =============================================================================
# 4. Output Formatting
# =============================================================================
print("=" * 60)
print("4. Output Formatting")
print("=" * 60)

from src.utils.formatters import (
    JSONFormatter,
    JSONLFormatter,
    CSVFormatter,
    LangChainFormatter,
    LlamaIndexFormatter,
)

# Create a document with chunks
doc_with_chunks = Document(
    id="doc-002",
    content=sample_text,
    doc_type=DocumentType.TEXT,
    metadata=DocumentMetadata(title="NLP Document", source_path="example.txt"),
    chunks=chunks[:3],  # Use first 3 chunks
)

# JSON format
print("--- JSON Format ---")
json_formatter = JSONFormatter(indent=2)
json_output = json_formatter.format(doc_with_chunks)
print(json_output[:300] + "..." if len(json_output) > 300 else json_output)
print()

# LangChain format
print("--- LangChain Document Format ---")
langchain_formatter = LangChainFormatter()
lc_docs = langchain_formatter.format(doc_with_chunks)
print(f"Number of LangChain documents: {len(lc_docs)}")
for i, lc_doc in enumerate(lc_docs[:2]):
    print(f"  Doc {i}: page_content='{lc_doc['page_content'][:50]}...', metadata={list(lc_doc['metadata'].keys())}")
print()

# LlamaIndex format
print("--- LlamaIndex Document Format ---")
llamaindex_formatter = LlamaIndexFormatter()
li_docs = llamaindex_formatter.format(doc_with_chunks)
print(f"Number of LlamaIndex documents: {len(li_docs)}")
for i, li_doc in enumerate(li_docs[:2]):
    print(f"  Doc {i}: text='{li_doc['text'][:50]}...', extra_info={list(li_doc['extra_info'].keys())}")
print()

print("=" * 60)
print("Basic Usage Example Complete!")
print("=" * 60)
