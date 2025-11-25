# AI Document Preprocessing Parser - References

## 1. Document Parsing Libraries

### PDF Parsing

| Library | Best For | Speed | Notes |
|---------|----------|-------|-------|
| **PyPDF2/pypdf** | Basic text extraction | Fast (0.024s) | Lightweight, occasional spacing artifacts |
| **PyMuPDF (fitz)** | Layout-sensitive tasks | Very Fast | Good for preserving document structure |
| **pypdfium2** | Pure speed | Fastest (0.003s) | Clean basic text, no structure |
| **pdfplumber** | Tables & structure | Medium (0.10s) | Excellent for complex layouts |
| **PDFMiner** | Complex layouts | Slower | Robust metadata extraction |

**References:**
- [Evaluating Python PDF to Text Libraries](https://unstract.com/blog/evaluating-python-pdf-to-text-libraries/)
- [7 Python PDF Extractors Tested (2025)](https://onlyoneaman.medium.com/i-tested-7-python-pdf-extractors-so-you-dont-have-to-2025-edition-c88013922257)
- [PDF Extraction Libraries Guide](https://www.metriccoders.com/post/a-guide-to-pdf-extraction-libraries-in-python)

### OCR Libraries

| Library | Features | Notes |
|---------|----------|-------|
| **Tesseract/pytesseract** | Open-source, 100+ languages | Google's OCR engine |
| **EasyOCR** | 80+ languages, Deep Learning | Better for mixed content |
| **OCRmyPDF** | PDF-specific, batch processing | Adds searchable text layer |
| **AWS Textract** | Cloud-based, scalable | Managed service |

**References:**
- [Python OCR Libraries for PDF](https://ploomber.io/blog/pdf-ocr/)
- [OCRmyPDF PyPI](https://pypi.org/project/ocrmypdf/)
- [Top 7 Python OCR Libraries](https://www.tecmint.com/python-text-extraction-from-images/)

### Document Loaders (LangChain/Unstructured)

**Unstructured.io** - Powerful library for extracting structured data from unstructured documents.

Supported formats:
- PDF, DOCX, PPTX, XLSX
- HTML, Markdown
- Images (with OCR)
- Email (EML, MSG)

**References:**
- [LangChain Unstructured Integration](https://python.langchain.com/docs/integrations/document_loaders/unstructured_file/)
- [Document Loaders and Parsers Guide](https://muegenai.com/docs/data-science/llmops/module-4-data-pipelines-for-llms/document-loaders-and-parsers-langchain-unstructured-io/)

---

## 2. Text Preprocessing & NLP

### Core Libraries

| Library | Purpose | Notes |
|---------|---------|-------|
| **NLTK** | Full NLP toolkit | 50+ corpora, comprehensive |
| **spaCy** | Industrial NLP | Fast, accurate, production-ready |
| **Gensim** | Semantic similarity | Topic modeling, word vectors |
| **Textacy** | Text preprocessing | Built on spaCy |
| **Hugging Face Tokenizers** | Transformer tokenization | BERT, GPT compatible |

### Preprocessing Steps

1. **Cleaning**: Remove special characters, HTML tags, URLs
2. **Tokenization**: Break text into words/sentences
3. **Normalization**: Lowercase, stemming, lemmatization
4. **Stop Word Removal**: Remove common words
5. **Rare/Frequent Word Removal**: Statistical filtering

**References:**
- [Text Preprocessing in NLP with Python](https://www.analyticsvidhya.com/blog/2021/06/text-preprocessing-in-nlp-with-python-codes/)
- [Text Data Cleaning with Textacy](https://www.datacamp.com/tutorial/textacy-text-data-cleaning-normalization-python)
- [NLTK Preprocessing Guide](https://codefinity.com/blog/A-Comprehensive-Guide-to-Text-Preprocessing-with-NLTK)

---

## 3. Chunking Strategies for RAG

### Strategy Comparison

| Strategy | Recall | Complexity | Best For |
|----------|--------|------------|----------|
| **Fixed-Size** | ~85% | Low | Simple use cases |
| **RecursiveCharacterTextSplitter** | 88-89% | Low | General purpose |
| **Semantic Chunking** | ~91% | High | High-quality RAG |
| **LLM-Based Chunking** | ~92% | Very High | Complex documents |

### Recommended Settings

- **RecursiveCharacterTextSplitter**: 400-512 tokens, 10-20% overlap
- **Semantic Chunking**: Use when 3% recall improvement justifies 10x cost
- **Code/Technical Docs**: Language-specific recursive chunking

### Key Trade-offs

- Smaller chunks → Better query precision, less context
- Larger chunks → Better context preservation, diluted relevance

**References:**
- [Chunking Strategies for RAG (Pinecone)](https://www.pinecone.io/learn/chunking-strategies/)
- [Best Chunking Strategies 2025](https://www.firecrawl.dev/blog/best-chunking-strategies-rag-2025)
- [Five Levels of Chunking Strategies](https://medium.com/@anuragmishra_27746/five-levels-of-chunking-strategies-in-rag-notes-from-gregs-video-7b735895694d)
- [Ultimate Guide to RAG Chunking](https://agenta.ai/blog/the-ultimate-guide-for-chunking-strategies)
- [Mastering RAG: Advanced Chunking](https://galileo.ai/blog/mastering-rag-advanced-chunking-techniques-for-llm-applications)

---

## 4. AI-Powered Document Processing

### Commercial Solutions

| Tool | Features | Pricing |
|------|----------|---------|
| **LlamaParse** | Markdown output, LLM-optimized | API-based |
| **Landing AI (Agentic)** | No-code, playground | $0.03/page |
| **Google Document AI** | Layout parser, RAG-ready | Cloud pricing |
| **Firecrawl** | Web scraping, LLM-friendly | SaaS |

### Open Source Alternatives

- **ExtractThinker**: ORM-style document intelligence
- **Docling**: IBM's document conversion library
- **Marker**: PDF to Markdown converter

**References:**
- [5 Best Document Parsers 2025](https://www.f22labs.com/blogs/5-best-document-parsers-in-2025-tested/)
- [Document AI with Python (Google)](https://codelabs.developers.google.com/codelabs/docai-form-parser-v1-python)
- [BigQuery + Document AI for RAG](https://cloud.google.com/blog/products/data-analytics/bigquery-and-document-ai-layout-parser-for-document-preprocessing/)

---

## 5. Recommended Tech Stack

### Core Dependencies

```txt
# PDF Processing
pypdf>=3.0.0
pymupdf>=1.23.0
pdfplumber>=0.10.0

# OCR
pytesseract>=0.3.10
easyocr>=1.7.0

# Document Loading
unstructured>=0.10.0
python-docx>=1.0.0
python-pptx>=0.6.21
openpyxl>=3.1.0

# NLP & Text Processing
spacy>=3.7.0
nltk>=3.8.0
tiktoken>=0.5.0

# Chunking & RAG
langchain>=0.1.0
langchain-text-splitters>=0.0.1

# Utilities
beautifulsoup4>=4.12.0
lxml>=4.9.0
chardet>=5.2.0
```

### Optional Dependencies

```txt
# Advanced OCR
ocrmypdf>=16.0.0
paddleocr>=2.7.0

# Cloud Services
boto3>=1.34.0  # AWS Textract
google-cloud-documentai>=2.20.0

# LLM Integration
openai>=1.0.0
anthropic>=0.18.0
llama-index>=0.10.0
```
