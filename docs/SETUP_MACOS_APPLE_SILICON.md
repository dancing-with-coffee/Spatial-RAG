# Spatial-RAG 설치 가이드 (macOS Apple Silicon)

MacBook M4 Max (Apple Silicon) 환경에서 Spatial-RAG 맛집 서비스를 설정하는 가이드입니다.

---

## 목차

1. [사전 준비](#1-사전-준비)
2. [Homebrew 패키지 설치](#2-homebrew-패키지-설치)
3. [PostgreSQL + PostGIS + pgvector 설정](#3-postgresql--postgis--pgvector-설정)
4. [Conda 환경 설정](#4-conda-환경-설정)
5. [환경 변수 설정](#5-환경-변수-설정)
6. [데이터베이스 초기화](#6-데이터베이스-초기화)
7. [서버 실행](#7-서버-실행)
8. [Apple Silicon 고려사항](#8-apple-silicon-고려사항)

---

## 1. 사전 준비

### 1.1 Homebrew 설치 (없는 경우)

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### 1.2 Xcode Command Line Tools

```bash
xcode-select --install
```

### 1.3 HuggingFace 준비

1. https://huggingface.co/settings/tokens 에서 토큰 발급 (Read 권한)
2. https://huggingface.co/google/embeddinggemma-300m 방문하여 라이선스 동의

---

## 2. Homebrew 패키지 설치

```bash
# PostgreSQL 15
brew install postgresql@15

# PostGIS
brew install postgis

# pgvector
brew install pgvector

# 기타 필요한 도구
brew install wget git
```

---

## 3. PostgreSQL + PostGIS + pgvector 설정

### 3.1 PostgreSQL 서비스 시작

```bash
# PostgreSQL 서비스 시작
brew services start postgresql@15

# 상태 확인
brew services list
```

### 3.2 PostgreSQL PATH 설정

```bash
# ~/.zshrc에 추가
echo 'export PATH="/opt/homebrew/opt/postgresql@15/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### 3.3 데이터베이스 및 사용자 생성

```bash
# PostgreSQL 접속
psql postgres

# 데이터베이스 생성
CREATE DATABASE spatial_rag;

# 사용자 생성 (비밀번호: postgres)
CREATE USER postgres WITH PASSWORD 'postgres';

# 권한 부여
GRANT ALL PRIVILEGES ON DATABASE spatial_rag TO postgres;
ALTER DATABASE spatial_rag OWNER TO postgres;

# 접속 종료
\q
```

### 3.4 확장 설치

```bash
# spatial_rag 데이터베이스에 접속
psql -d spatial_rag

# 확장 설치
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS vector;

# 확장 확인
\dx

# 접속 종료
\q
```

### 3.5 스키마 적용

```bash
# 프로젝트 디렉토리에서
psql -d spatial_rag -f schema.sql
```

---

## 4. Conda 환경 설정

### 4.1 Miniforge 설치 (Apple Silicon 최적화)

```bash
# Miniforge 설치 (Apple Silicon 네이티브)
brew install miniforge

# conda 초기화
conda init zsh
source ~/.zshrc
```

> **참고**: Anaconda 대신 Miniforge를 권장합니다. Apple Silicon에 최적화되어 있습니다.

### 4.2 Conda 환경 생성

```bash
# Python 3.11 환경 생성
conda create -n spatial-rag python=3.11 -y

# 환경 활성화
conda activate spatial-rag
```

### 4.3 Python 패키지 설치

```bash
# 프로젝트 디렉토리로 이동
cd /path/to/Spatial-RAG

# 패키지 설치
pip install -r api/requirements.txt
```

### 4.4 PyTorch MPS 지원 확인

```python
# Python에서 확인
import torch
print(f"MPS available: {torch.backends.mps.is_available()}")
print(f"MPS built: {torch.backends.mps.is_built()}")
```

---

## 5. 환경 변수 설정

### 5.1 .env 파일 생성

프로젝트 루트에 `.env` 파일 생성:

```bash
# ===========================================
# Spatial-RAG 맛집 서비스 환경 변수
# ===========================================

# ----- HuggingFace (필수) -----
HUGGINGFACE_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# ----- Embedding 설정 -----
EMBEDDING_MODEL=google/embeddinggemma-300m
EMBEDDING_DIMENSION=768

# ----- Database 설정 (macOS 로컬) -----
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=spatial_rag
DATABASE_USER=postgres
DATABASE_PASSWORD=postgres

# ----- 검색 설정 -----
RETRIEVAL_TOP_K=10
HYBRID_ALPHA=0.40
HYBRID_BETA=0.25
DEFAULT_RADIUS_M=500

# ----- LLM 설정 (선택) -----
OPENAI_API_KEY=
LLM_MODEL=gpt-4o-mini
LLM_TEMPERATURE=0.0
```

---

## 6. 데이터베이스 초기화

### 6.1 스키마 적용

```bash
psql -d spatial_rag -f schema.sql
```

### 6.2 테이블 확인

```bash
psql -d spatial_rag -c "\dt"
```

예상 출력:
```
             List of relations
 Schema |        Name        | Type  | Owner
--------+--------------------+-------+----------
 public | reranker_training  | table | postgres
 public | spatial_docs       | table | postgres
```

### 6.3 확장 확인

```bash
psql -d spatial_rag -c "\dx"
```

예상 출력:
```
                        List of installed extensions
  Name   | Version |   Schema   |                Description
---------+---------+------------+--------------------------------------------
 plpgsql | 1.0     | pg_catalog | PL/pgSQL procedural language
 postgis | 3.4.0   | public     | PostGIS geometry and geography types
 vector  | 0.5.1   | public     | vector data type and ivfflat access method
```

---

## 7. 서버 실행

### 7.1 백엔드 서버 시작

```bash
# Conda 환경 활성화
conda activate spatial-rag

# 프로젝트 디렉토리로 이동
cd /path/to/Spatial-RAG

# FastAPI 서버 시작
cd api
uvicorn app.main:app --reload --port 8080
```

### 7.2 API 확인

```bash
# 헬스 체크
curl http://localhost:8080/health

# Swagger UI
open http://localhost:8080/docs
```

### 7.3 프론트엔드 서버 시작 (별도 터미널)

```bash
cd /path/to/Spatial-RAG/frontend
npm install
npm run dev
```

접속: http://localhost:3000

---

## 8. Apple Silicon 고려사항

### 8.1 PyTorch MPS 가속

M4 Max의 GPU를 활용하려면 MPS(Metal Performance Shaders)를 사용할 수 있습니다:

```python
import torch

# MPS 디바이스 사용
device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
model = model.to(device)
```

> **참고**: sentence-transformers는 기본적으로 CPU를 사용합니다. MPS 가속이 필요하면 명시적으로 설정해야 합니다.

### 8.2 메모리 관리

M4 Max는 통합 메모리를 사용하므로:

- **embeddinggemma-300m**: ~1.2GB VRAM 사용
- 충분한 메모리(64GB+)가 있다면 배치 사이즈를 늘려 성능 향상 가능

### 8.3 알려진 호환성 이슈

| 패키지 | 상태 | 비고 |
|--------|------|------|
| PyTorch | ✅ 지원 | MPS 백엔드 사용 가능 |
| sentence-transformers | ✅ 지원 | 정상 동작 |
| geopandas | ✅ 지원 | ARM64 네이티브 |
| psycopg2-binary | ✅ 지원 | Homebrew PostgreSQL과 호환 |
| h3 | ✅ 지원 | ARM64 wheel 제공 |

### 8.4 성능 최적화 팁

```python
# embeddings.py에서 배치 사이즈 조정 가능
embeddings = model.encode(
    texts,
    normalize_embeddings=True,
    batch_size=64,  # M4 Max에서는 큰 배치 가능
    show_progress_bar=True
)
```

### 8.5 Rosetta 2 없이 네이티브 실행

모든 패키지가 ARM64 네이티브로 실행되는지 확인:

```bash
# Python 아키텍처 확인
python -c "import platform; print(platform.machine())"
# 출력: arm64

# PostgreSQL 아키텍처 확인
file $(which psql)
# 출력: ... arm64
```

---

## 트러블슈팅

### PostgreSQL 연결 실패

```bash
# PostgreSQL 서비스 상태 확인
brew services list

# 재시작
brew services restart postgresql@15
```

### pgvector 확장 로드 실패

```bash
# pgvector 재설치
brew reinstall pgvector

# PostgreSQL 재시작
brew services restart postgresql@15
```

### HuggingFace 인증 오류

```bash
# 토큰 확인
huggingface-cli whoami

# 재로그인
huggingface-cli login
```

### PyTorch MPS 오류

```python
# MPS 폴백 설정
import os
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
```

---

## 빠른 시작 체크리스트

- [ ] Homebrew 설치
- [ ] PostgreSQL 15 + PostGIS + pgvector 설치
- [ ] PostgreSQL 서비스 시작
- [ ] spatial_rag 데이터베이스 생성
- [ ] PostGIS, vector 확장 설치
- [ ] Miniforge/Conda 설치
- [ ] spatial-rag 환경 생성 및 활성화
- [ ] Python 패키지 설치
- [ ] .env 파일 설정 (HuggingFace 토큰 포함)
- [ ] schema.sql 적용
- [ ] FastAPI 서버 실행 확인
- [ ] http://localhost:8080/health 응답 확인

---

## 다음 단계

설치가 완료되면:

1. 맛집 데이터 수집 (공덕역 500m 반경)
2. 데이터 시딩 스크립트 실행
3. 검색 API 테스트
