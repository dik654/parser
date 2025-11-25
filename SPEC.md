# AI Document Preprocessing Parser - Specification

## 1. Overview

### 1.1 Project Description
AI Document Preprocessing Parser는 다양한 형식의 문서(PDF, DOCX, HTML, 이미지 등)를 AI/LLM 학습 및 RAG(Retrieval-Augmented Generation) 시스템에 적합한 형태로 변환하는 Python 라이브러리입니다.

### 1.2 Goals
- 다양한 문서 형식 지원 (PDF, DOCX, PPTX, XLSX, HWPX/HWP, HTML, Markdown, 이미지)
- 고품질 텍스트 추출 및 구조 보존
- OCR 지원으로 스캔 문서 처리
- **임베디드 이미지 OCR 처리** (문서 내 포함된 이미지에서 텍스트 추출)
- RAG 시스템을 위한 최적화된 청킹(Chunking)
- 메타데이터 추출 및 관리
- 확장 가능한 파이프라인 아키텍처
- 한글 문서(HWP/HWPX) 네이티브 지원

### 1.3 Non-Goals
- 문서 생성/편집 기능
- 실시간 스트리밍 처리
- 웹 크롤링 (별도 도구 활용 권장)

---

## 2. Architecture

### 2.1 System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Document Parser                          │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │   Loader    │──│   Parser    │──│ Preprocessor│──┐          │
│  │   Layer     │  │   Layer     │  │    Layer    │  │          │
│  └─────────────┘  └─────────────┘  └─────────────┘  │          │
│                                                      ▼          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │   Output    │◀─│   Chunker   │◀─│   Text Cleaner/         │ │
│  │   Layer     │  │   Layer     │  │   Normalizer            │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Directory Structure

```
parser/
├── src/
│   ├── __init__.py
│   ├── parsers/                 # 문서 형식별 파서
│   │   ├── __init__.py
│   │   ├── base.py              # BaseParser 추상 클래스
│   │   ├── pdf_parser.py        # PDF 파서
│   │   ├── docx_parser.py       # DOCX 파서
│   │   ├── html_parser.py       # HTML 파서
│   │   ├── markdown_parser.py   # Markdown 파서
│   │   ├── image_parser.py      # 이미지 OCR 파서
│   │   ├── pptx_parser.py       # PowerPoint 파서
│   │   ├── xlsx_parser.py       # Excel 파서
│   │   └── hwp_parser.py        # 한글(HWP/HWPX) 파서
│   │
│   ├── preprocessors/           # 텍스트 전처리기
│   │   ├── __init__.py
│   │   ├── cleaner.py           # 텍스트 클리닝
│   │   ├── normalizer.py        # 정규화 (소문자, 유니코드 등)
│   │   ├── tokenizer.py         # 토크나이저 래퍼
│   │   └── chunker.py           # 청킹 전략
│   │
│   ├── utils/                   # 유틸리티
│   │   ├── __init__.py
│   │   ├── file_utils.py        # 파일 처리 유틸
│   │   ├── encoding.py          # 인코딩 감지/변환
│   │   └── metadata.py          # 메타데이터 추출
│   │
│   ├── pipeline.py              # 파이프라인 오케스트레이터
│   ├── document.py              # Document 데이터 클래스
│   └── config.py                # 설정 관리
│
├── tests/                       # 테스트
│   ├── __init__.py
│   ├── test_parsers/
│   ├── test_preprocessors/
│   └── fixtures/                # 테스트용 샘플 문서
│
├── docs/                        # 문서
│   └── references/
│       └── REFERENCES.md
│
├── examples/                    # 사용 예제
│   ├── basic_usage.py
│   ├── batch_processing.py
│   └── rag_integration.py
│
├── config/                      # 설정 파일
│   └── default_config.yaml
│
├── SPEC.md                      # 스펙 문서 (이 파일)
├── TODO.md                      # 작업 목록
├── README.md                    # 프로젝트 소개
├── pyproject.toml               # 프로젝트 설정
└── requirements.txt             # 의존성 목록
```

---

## 3. Core Components

### 3.1 Document Data Model

```python
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class DocumentType(Enum):
    PDF = "pdf"
    DOCX = "docx"
    PPTX = "pptx"
    XLSX = "xlsx"
    HWP = "hwp"
    HWPX = "hwpx"
    HTML = "html"
    MARKDOWN = "markdown"
    IMAGE = "image"
    TEXT = "text"
    UNKNOWN = "unknown"

@dataclass
class DocumentMetadata:
    """문서 메타데이터"""
    title: Optional[str] = None
    author: Optional[str] = None
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
    page_count: Optional[int] = None
    word_count: Optional[int] = None
    language: Optional[str] = None
    source_path: Optional[str] = None
    file_size: Optional[int] = None
    custom: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TextChunk:
    """텍스트 청크"""
    content: str
    index: int
    start_char: int
    end_char: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    # 선택적 필드
    page_number: Optional[int] = None
    section: Optional[str] = None
    embedding: Optional[List[float]] = None

@dataclass
class Document:
    """파싱된 문서"""
    id: str
    content: str
    doc_type: DocumentType
    metadata: DocumentMetadata
    chunks: List[TextChunk] = field(default_factory=list)
    raw_content: Optional[bytes] = None
    tables: List[Dict[str, Any]] = field(default_factory=list)
    images: List[Dict[str, Any]] = field(default_factory=list)
```

### 3.2 Parser Interface

```python
from abc import ABC, abstractmethod
from typing import Union, BinaryIO
from pathlib import Path

class BaseParser(ABC):
    """모든 파서의 기본 추상 클래스"""

    @abstractmethod
    def parse(
        self,
        source: Union[str, Path, BinaryIO, bytes],
        **kwargs
    ) -> Document:
        """
        문서를 파싱하여 Document 객체 반환

        Args:
            source: 파일 경로, 파일 객체, 또는 바이트 데이터
            **kwargs: 파서별 추가 옵션

        Returns:
            Document: 파싱된 문서 객체
        """
        pass

    @abstractmethod
    def supports(self, source: Union[str, Path]) -> bool:
        """해당 파서가 주어진 파일을 지원하는지 확인"""
        pass

    @property
    @abstractmethod
    def supported_extensions(self) -> List[str]:
        """지원하는 파일 확장자 목록"""
        pass
```

### 3.3 Preprocessor Interface

```python
from abc import ABC, abstractmethod

class BasePreprocessor(ABC):
    """모든 전처리기의 기본 추상 클래스"""

    @abstractmethod
    def process(self, text: str, **kwargs) -> str:
        """
        텍스트 전처리 수행

        Args:
            text: 입력 텍스트
            **kwargs: 전처리기별 추가 옵션

        Returns:
            str: 전처리된 텍스트
        """
        pass
```

### 3.4 Chunking Strategies

```python
from enum import Enum
from typing import List

class ChunkingStrategy(Enum):
    FIXED_SIZE = "fixed_size"
    RECURSIVE = "recursive"
    SEMANTIC = "semantic"
    SENTENCE = "sentence"
    PARAGRAPH = "paragraph"

@dataclass
class ChunkerConfig:
    """청커 설정"""
    strategy: ChunkingStrategy = ChunkingStrategy.RECURSIVE
    chunk_size: int = 512           # 토큰 수
    chunk_overlap: int = 50         # 오버랩 토큰 수
    separators: List[str] = field(
        default_factory=lambda: ["\n\n", "\n", ". ", " ", ""]
    )
    # Semantic chunking용
    embedding_model: Optional[str] = None
    similarity_threshold: float = 0.5
```

---

## 4. Supported Formats

### 4.1 PDF
- **라이브러리**: PyMuPDF (기본), pdfplumber (테이블용)
- **기능**:
  - 네이티브 텍스트 추출
  - OCR 지원 (스캔 문서)
  - 테이블 추출
  - 이미지 추출
  - 메타데이터 추출
  - 페이지별 처리

### 4.2 DOCX
- **라이브러리**: python-docx
- **기능**:
  - 텍스트 및 서식 추출
  - 테이블 추출
  - 이미지 추출
  - 스타일 정보 보존
  - 헤더/푸터 처리

### 4.3 HTML
- **라이브러리**: BeautifulSoup4, lxml
- **기능**:
  - 태그 제거 및 텍스트 추출
  - 구조 보존 옵션
  - 링크/이미지 메타데이터
  - 인코딩 자동 감지

### 4.4 Markdown
- **라이브러리**: markdown-it-py
- **기능**:
  - 마크다운 → 플레인 텍스트
  - 구조 보존 (헤딩, 리스트 등)
  - 코드 블록 처리

### 4.5 Images
- **라이브러리**: pytesseract, EasyOCR
- **기능**:
  - OCR 텍스트 추출
  - 다국어 지원
  - 이미지 전처리 (노이즈 제거, 이진화)

### 4.6 PowerPoint (PPTX)
- **라이브러리**: python-pptx
- **기능**:
  - 슬라이드별 텍스트 추출
  - 노트 추출
  - 이미지/도형 텍스트
  - **임베디드 이미지 OCR** (선택적)

### 4.7 Excel (XLSX/XLS)
- **라이브러리**: openpyxl (기본), pandas (데이터 처리)
- **기능**:
  - 시트별 텍스트 추출
  - 셀 데이터 → 텍스트 변환
  - 테이블 구조 보존 옵션
  - 수식 결과값 추출
  - 병합 셀 처리
  - **임베디드 이미지 OCR** (선택적)
  - 다중 시트 처리

### 4.8 한글 문서 (HWP/HWPX)
- **라이브러리**:
  - HWPX: zipfile + xml.etree (표준 라이브러리), BeautifulSoup (파싱 보조)
  - HWP: olefile, pyhwp, libhwp (Rust 기반)
- **기능**:
  - 본문 텍스트 추출
  - 테이블 추출
  - 메타데이터 추출 (제목, 저자 등)
  - 섹션별 처리 (section0.xml, section1.xml 등)
  - **임베디드 이미지 OCR** (선택적)
- **참고**:
  - HWPX는 ZIP 기반 XML 포맷 (KS X 6101 표준)
  - HWP는 OLE Compound File 구조 (바이너리)

### 4.9 임베디드 이미지 처리 (Embedded Image OCR)

모든 문서 형식에서 포함된 이미지를 추출하고 OCR을 수행할 수 있습니다.

- **지원 문서**: PDF, DOCX, PPTX, XLSX, HWPX
- **라이브러리**:
  - 이미지 추출: PyMuPDF (PDF), python-docx (DOCX), python-pptx (PPTX)
  - OCR: pytesseract, EasyOCR
- **기능**:
  - 문서 내 이미지 자동 감지 및 추출
  - 추출된 이미지에 OCR 적용
  - OCR 결과를 본문 텍스트에 병합
  - 이미지 위치 정보 보존 (선택적)
  - 이미지별 메타데이터 (크기, 형식, 페이지 번호)

```python
# 임베디드 이미지 OCR 사용 예시
from parser import parse

doc = parse("document.pdf", extract_embedded_images=True, ocr_images=True)

# 추출된 이미지 정보
for img in doc.images:
    print(f"Image: {img['filename']}, Page: {img['page']}")
    print(f"OCR Text: {img['ocr_text']}")
```

---

## 5. Text Preprocessing Pipeline

### 5.1 Cleaning Steps

1. **HTML 태그 제거**
   ```python
   # <p>Hello</p> → Hello
   ```

2. **특수 문자 처리**
   ```python
   # 불필요한 특수문자 제거 또는 정규화
   ```

3. **공백 정규화**
   ```python
   # 연속 공백, 탭 → 단일 공백
   ```

4. **URL/이메일 처리**
   ```python
   # 제거 또는 [URL], [EMAIL]로 대체
   ```

5. **이모지/비ASCII 처리**
   ```python
   # 제거 또는 유지 (설정 가능)
   ```

### 5.2 Normalization Steps

1. **유니코드 정규화** (NFC/NFKC)
2. **대소문자 변환** (선택적)
3. **숫자 정규화** (선택적)
4. **약어 확장** (선택적)

### 5.3 Advanced Processing (Optional)

1. **불용어 제거**
2. **형태소 분석 (한국어)**
3. **어간 추출 (Stemming)**
4. **표제어 추출 (Lemmatization)**

---

## 6. Pipeline Configuration

### 6.1 YAML Configuration

```yaml
# config/default_config.yaml

parser:
  pdf:
    engine: "pymupdf"          # pymupdf | pdfplumber
    ocr_enabled: true
    ocr_engine: "tesseract"    # tesseract | easyocr
    ocr_languages: ["eng", "kor"]
    extract_tables: true
    extract_images: false

  docx:
    preserve_formatting: false
    extract_tables: true
    extract_images: true
    ocr_images: true              # 임베디드 이미지 OCR

  pptx:
    extract_notes: true
    extract_images: true
    ocr_images: true

  xlsx:
    include_all_sheets: true
    preserve_table_structure: true
    include_formulas: false       # 수식 대신 결과값 사용
    extract_images: true
    ocr_images: true

  hwp:
    engine: "auto"                # auto | olefile | libhwp
    extract_tables: true
    extract_images: true
    ocr_images: true

  hwpx:
    extract_tables: true
    extract_images: true
    ocr_images: true
    parse_sections: true          # 여러 섹션 파일 처리

  html:
    remove_scripts: true
    remove_styles: true
    preserve_links: false

preprocessing:
  cleaning:
    remove_html_tags: true
    remove_urls: true
    remove_emails: true
    remove_special_chars: false
    normalize_whitespace: true

  normalization:
    unicode_normalize: "NFKC"
    lowercase: false

  advanced:
    remove_stopwords: false
    stopword_language: "english"
    stemming: false
    lemmatization: false

chunking:
  strategy: "recursive"
  chunk_size: 512
  chunk_overlap: 50
  separators:
    - "\n\n"
    - "\n"
    - ". "
    - " "

output:
  format: "json"              # json | jsonl | pickle
  include_metadata: true
  include_raw_content: false
```

### 6.2 Programmatic Configuration

```python
from parser import ParserConfig, Pipeline

config = ParserConfig(
    pdf_engine="pymupdf",
    ocr_enabled=True,
    chunk_strategy="recursive",
    chunk_size=512,
    chunk_overlap=50,
)

pipeline = Pipeline(config)
documents = pipeline.process("./documents/")
```

---

## 7. API Design

### 7.1 High-Level API

```python
from parser import parse, parse_directory, Pipeline

# 단일 파일 파싱
doc = parse("document.pdf")

# 디렉토리 일괄 파싱
docs = parse_directory("./documents/", recursive=True)

# 파이프라인 사용
pipeline = Pipeline()
pipeline.add_parser(PDFParser())
pipeline.add_preprocessor(TextCleaner())
pipeline.add_chunker(RecursiveChunker(chunk_size=512))

result = pipeline.run("document.pdf")
```

### 7.2 Low-Level API

```python
from parser.parsers import PDFParser
from parser.preprocessors import TextCleaner, Normalizer
from parser.chunker import RecursiveChunker

# 파서 직접 사용
parser = PDFParser(ocr_enabled=True)
doc = parser.parse("document.pdf")

# 전처리 체인
cleaner = TextCleaner()
normalizer = Normalizer()

text = cleaner.process(doc.content)
text = normalizer.process(text)

# 청킹
chunker = RecursiveChunker(chunk_size=512, overlap=50)
chunks = chunker.chunk(text)
```

### 7.3 Async Support

```python
import asyncio
from parser import AsyncPipeline

async def main():
    pipeline = AsyncPipeline()

    # 비동기 배치 처리
    files = ["doc1.pdf", "doc2.pdf", "doc3.pdf"]
    docs = await pipeline.process_batch(files, concurrency=3)

asyncio.run(main())
```

---

## 8. Error Handling

### 8.1 Exception Hierarchy

```python
class ParserException(Exception):
    """기본 파서 예외"""
    pass

class UnsupportedFormatException(ParserException):
    """지원하지 않는 파일 형식"""
    pass

class ParseException(ParserException):
    """파싱 중 오류"""
    pass

class OCRException(ParserException):
    """OCR 처리 중 오류"""
    pass

class EncodingException(ParserException):
    """인코딩 감지/변환 오류"""
    pass

class ChunkingException(ParserException):
    """청킹 중 오류"""
    pass
```

### 8.2 Error Handling Strategy

```python
from parser import Pipeline, ParserConfig

config = ParserConfig(
    on_error="skip",           # skip | raise | log
    max_retries=3,
    fallback_parser=True,      # 실패 시 대체 파서 사용
)

pipeline = Pipeline(config)
results = pipeline.process_directory("./docs/")

# 실패한 파일 확인
for error in results.errors:
    print(f"Failed: {error.file_path} - {error.message}")
```

---

## 9. Performance Considerations

### 9.1 Optimization Strategies

1. **병렬 처리**: `multiprocessing` 또는 `asyncio` 활용
2. **메모리 관리**: 대용량 파일 스트리밍 처리
3. **캐싱**: 파싱 결과 캐싱 (선택적)
4. **지연 로딩**: 필요한 시점에만 OCR 수행

### 9.2 Benchmarks Target

| 작업 | 목표 처리 시간 |
|------|---------------|
| PDF 텍스트 추출 (10페이지) | < 1초 |
| PDF OCR (10페이지) | < 30초 |
| DOCX 파싱 | < 0.5초 |
| PPTX 파싱 (20슬라이드) | < 1초 |
| XLSX 파싱 (1,000행) | < 0.5초 |
| HWPX 파싱 | < 0.5초 |
| HWP 파싱 | < 1초 |
| 임베디드 이미지 OCR (이미지당) | < 3초 |
| 청킹 (10,000 토큰) | < 0.1초 |

---

## 10. Integration Examples

### 10.1 LangChain Integration

```python
from parser import parse
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings

doc = parse("document.pdf")

# LangChain Document로 변환
lc_docs = [
    LangChainDocument(
        page_content=chunk.content,
        metadata=chunk.metadata
    )
    for chunk in doc.chunks
]

# 벡터 스토어에 저장
vectorstore = Chroma.from_documents(lc_docs, OpenAIEmbeddings())
```

### 10.2 RAG Pipeline

```python
from parser import Pipeline
from openai import OpenAI

# 문서 파싱
pipeline = Pipeline()
doc = pipeline.process("knowledge_base.pdf")

# 검색용 인덱스 구축
chunks = doc.chunks
embeddings = get_embeddings([c.content for c in chunks])

# RAG 쿼리
query = "What is the main topic?"
relevant_chunks = retrieve(query, embeddings, chunks, top_k=3)
context = "\n".join([c.content for c in relevant_chunks])

response = OpenAI().chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": f"Context:\n{context}"},
        {"role": "user", "content": query}
    ]
)
```

---

## 11. Testing Strategy

### 11.1 Test Categories

1. **Unit Tests**: 개별 컴포넌트 테스트
2. **Integration Tests**: 파이프라인 통합 테스트
3. **Performance Tests**: 벤치마크 및 부하 테스트
4. **Edge Case Tests**: 특수 케이스 (빈 파일, 손상된 파일 등)

### 11.2 Test Fixtures

- 다양한 형식의 샘플 문서
- 여러 언어 문서 (영어, 한국어, 일본어 등)
- 스캔된 PDF (OCR 테스트용)
- 복잡한 레이아웃 문서 (테이블, 다단 등)

---

## 12. Future Enhancements

### Phase 2
- [ ] 다국어 지원 강화 (중국어, 일본어 등)
- [ ] 테이블 구조 보존 강화
- [ ] 수식 추출 지원 (LaTeX)

### Phase 3
- [ ] LLM 기반 청킹 (GPT-4 등 활용)
- [ ] 문서 구조 분석 (헤딩, 섹션 자동 인식)
- [ ] 임베딩 통합 (문서 청크 임베딩)

### Phase 4
- [ ] 웹 UI 대시보드
- [ ] REST API 서버 모드
- [ ] 분산 처리 지원 (Ray, Dask)
