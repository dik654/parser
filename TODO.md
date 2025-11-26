# AI Document Preprocessing Parser - TODO

## Overview

이 문서는 AI Document Preprocessing Parser 프로젝트의 개발 작업 목록입니다.
각 작업은 우선순위별로 분류되어 있습니다.

**범례:**
- ⬜ 미시작
- 🔄 진행중
- ✅ 완료
- ⏸️ 보류

---

## Phase 1: Foundation (Core Infrastructure) ✅

### 1.1 프로젝트 설정 ✅
- [x] `pyproject.toml` 설정 및 패키지 구조 정의
- [x] `requirements.txt` 및 `requirements-dev.txt` 작성
- [x] Pre-commit hooks 설정 (black, isort, flake8, mypy)
- [x] pytest 설정 및 기본 테스트 구조
- [x] GitHub Actions CI/CD 파이프라인 설정
- [x] README.md 작성

### 1.2 Core Data Models ✅
- [x] `Document` 데이터 클래스 구현
- [x] `DocumentMetadata` 구현
- [x] `TextChunk` 구현
- [x] `DocumentType` Enum 구현
- [x] 직렬화/역직렬화 (JSON, Pickle) 지원

### 1.3 Base Interfaces ✅
- [x] `BaseParser` 추상 클래스 구현
- [x] `BasePreprocessor` 추상 클래스 구현
- [x] `BaseChunker` 추상 클래스 구현
- [x] `ParserRegistry` 구현 (파서 자동 등록/검색)

---

## Phase 2: Document Parsers ✅

### 2.1 PDF Parser ✅
- [x] PyMuPDF 기반 텍스트 추출 구현
- [x] pdfplumber 기반 테이블 추출 구현
- [x] 메타데이터 추출 (제목, 저자, 페이지 수 등)
- [x] 페이지별 파싱 지원
- [x] 암호화된 PDF 처리
- [x] OCR fallback 통합 (스캔 문서용)
- [x] Unit tests 작성

### 2.2 DOCX Parser ✅
- [x] python-docx 기반 텍스트 추출
- [x] 테이블 추출
- [x] 스타일/서식 메타데이터 추출
- [x] 이미지 추출 및 참조
- [x] 헤더/푸터 처리
- [x] Unit tests 작성

### 2.3 HTML Parser ✅
- [x] BeautifulSoup4 기반 파서 구현
- [x] 태그 제거 및 텍스트 추출
- [x] 구조 보존 모드 (헤딩, 리스트 등)
- [x] 인코딩 자동 감지 (chardet)
- [x] 메타 태그 파싱
- [x] Unit tests 작성

### 2.4 Markdown Parser ✅
- [x] markdown-it-py 또는 mistune 기반 구현
- [x] 헤딩/섹션 구조 보존
- [x] 코드 블록 처리 옵션
- [x] 링크/이미지 메타데이터 추출
- [x] Unit tests 작성

### 2.5 Image Parser (OCR) ✅
- [x] pytesseract 통합
- [x] EasyOCR 통합 (대체 엔진)
- [x] 이미지 전처리 (노이즈 제거, 이진화, 회전 보정)
- [x] 다국어 지원 (영어, 한국어 우선)
- [x] 신뢰도 점수 반환
- [x] Unit tests 작성

### 2.6 PPTX Parser ✅
- [x] python-pptx 기반 구현
- [x] 슬라이드별 텍스트 추출
- [x] 발표자 노트 추출
- [x] 도형 내 텍스트 추출
- [x] 임베디드 이미지 추출 및 OCR
- [x] Unit tests 작성

### 2.7 XLSX Parser ✅
- [x] openpyxl 기반 구현
- [x] pandas 통합 (데이터 처리용)
- [x] 다중 시트 처리
- [x] 셀 데이터 → 텍스트 변환
- [x] 테이블 구조 보존 옵션
- [x] 수식 결과값 추출
- [x] 병합 셀 처리
- [x] 임베디드 이미지 추출 및 OCR
- [x] Unit tests 작성

### 2.8 HWP Parser (한글 - 바이너리) ✅
- [x] olefile 기반 구현
- [x] libhwp (Rust) 통합 (대체 엔진)
- [x] 본문 텍스트 추출
- [x] 테이블 추출
- [x] 메타데이터 추출
- [x] 임베디드 이미지 추출 및 OCR
- [x] Unit tests 작성

### 2.9 HWPX Parser (한글 - XML) ✅
- [x] zipfile + xml.etree 기반 구현
- [x] BeautifulSoup 파싱 보조
- [x] section*.xml 파일 처리
- [x] Contents/content.hpf 분석
- [x] 본문 텍스트 추출 (hp:t 태그)
- [x] 테이블 추출 (hp:tbl 태그)
- [x] 메타데이터 추출
- [x] 임베디드 이미지 추출 및 OCR
- [x] Unit tests 작성

### 2.10 Embedded Image OCR (공통 모듈) ✅
- [x] 이미지 추출 인터페이스 정의
- [x] PDF 임베디드 이미지 추출 (PyMuPDF)
- [x] DOCX 임베디드 이미지 추출 (python-docx)
- [x] PPTX 임베디드 이미지 추출 (python-pptx)
- [x] XLSX 임베디드 이미지 추출 (openpyxl)
- [x] HWPX 임베디드 이미지 추출 (BinData 폴더)
- [x] OCR 엔진 통합 (pytesseract/EasyOCR)
- [x] 이미지 전처리 파이프라인
- [x] OCR 결과 텍스트 병합 옵션
- [x] Unit tests 작성

---

## Phase 3: Text Preprocessing ✅

### 3.1 Text Cleaner ✅
- [x] HTML 태그 제거
- [x] 특수 문자 처리 (설정 가능)
- [x] 공백 정규화 (연속 공백, 탭, 줄바꿈)
- [x] URL 제거/대체
- [x] 이메일 제거/대체
- [x] 전화번호 제거/대체 (선택적)
- [x] 이모지 처리 (제거/유지)
- [x] Unit tests 작성

### 3.2 Text Normalizer ✅
- [x] 유니코드 정규화 (NFC, NFKC, NFD, NFKD)
- [x] 대소문자 변환 (선택적)
- [x] 숫자 정규화 (선택적)
- [x] 약어 확장 (설정 파일 기반)
- [x] 문장 부호 정규화
- [x] Unit tests 작성

### 3.3 Advanced NLP Processing (Optional)
- [ ] NLTK 기반 불용어 제거
- [ ] spaCy 기반 불용어 제거
- [ ] 어간 추출 (Stemming) - Porter, Snowball
- [ ] 표제어 추출 (Lemmatization)
- [ ] 한국어 형태소 분석 (Mecab/Konlpy)
- [ ] Unit tests 작성

---

## Phase 4: Chunking Strategies ✅

### 4.1 Basic Chunkers ✅
- [x] Fixed-size chunker (문자/토큰 수 기준)
- [x] Sentence-based chunker
- [x] Paragraph-based chunker
- [x] Unit tests 작성

### 4.2 Recursive Character Text Splitter ✅
- [x] LangChain 호환 구현
- [x] 커스텀 구분자 지원
- [x] 오버랩 지원
- [x] 최소/최대 청크 크기 설정
- [x] Unit tests 작성

### 4.3 Semantic Chunker ✅
- [x] 문장 임베딩 기반 분할
- [x] 유사도 임계값 설정
- [x] 여러 임베딩 모델 지원
- [x] Unit tests 작성

### 4.4 Token Counter ✅
- [x] tiktoken 통합 (OpenAI 모델용)
- [x] HuggingFace tokenizers 통합
- [x] 커스텀 토크나이저 지원
- [x] Unit tests 작성

---

## Phase 5: Pipeline & Configuration ✅

### 5.1 Pipeline Orchestrator ✅
- [x] `Pipeline` 클래스 구현
- [x] 파서 체인 구성
- [x] 전처리 체인 구성
- [x] 청커 통합
- [x] 에러 핸들링 전략 (skip/raise/log)
- [x] 진행 상황 콜백
- [x] Unit tests 작성

### 5.2 Configuration System ✅
- [x] YAML 설정 파일 로더
- [x] JSON 설정 파일 로더
- [x] 환경 변수 지원
- [x] 설정 검증 (Pydantic)
- [x] 기본 설정 템플릿
- [x] Unit tests 작성

### 5.3 Batch Processing ✅
- [x] 디렉토리 일괄 처리
- [x] glob 패턴 지원
- [x] 병렬 처리 (multiprocessing)
- [x] 비동기 처리 (asyncio)
- [x] 진행률 표시 (tqdm)
- [x] 결과 저장 (JSON, JSONL)
- [x] Unit tests 작성

---

## Phase 6: Utilities & Helpers ✅

### 6.1 File Utilities ✅
- [x] 파일 타입 자동 감지 (magic/mimetypes)
- [x] 인코딩 감지 (chardet)
- [x] 임시 파일 관리
- [x] 압축 파일 처리 (zip, tar)
- [x] Unit tests 작성

### 6.2 Metadata Utilities ✅
- [x] 통합 메타데이터 추출기
- [x] 언어 감지 (langdetect)
- [x] 키워드 추출
- [x] 요약 생성 (선택적, LLM 기반)
- [x] Unit tests 작성

### 6.3 Output Formatters ✅
- [x] JSON 출력
- [x] JSONL 출력 (스트리밍용)
- [x] CSV 출력 (메타데이터)
- [x] LangChain Document 변환
- [x] LlamaIndex Document 변환
- [x] Unit tests 작성

---

## Phase 7: Evaluation & Benchmarking ✅

### 7.1 평가 메트릭 구현 ✅
- [x] TextExtractionMetrics 구현 (precision, recall, F1, BLEU)
- [x] ChunkingMetrics 구현 (크기 분포, 경계 분석)
- [x] EmbeddingMetrics 구현 (검색 품질, 유사도)
- [x] calculate_text_similarity 구현 (sequence, jaccard, cosine)
- [x] calculate_bleu_score 구현
- [x] calculate_word_error_rate 구현
- [x] Unit tests 작성

### 7.2 설정 비교기 구현 ✅
- [x] ParsingResult 데이터 클래스
- [x] ConfigComparator 클래스
- [x] ComparisonReport 생성
- [x] 설정별 순위 계산
- [x] 권장 설정 생성
- [x] JSON 리포트 저장
- [x] Unit tests 작성

### 7.3 임베딩 평가 모듈 ✅
- [x] EmbeddingEvaluator 클래스
- [x] 코사인 유사도 계산
- [x] 검색 결과 비교 (find_similar)
- [x] Recall@K, Precision@K 계산
- [x] MRR, NDCG 계산
- [x] 설정 간 임베딩 비교
- [x] Unit tests 작성

### 7.4 벤치마크 러너 ✅
- [x] BenchmarkConfig 데이터 클래스
- [x] BenchmarkResult 데이터 클래스
- [x] BenchmarkRunner 클래스
- [x] BenchmarkSuite 생성
- [x] 기본 설정 템플릿 (create_default_configs)
- [x] 진행 콜백 지원
- [x] Unit tests 작성

### 7.5 추가 개선 (Optional)
- [ ] 시각화 리포트 생성 (HTML/Matplotlib)
- [ ] 통계적 유의성 테스트
- [ ] 자동 최적 설정 탐색
- [ ] CI/CD 벤치마크 통합

---

## Phase 8: Documentation & Examples 🔄

### 8.1 Documentation
- [x] README.md 작성
- [ ] API 문서 (Sphinx/MkDocs)
- [ ] 설치 가이드
- [ ] 빠른 시작 가이드
- [ ] 설정 레퍼런스
- [ ] 트러블슈팅 가이드
- [ ] 기여 가이드 (CONTRIBUTING.md)

### 8.2 Examples
- [ ] 기본 사용법 예제
- [ ] 배치 처리 예제
- [ ] 커스텀 파서 작성 예제
- [ ] LangChain 통합 예제
- [ ] RAG 파이프라인 예제
- [ ] 설정 파일 예제
- [x] 벤치마크 예제 (benchmark_example.py)

---

## Phase 9: Testing & Quality ✅

### 9.1 Testing ✅
- [x] 단위 테스트 (coverage > 80%)
- [x] 통합 테스트
- [x] 성능 벤치마크 테스트
- [ ] 다양한 샘플 문서 수집 (fixtures)
- [ ] 엣지 케이스 테스트 (빈 파일, 손상된 파일 등)

### 9.2 Quality Assurance
- [x] Type hints 완전 적용
- [ ] mypy 통과
- [ ] 코드 스타일 일관성 (black, isort)
- [ ] 문서화 완성도 검토
- [ ] 보안 검토 (파일 경로 등)

---

## Phase 10: Advanced Features (Future)

### 10.1 Performance Optimization
- [ ] 캐싱 레이어 추가
- [ ] 스트리밍 처리 지원
- [ ] 메모리 최적화 (대용량 파일)
- [ ] 프로파일링 및 병목 해결

### 10.2 Advanced OCR
- [ ] PaddleOCR 통합
- [ ] 레이아웃 분석
- [ ] 표 인식 개선
- [ ] 수식 인식

### 10.3 LLM Integration
- [ ] LLM 기반 청킹
- [ ] 문서 구조 분석 (LLM)
- [ ] 자동 메타데이터 생성
- [ ] 의미 기반 섹션 분할

### 10.4 API Server (Optional)
- [ ] FastAPI 기반 REST API
- [ ] 비동기 작업 큐
- [ ] 인증/권한 관리
- [ ] 웹 UI 대시보드

---

## Milestones

### MVP (Minimum Viable Product) ✅
**목표:** 기본적인 PDF, DOCX, HTML 파싱 및 청킹

- [x] Phase 1 완료
- [x] PDF Parser (기본 기능)
- [x] DOCX Parser
- [x] HTML Parser
- [x] Text Cleaner (기본)
- [x] Recursive Chunker
- [x] 기본 파이프라인

### v1.0 Release ✅
**목표:** 모든 주요 기능 구현 및 안정화

- [x] Phase 1-6 완료
- [x] 모든 파서 구현 (PDF, DOCX, HTML, PPTX, XLSX, HWP, HWPX)
- [x] OCR 완전 지원
- [x] 임베디드 이미지 OCR 지원
- [x] 모든 청킹 전략
- [x] 문서화 완료
- [x] 테스트 커버리지 80%+

### v2.0 Release
**목표:** 고급 기능 및 성능 최적화

- [ ] Phase 7-9 완료
- [ ] LLM 통합
- [ ] API 서버
- [ ] 성능 최적화

---

## Notes

### Dependencies Priority
1. **필수:** pypdf, pymupdf, python-docx, python-pptx, openpyxl, beautifulsoup4, pytesseract
2. **권장:** pdfplumber, pandas, spacy, tiktoken, langchain-text-splitters, olefile
3. **선택:** easyocr, paddleocr, libhwp, openai, anthropic

### Known Challenges
1. OCR 정확도 (스캔 품질에 의존)
2. 복잡한 PDF 레이아웃 (다단, 표)
3. 다국어 문서 처리
4. 대용량 파일 메모리 관리
5. HWP 바이너리 포맷 파싱 (복잡한 OLE 구조)
6. HWPX 네임스페이스 버전 호환성
7. 임베디드 이미지 OCR 성능 최적화

### References
- [REFERENCES.md](docs/references/REFERENCES.md) 참조
- [SPEC.md](SPEC.md) 참조
