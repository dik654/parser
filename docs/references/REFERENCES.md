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

### Excel (XLSX) Parsing

| Library | Best For | Notes |
|---------|----------|-------|
| **openpyxl** | Read/Write xlsx | Native Python, full feature support |
| **pandas** | Data analysis | High-level API, DataFrame output |
| **xlrd** | Legacy xls files | Read-only, older format support |

**Key Features:**
- `openpyxl.load_workbook()`: Load xlsx files
- `sheet.iter_rows()`: Iterate over rows efficiently
- `pandas.read_excel()`: Read to DataFrame with chunking support
- Multiple sheet handling

**References:**
- [openpyxl Documentation](https://openpyxl.readthedocs.io/)
- [pandas read_excel](https://pandas.pydata.org/docs/reference/api/pandas.read_excel.html)
- [Excel Spreadsheets in Python (Real Python)](https://realpython.com/openpyxl-excel-spreadsheets-python/)

### 한글 문서 (HWP/HWPX) Parsing

#### HWPX (XML 기반, 신형식)

HWPX는 ZIP 압축된 XML 기반 포맷입니다 (KS X 6101 표준).

**구조:**
```
document.hwpx
├── META-INF/
├── Contents/
│   ├── content.hpf        # 문서 구조 정보
│   ├── section0.xml       # 본문 내용 (여러 섹션 가능)
│   ├── section1.xml
│   └── ...
├── BinData/               # 임베디드 이미지/OLE 객체
└── Preview/
```

**파싱 방법:**
```python
import zipfile
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup

# ZIP 압축 해제 후 XML 파싱
with zipfile.ZipFile('document.hwpx', 'r') as zf:
    section = zf.read('Contents/section0.xml')
    soup = BeautifulSoup(section, 'xml')
    # hp:t 태그에서 텍스트 추출
    texts = [t.get_text() for t in soup.find_all('hp:t')]
```

**References:**
- [한컴테크 - HWPX 포맷 파싱하기](https://tech.hancom.com/python-hwpx-parsing-1/)
- [HWPX 표 읽기 (BeautifulSoup)](https://blog.harampark.com/blog/python-read-hwpx/)

#### HWP (바이너리, 구형식)

HWP는 OLE Compound File 구조를 사용합니다.

| Library | Notes |
|---------|-------|
| **olefile** | OLE 구조 파싱, MS Office 호환 |
| **pyhwp** | HWP 전용, 명령줄 변환 |
| **libhwp** | Rust 기반, Python 바인딩 제공 |
| **pyhwpx** | Windows 전용, 한/글 설치 필요 |

**References:**
- [한컴테크 - HWP 포맷 파싱하기](https://tech.hancom.com/python-hwp-parsing-1/)
- [pyhwpx PyPI](https://pypi.org/project/pyhwpx/)
- [libhwp GitHub](https://blog.hanlee.io/2022/hwp-rs/)

### 임베디드 이미지 OCR (Embedded Image Extraction)

문서 내 포함된 이미지를 추출하고 OCR을 수행합니다.

| Document | Extraction Method |
|----------|-------------------|
| **PDF** | PyMuPDF `page.get_images()` |
| **DOCX** | python-docx `document.part.rels` |
| **PPTX** | python-pptx `shape.image` |
| **XLSX** | openpyxl `worksheet._images` |
| **HWPX** | ZIP BinData 폴더에서 추출 |

**통합 라이브러리:**

| Library | Features |
|---------|----------|
| **Kreuzberg** | 통합 문서 인텔리전스, 임베디드 이미지 OCR 지원 |
| **textract** | 다양한 형식 지원, 통합 인터페이스 |

**References:**
- [Kreuzberg PyPI](https://pypi.org/project/kreuzberg/)
- [textract Documentation](https://textract.readthedocs.io/en/stable/)
- [PyMuPDF OCR Recipes](https://pymupdf.readthedocs.io/en/latest/recipes-ocr.html)
- [Extract Images from PDF (Medium)](https://karthikeyanrathinam.medium.com/extracting-text-and-images-from-pdfs-using-python-a-step-by-step-guide-b9c8506fd613)

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
pandas>=2.0.0

# 한글 문서 (HWP/HWPX)
olefile>=0.46          # HWP 파싱
# libhwp                # Rust 기반 (선택적)

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
