# AI Document Preprocessing Parser

다양한 문서 형식을 파싱하고 AI/LLM 애플리케이션을 위해 전처리하는 Python 라이브러리입니다.

## Features

- **다중 문서 형식 지원**: PDF, DOCX, PPTX, XLSX, HWP, HWPX, HTML, Markdown, 이미지
- **OCR 통합**: pytesseract, EasyOCR을 통한 스캔 문서 및 임베디드 이미지 처리
- **유연한 텍스트 청킹**: 고정 크기, 문장 기반, 재귀적, 시맨틱 청킹 지원
- **텍스트 전처리**: 정규화, 클리닝, 불용어 제거 등
- **RAG 파이프라인 최적화**: LangChain, LlamaIndex 호환 출력
- **설정 기반 파이프라인**: YAML/JSON 설정 파일 지원
- **평가 시스템**: 설정별 결과 비교 및 벤치마킹

## Installation

```bash
# 기본 설치
pip install ai-document-parser

# 개발 환경
pip install -e ".[dev]"

# OCR 확장
pip install ai-document-parser[ocr]

# 전체 설치
pip install ai-document-parser[ocr,nlp,docs]
```

### System Dependencies

```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr tesseract-ocr-kor libmagic1

# macOS
brew install tesseract tesseract-lang libmagic
```

## Quick Start

```python
from src.parsers import PDFParser
from src.preprocessors import TextCleaner
from src.chunkers import RecursiveChunker

# 문서 파싱
parser = PDFParser()
document = parser.parse("document.pdf")

# 텍스트 전처리
cleaner = TextCleaner()
cleaned_text = cleaner.process(document.content)

# 청킹
chunker = RecursiveChunker(chunk_size=1000, chunk_overlap=200)
chunks = chunker.chunk(cleaned_text)

for chunk in chunks:
    print(f"Chunk {chunk.index}: {chunk.content[:100]}...")
```

## Supported Formats

| Format | Extension | Parser | Notes |
|--------|-----------|--------|-------|
| PDF | .pdf | PDFParser | PyMuPDF + pdfplumber |
| Word | .docx | DOCXParser | python-docx |
| PowerPoint | .pptx | PPTXParser | python-pptx |
| Excel | .xlsx | XLSXParser | openpyxl + pandas |
| 한글 (XML) | .hwpx | HWPXParser | zipfile + xml |
| 한글 (Binary) | .hwp | HWPParser | olefile |
| HTML | .html | HTMLParser | BeautifulSoup |
| Markdown | .md | MarkdownParser | markdown-it-py |
| Image | .png, .jpg | ImageParser | pytesseract/EasyOCR |

## Configuration

YAML 설정 파일을 통한 파이프라인 구성:

```yaml
# config.yaml
parser:
  pdf:
    extract_tables: true
    ocr_enabled: true
    ocr_language: "eng+kor"

preprocessor:
  normalize_unicode: true
  remove_extra_whitespace: true
  lowercase: false

chunker:
  strategy: "recursive"
  chunk_size: 1000
  chunk_overlap: 200
```

```python
from src.pipeline import Pipeline

pipeline = Pipeline.from_config("config.yaml")
documents = pipeline.process_directory("./documents/")
```

## Evaluation & Benchmarking

설정 간 결과 비교:

```python
from src.evaluation import ConfigComparator, BenchmarkRunner

# 설정 비교
comparator = ConfigComparator(ground_truth=expected_text)
comparator.add_result(result_a)
comparator.add_result(result_b)
report = comparator.generate_report()

# 벤치마크 실행
runner = BenchmarkRunner()
suite = runner.run_benchmark(
    documents=test_docs,
    configs=test_configs,
    parse_fn=parse_document,
    chunk_fn=chunk_text,
    embed_fn=embed_chunks
)
print(suite.summary)
```

## Project Structure

```
parser/
├── src/
│   ├── document.py          # Core data models
│   ├── parsers/             # Document parsers
│   ├── preprocessors/       # Text preprocessors
│   ├── chunkers/            # Chunking strategies
│   ├── evaluation/          # Benchmarking tools
│   └── utils/               # Utilities
├── tests/                   # Test suite
├── config/                  # Configuration templates
├── examples/                # Usage examples
└── docs/                    # Documentation
```

## Development

```bash
# 저장소 클론
git clone https://github.com/dik654/parser.git
cd parser

# 가상환경 설정
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 개발 의존성 설치
pip install -r requirements-dev.txt
pip install -e .

# Pre-commit hooks 설정
pre-commit install

# 테스트 실행
pytest tests/ -v --cov=src

# 코드 포맷팅
black src tests
isort src tests
```

## Documentation

- [SPEC.md](SPEC.md) - 상세 기술 명세
- [TODO.md](TODO.md) - 개발 로드맵
- [REFERENCES.md](docs/references/REFERENCES.md) - 참고 자료

## License

MIT License - see [LICENSE](LICENSE) for details.
