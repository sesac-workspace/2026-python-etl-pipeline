# ETL 파이프라인

## 프로젝트 개요
본 프로젝트는 추출(`Extract`), 변환(`Transform`), 적재(`Load`) 과정을 거쳐 RAG(`Retrieval-Augmented Generation`) 시스템을 구축하는 고성능 ETL 파이프라인입니다.

**SeSAC 프로젝트 [이음새: 복지 공고 간소화 서비스](https://github.com/E-will-era/easy-welfare-guide)에 사용**

## 프로젝트 설계

![ETL Pipeline Architecture](/docs/architecture/ETL_Pipeline_Architecture.png)

### 프로젝트 기능
1. **고품질 문서 변환**
    - `Docling` 라이브러리를 활용하여 PDF 문서 내 데이터를 고품질의 **Markdown 문서**로 변환합니다.

2. **구조적 청킹 전략**
    - 문서 구조를 분석하여 문맥 보존을 위한 **Parent Chunk**와 정밀 검색을 위한 **Child Chunk**로 계층적으로 분할합니다.

3. **멱등성 보장**
    - 각 Chunk의 내용을 기반으로 UUID(`MD5+uuid5`)를 생성하여 동일한 데이터에 대한 **중복 처리를 방지**합니다.

4. **Hybrid Search 지원**
    - `Semantic Search`: BAAI(베이징인공지능연구소)의 `bge-m3` 임베딩 모델을 사용하여 **1,024차원의 벡터로 변환** 후 ChromaDB에 적재합니다.
    - `Lexical Search`: 한국어 형태소 분석기 `Kiwi`와 키워드 기반 검색 알고리즘 `BM25`를 사용하여 **한국어 키워드 검색 인덱스**를 구축합니다.

5. **문맥 보존 저장소**
    - 검색된 청크의 원본 문맥을 제공하기 위해 별도의 **Document Store**를 JSON 파일로 구축합니다.

### 프로젝트 구조
```text
📁root/
├── 📄main.py                 # CLI 인자를 파싱하고 파이프라인을 가동하는 엔트리 포인트
│
├── 📁app/
│   ├── 📄orchestrator.py     # ETL 파이프라인의 전체 흐름을 제어하고 관리하는 클래스
│   │
│   ├── 📁core/
│   │   ├── 📄config.py       # 파일 경로, 로그 설정 등 프로젝트 상수를 관리하는 설정 클래스
│   │   └── 📄logger.py       # 콘솔 출력, 파일 저장을 위한 로깅 인스턴스를 생성하는 클래스
│   │
│   └── 📁pipeline/
│       ├── 📄extractor.py    # Markdown 문서로 변환하고 메타 데이터와 병합하는 클래스
│       ├── 📄transformer.py  # Parent-Child 전략으로 문서를 청킹하고 구조화하는 클래스
│       └── 📄loader.py       # 데이터를 VectorDB, Index, Document Store에 적재하는 클래스
│
└── 🔧requirements.txt        # 프로젝트 실행에 필요한 라이브러리와 버전을 명시한 텍스트 파일
```

## 실행 가이드

### 사전 안내

#### 요구사항
- Python은 3.10 이상 3.12 이하 권장 (Docling 및 LangChain 호환성)
- MacOS, Linux 호환하나 Windows10 이상 권장
- OCR 및 Embedding 처리를 위해 CUDA 12.4 이상의 NVIDIA GPU 필수

#### 개발 환경
| Component | Specification | Detail |
| :--- | :--- | :--- |
| **CPU** | **AMD Ryzen 7 5700X3D** | 8-Core 16-Thread, 3.0GHz (Max 4.1GHz) |
| **M/B** | **MSI X470 Gaming Pro** | AM4 Socket, PCIe 3.0 Support |
| **GPU** | **NVIDIA RTX 2000 Blackwell** | **16GB VRAM**, PCIe 5.0 x8 |
| **RAM** | **G.Skill Trident Z Neo** | DDR4-3200MHz CL16 **64GB** (32GB x 2) |
| **Storage** | **Samsung 970 EVO Plus** | 2TB NVMe M.2 SSD (PCIe 3.0 x4) |

### 1. 가상 환경 생성 및 활성화
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/Mac
python -m venv .venv
source .venv/bin/activate
```
- **Python**: 3.10 이상 3.12 이하 권장 (Docling 및 LangChain 호환성)

### 2. 필수 의존성 설치
```bash
pip install -r requirements.txt
```
- 주요 의존성
    - `langchain`: 데이터 로드, 텍스트 분할, 벡터 저장소 연동 등 파이프라인을 구성하는 핵심 프레임워크
    - `docling`: IBM에서 개발한 고성능 문서 변환 도구로 PDF 문서를 고품질의 Markdown 문서로 추출
    - `transformers`: Docling의 레이아웃 분석 모델과 임베딩 모델 구동을 위한 필수 백엔드 라이브러리
    - `chromadb`: 임베딩된 벡터 데이터를 저장하고 조회하는 고성능 벡터 데이터베이스
    - `kiwipiepy`: 정확도가 뛰어난 한국어 형태소 분석기로 일반 명사, 고유 명사 등을 추출하여 토큰화
    - `rank_bm25`: 추출된 형태소를 바탕으로 문서의 연관성을 평가하는 키워드 검색 알고리즘

### 3. 빠른 실행

#### 3.1. 데이터 준비
- Markdown 문서로 변환할 PDF 문서를 `/data/rawdata` 경로로 이동합니다.
- 메타 데이터는 JSON 형식으로 사용자가 지정한 경로에 있어야 합니다.

#### 3.2. 명령어 실행
```bash
python -m main --input_json "/input/your/json/metadata"
```
- 실행이 완료되면 `/data/pipeline/export` 경로에 VectorDB, Index, Document Store가 생성됩니다.

## 작성자
- **Name**: Kim Hyunsik
- **GitHub**: [main328](https://github.com/main328)
- **Contact**: [E-mail](kimhyunsik810@gmail.com)