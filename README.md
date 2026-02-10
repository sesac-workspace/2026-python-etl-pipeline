# ETL 파이프라인

## 프로젝트 개요

## 프로젝트 설계

### 프로젝트 구조
```text
📁root/
├── 📄main.py
├── 📁app/
│   ├── 📄orchestrator.py
│   ├── 📁core/
│   │   ├── 📄config.py
│   │   └── 📄logger.py
│   └── 📁pipeline/
│       ├── 📄extractor.py
│       ├── 📄transformer.py
│       └── 📄loader.py
└── 🔧requirements.txt
```

## 실행 가이드

### 1. 가상 환경 생성 및 활성화
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/Mac
python -m venv .venv
source .venv/bin/activate
```

### 2. 필수 의존성 설치
```bash
pip install -r requirements.txt
```

### 3. 빠른 실행
```bash
python -m app.main --input_json "/input/your/json/metadata"
```