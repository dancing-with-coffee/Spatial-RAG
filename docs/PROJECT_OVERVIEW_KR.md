# Spatial-RAG 프로젝트 개요

공간 지능(Spatial Intelligence)과 의미 검색(Semantic Search)을 결합한 지리공간 RAG 시스템

---

## 목차

1. [프로젝트 소개](#1-프로젝트-소개)
2. [시스템 구성](#2-시스템-구성)
3. [데이터 흐름](#3-데이터-흐름)
4. [확장 아이디어: 한국 부동산](#4-확장-아이디어-한국-부동산)
5. [확장 아이디어: 한국 맛집](#5-확장-아이디어-한국-맛집)
6. [공통 확장 고려사항](#6-공통-확장-고려사항)

---

## 1. 프로젝트 소개

### 1.1 Spatial-RAG란?

Spatial-RAG는 **공간적 근접성(Spatial Proximity)**과 **의미적 유사성(Semantic Similarity)**을 결합한 하이브리드 검색 시스템입니다. 기존 RAG 시스템이 텍스트의 의미만 고려하는 것과 달리, Spatial-RAG는 "어디에서"라는 공간 정보를 함께 활용합니다.

**핵심 수식:**
```
hybrid_score = 0.7 × semantic_similarity + 0.3 × spatial_score
```

- **semantic_similarity**: 쿼리와 문서 간 의미적 유사도 (0~1)
- **spatial_score**: 공간적 근접도 = 1 / (1 + 거리(m))

### 1.2 핵심 기술 스택

| 계층 | 기술 | 역할 |
|------|------|------|
| **프론트엔드** | Next.js 14, TypeScript, Tailwind CSS | 사용자 인터페이스 |
| **지도** | Leaflet, React-Leaflet | 지도 시각화 |
| **상태관리** | Zustand | 클라이언트 상태 |
| **백엔드** | FastAPI (Python) | REST API 서버 |
| **임베딩** | BGE-small-en-v1.5 (384차원) | 텍스트 벡터화 |
| **LLM** | OpenAI GPT-4o-mini (선택사항) | 답변 생성 |
| **DB** | PostgreSQL 15 | 데이터 저장소 |
| **공간 확장** | PostGIS | 지리공간 쿼리 |
| **벡터 확장** | pgvector | 벡터 유사도 검색 |
| **공간 인덱싱** | H3 | 계층적 공간 인덱스 |

### 1.3 아키텍처 다이어그램

```
┌─────────────────────────────────────────────────────────────┐
│                     사용자 브라우저                           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              프론트엔드 (Next.js 14) :3000                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  QueryPanel  │  │     Map      │  │ ResultsList  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                          │                                  │
│                    Zustand Store                            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼ REST API
┌─────────────────────────────────────────────────────────────┐
│                  백엔드 (FastAPI) :8080                      │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ /query - 하이브리드 검색 + LLM 답변                    │  │
│  │ /stream - SSE 스트리밍 응답                           │  │
│  │ /documents - 문서 조회                                │  │
│  └──────────────────────────────────────────────────────┘  │
│                              │                              │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐           │
│  │ Retriever  │  │ Embeddings │  │    LLM     │           │
│  │ (하이브리드) │  │   (BGE)    │  │ (OpenAI)   │           │
│  └────────────┘  └────────────┘  └────────────┘           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼ SQL
┌─────────────────────────────────────────────────────────────┐
│            PostgreSQL + PostGIS + pgvector :5432            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ spatial_docs 테이블                                   │  │
│  │ - geom (GEOMETRY) ← PostGIS                          │  │
│  │ - embedding (VECTOR) ← pgvector                       │  │
│  │ - h3_index (BIGINT) ← H3 인덱스                        │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. 시스템 구성

### 2.1 백엔드 (FastAPI)

#### 디렉토리 구조

```
api/
├── app/
│   ├── main.py           # API 엔드포인트 정의
│   ├── retriever.py      # 하이브리드 검색 로직
│   ├── spatial_query.py  # PostGIS 쿼리 빌더
│   ├── embeddings.py     # BGE 임베딩 모델
│   ├── llm_generator.py  # LLM 응답 생성
│   ├── database.py       # DB 연결 관리
│   └── config.py         # 환경 설정
├── seed.py               # 테스트 데이터 생성
└── requirements.txt
```

#### 주요 API 엔드포인트

| 엔드포인트 | 메서드 | 설명 |
|-----------|--------|------|
| `/query` | POST | 하이브리드 검색 실행 + LLM 답변 생성 |
| `/stream` | GET | SSE 방식 실시간 스트리밍 응답 |
| `/documents` | GET | 문서 목록 조회 (페이지네이션) |
| `/documents/{id}` | GET | 단일 문서 상세 조회 |
| `/health` | GET | 서비스 상태 확인 |

#### 하이브리드 검색 로직 (retriever.py)

```python
class SpatialHybridRetriever:
    """공간 + 의미 하이브리드 검색기"""

    def retrieve(self, query, center_lat, center_lon, radius_m, top_k):
        # 1. 쿼리 임베딩 생성
        query_embedding = self.embedding_model.embed_query(query)

        # 2. 공간 필터 구성
        spatial_filter = build_spatial_filter(center_lat, center_lon, radius_m)

        # 3. 하이브리드 쿼리 실행
        results = build_hybrid_query(query_embedding, spatial_filter, top_k)

        return results
```

#### 공간 쿼리 빌더 (spatial_query.py)

두 가지 공간 필터 모드 지원:
- **반경 검색**: `ST_DWithin(geom::geography, point, radius_m)`
- **영역 검색**: `ST_Intersects(geom, region_polygon)`

```sql
-- 하이브리드 스코어링 쿼리 예시
SELECT
    id, title, content,
    1 - (embedding <=> query_vector) AS semantic_score,
    1.0 / (1.0 + ST_Distance(geom::geography, point)) AS spatial_score,
    hybrid_score(embedding <=> query_vector, ST_Distance(...)) AS hybrid_score
FROM spatial_docs
WHERE ST_DWithin(geom::geography, point, radius_m)
ORDER BY hybrid_score DESC
LIMIT top_k;
```

#### 임베딩 모델 (embeddings.py)

- **모델**: BAAI/bge-small-en-v1.5
- **차원**: 384
- **BGE 프리픽스 규칙**:
  - 쿼리: `"query: "` 접두사 추가
  - 문서: `"passage: "` 접두사 추가

### 2.2 프론트엔드 (Next.js 14)

#### 디렉토리 구조

```
frontend/app/
├── page.tsx              # 메인 페이지 레이아웃
├── layout.tsx            # 루트 레이아웃
├── globals.css           # 전역 스타일
├── components/
│   ├── QueryPanel.tsx    # 검색 폼
│   ├── Map.tsx           # Leaflet 지도
│   ├── ResultsList.tsx   # 검색 결과 목록
│   └── AnswerDisplay.tsx # LLM 답변 표시
├── store/
│   └── useStore.ts       # Zustand 상태 관리
└── lib/
    ├── schemas.ts        # Zod 스키마 정의
    └── geojson.ts        # GeoJSON 유틸리티
```

#### 상태 관리 (Zustand)

```typescript
interface AppState {
  // 검색 상태
  query: string;
  isLoading: boolean;
  error: string | null;

  // 결과 상태
  answer: string | null;
  documents: Document[];
  selectedDocumentId: string | null;

  // 지도 상태
  mapCenter: [number, number];  // [위도, 경도]
  mapZoom: number;
  drawnRegion: GeoJSON | null;  // 사용자가 그린 영역

  // 검색 파라미터
  radiusM: number;              // 검색 반경 (미터)
  topK: number;                 // 반환할 문서 수
}
```

#### 지도 컴포넌트 (Map.tsx)

- **타일**: OpenStreetMap
- **기능**:
  - 검색 반경 시각화 (원형 오버레이)
  - 문서 위치 마커 표시
  - 폴리곤 문서 영역 표시
  - 선택된 문서로 이동 (fly-to 애니메이션)
  - 점수 정보 팝업 표시

### 2.3 데이터베이스 (PostgreSQL + PostGIS + pgvector)

#### 메인 테이블: spatial_docs

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `id` | UUID | 문서 고유 식별자 |
| `title` | TEXT | 문서 제목 |
| `content` | TEXT | 문서 내용 |
| `geom` | GEOMETRY(Geometry, 4326) | 지리 정보 (WGS84) |
| `h3_index` | BIGINT | H3 공간 인덱스 (해상도 8, ~460m) |
| `embedding` | VECTOR(384) | BGE 임베딩 벡터 |
| `metadata` | JSONB | 추가 메타데이터 |
| `created_at` | TIMESTAMP | 생성 시간 |
| `updated_at` | TIMESTAMP | 수정 시간 |

#### 인덱스 구성

| 인덱스 | 타입 | 용도 |
|--------|------|------|
| `idx_spatial_docs_geom` | GiST | 공간 근접 검색 가속 |
| `idx_spatial_docs_h3` | B-tree | H3 버킷 검색 |
| `idx_spatial_docs_embedding` | IVFFlat (cosine) | 벡터 유사도 검색 |
| `idx_spatial_docs_created_at` | B-tree | 최신순 정렬 |
| `idx_spatial_docs_metadata` | GIN | JSONB 키 검색 |

#### 하이브리드 스코어 함수

```sql
CREATE FUNCTION hybrid_score(
    semantic_dist FLOAT,
    spatial_dist_m FLOAT,
    alpha FLOAT DEFAULT 0.7,
    beta FLOAT DEFAULT 0.3
) RETURNS FLOAT AS $$
BEGIN
    RETURN alpha * (1.0 - semantic_dist) + beta * (1.0 / (1.0 + spatial_dist_m));
END;
$$ LANGUAGE plpgsql;
```

---

## 3. 데이터 흐름

### 3.1 문서 저장 과정

```
1. 문서 데이터 입력
   └─ 제목, 내용, 위치 정보 (GeoJSON)

2. 임베딩 생성
   └─ BGE 모델로 content를 384차원 벡터로 변환
   └─ "passage: " 접두사 추가

3. 공간 인덱스 생성
   └─ GeoJSON → WKT 변환
   └─ 중심점에서 H3 인덱스 계산 (해상도 8)

4. DB 저장
   └─ spatial_docs 테이블에 INSERT
   └─ ST_GeomFromText()로 지오메트리 변환
```

### 3.2 쿼리 실행 과정

```
1. 사용자 쿼리 입력
   └─ 텍스트: "강남역 근처 카페"
   └─ 공간 정보: 중심 좌표 + 반경 또는 영역

2. 쿼리 임베딩 생성
   └─ "query: 강남역 근처 카페" → 384차원 벡터

3. 하이브리드 검색 실행
   └─ 공간 필터: ST_DWithin()로 반경 내 문서 필터
   └─ 의미 검색: embedding <=> query_vector (코사인 거리)
   └─ 점수 계산: 0.7 × 의미 + 0.3 × 공간
   └─ 상위 K개 반환

4. LLM 답변 생성 (선택)
   └─ 검색된 문서들을 컨텍스트로 제공
   └─ GPT-4o-mini가 종합 답변 생성

5. 결과 반환
   └─ 문서 목록 + 점수 + LLM 답변
```

### 3.3 하이브리드 스코어링 예시

"CBD 근처 용도지역 정보" 쿼리 예시:

| 문서 | 의미 점수 | 거리(m) | 공간 점수 | 하이브리드 점수 |
|------|----------|--------|----------|----------------|
| A | 0.85 | 100 | 0.0099 | **0.598** |
| B | 0.70 | 50 | 0.0196 | **0.496** |
| C | 0.90 | 2000 | 0.0005 | **0.630** |

→ 문서 C가 가장 높은 점수 (의미적으로 가장 관련성 높음)

---

## 4. 확장 아이디어: 한국 부동산

### 4.1 서비스 개요

**"AI 부동산 검색 도우미"** - 자연어로 원하는 매물을 찾아주는 서비스

**쿼리 예시:**
- "강남역 도보 10분 이내 10억 이하 아파트"
- "판교 근처 학군 좋은 30평대 빌라"
- "홍대입구역 근처 투룸 월세 100만원 이하"

### 4.2 데이터 구조 변경

#### 기존 spatial_docs → properties (매물 테이블)

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `id` | UUID | 매물 ID |
| `title` | TEXT | 매물 제목 |
| `description` | TEXT | 상세 설명 |
| `geom` | GEOMETRY | 매물 위치 |
| `h3_index` | BIGINT | H3 인덱스 |
| `embedding` | VECTOR(768) | 한국어 임베딩 |
| `property_type` | ENUM | 아파트/빌라/오피스텔/상가/원룸 |
| `transaction_type` | ENUM | 매매/전세/월세 |
| `price` | BIGINT | 가격 (만원) |
| `deposit` | BIGINT | 보증금 (만원) |
| `monthly_rent` | INTEGER | 월세 (만원) |
| `area_sqm` | FLOAT | 면적 (m2) |
| `floor` | INTEGER | 층수 |
| `total_floors` | INTEGER | 총 층수 |
| `built_year` | INTEGER | 건축년도 |
| `metadata` | JSONB | 추가 정보 |

#### 메타데이터 구조

```json
{
  "address": {
    "road": "서울특별시 강남구 테헤란로 123",
    "jibun": "서울특별시 강남구 역삼동 123-45"
  },
  "rooms": 3,
  "bathrooms": 2,
  "direction": "남향",
  "parking": true,
  "elevator": true,
  "school_district": {
    "elementary": "역삼초등학교",
    "middle": "역삼중학교",
    "distance_m": 350
  },
  "nearby": {
    "subway_station": "강남역",
    "subway_line": "2호선",
    "subway_distance_m": 200,
    "convenience_store": 50,
    "hospital": 500
  }
}
```

### 4.3 확장된 하이브리드 스코어링

```
부동산 점수 = 0.5 × 의미 유사도
           + 0.2 × 공간 근접도
           + 0.15 × 교통 접근성
           + 0.1 × 학군 점수
           + 0.05 × 생활 인프라 점수
```

#### 교통 접근성 점수

```python
def calculate_transit_score(property, user_preferences):
    """지하철역 근접도 + 버스정류장 근접도"""
    subway_score = 1.0 / (1.0 + property.subway_distance_m / 500)
    bus_score = 1.0 / (1.0 + property.bus_distance_m / 200)
    return 0.7 * subway_score + 0.3 * bus_score
```

#### 학군 점수

```python
def calculate_school_score(property, school_data):
    """초/중/고 거리 + 학업 성취도"""
    distance_score = 1.0 / (1.0 + property.school_distance_m / 1000)
    achievement_score = school_data.achievement_percentile / 100
    return 0.5 * distance_score + 0.5 * achievement_score
```

### 4.4 데이터 소스

| 소스 | 데이터 | 용도 |
|------|--------|------|
| **국토교통부 실거래가 API** | 아파트/빌라/오피스텔 실거래 | 시세 분석 |
| **공공데이터포털** | 학교 위치, 지하철역 | 인프라 점수 |
| **카카오맵 API** | POI, 도보 거리 | 접근성 계산 |
| **네이버 부동산** | 매물 정보 (크롤링 주의) | 매물 데이터 |
| **직방/다방 API** | 원룸/투룸 매물 | 소형 매물 |

### 4.5 쿼리 확장 예시

**입력**: "강남역 근처 역세권 신축 아파트 10억 이하"

**파싱 결과**:
```json
{
  "location": {"name": "강남역", "lat": 37.498, "lon": 127.028},
  "filters": {
    "property_type": "아파트",
    "transit_access": "역세권",
    "built_year_min": 2020,
    "price_max": 100000
  },
  "radius_m": 1000
}
```

**SQL 쿼리**:
```sql
SELECT *, hybrid_score_extended(...) AS score
FROM properties
WHERE property_type = '아파트'
  AND price <= 100000
  AND built_year >= 2020
  AND ST_DWithin(geom::geography, ST_Point(127.028, 37.498)::geography, 1000)
ORDER BY score DESC
LIMIT 10;
```

### 4.6 추가 기능 아이디어

1. **시세 추이 분석**: "이 아파트 최근 1년 시세 변화는?"
2. **투자 수익률 계산**: "전세가율, 예상 수익률 계산"
3. **유사 매물 추천**: "이 매물과 비슷한 다른 매물 추천"
4. **학군 상세 분석**: "주변 학교 입시 실적, 학원가 정보"
5. **미래 개발 정보**: "재개발/재건축 예정 지역 표시"

---

## 5. 확장 아이디어: 한국 맛집

### 5.1 서비스 개요

**"AI 맛집 검색 도우미"** - 상황에 맞는 맛집을 찾아주는 서비스

**쿼리 예시:**
- "강남역 근처 혼밥하기 좋은 일식집"
- "홍대 데이트하기 좋은 분위기 있는 이탈리안"
- "판교 회식 장소 20명 단체석 있는 곳"

### 5.2 데이터 구조 변경

#### restaurants (음식점 테이블)

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `id` | UUID | 음식점 ID |
| `name` | TEXT | 상호명 |
| `description` | TEXT | 음식점 설명 |
| `geom` | GEOMETRY | 위치 |
| `h3_index` | BIGINT | H3 인덱스 |
| `embedding` | VECTOR(768) | 한국어 임베딩 |
| `cuisine_type` | TEXT[] | 음식 종류 (한식, 일식, 중식...) |
| `price_range` | ENUM | 저가/중가/고가 |
| `average_price` | INTEGER | 1인 평균 가격 |
| `rating` | FLOAT | 평점 (1-5) |
| `review_count` | INTEGER | 리뷰 수 |
| `metadata` | JSONB | 추가 정보 |

#### 메타데이터 구조

```json
{
  "address": {
    "road": "서울특별시 마포구 와우산로 123",
    "jibun": "서울특별시 마포구 서교동 123-45"
  },
  "hours": {
    "monday": "11:00-22:00",
    "tuesday": "11:00-22:00",
    "break_time": "15:00-17:00",
    "last_order": "21:00"
  },
  "features": {
    "parking": true,
    "reservation": true,
    "delivery": false,
    "takeout": true,
    "pet_friendly": false,
    "kid_friendly": true
  },
  "atmosphere": ["데이트", "가족모임", "혼밥"],
  "capacity": {
    "total_seats": 50,
    "private_room": true,
    "max_group_size": 20
  },
  "signature_menu": [
    {"name": "숙성 삼겹살", "price": 18000},
    {"name": "된장찌개", "price": 8000}
  ],
  "nearby": {
    "subway_station": "홍대입구역",
    "subway_distance_m": 150
  }
}
```

### 5.3 확장된 하이브리드 스코어링

```
맛집 점수 = 0.4 × 의미 유사도
         + 0.25 × 공간 근접도
         + 0.2 × 평점 점수
         + 0.1 × 인기도 점수
         + 0.05 × 최신성 점수
```

#### 평점 점수

```python
def calculate_rating_score(restaurant):
    """평점 + 리뷰 수 가중치"""
    base_score = restaurant.rating / 5.0
    reliability = min(restaurant.review_count / 100, 1.0)  # 리뷰 100개 이상이면 1.0
    return base_score * (0.7 + 0.3 * reliability)
```

#### 분위기 매칭 점수

```python
def calculate_atmosphere_match(restaurant, user_intent):
    """사용자 의도와 분위기 매칭"""
    # "혼밥" → ["혼밥", "조용한"]
    # "데이트" → ["데이트", "분위기", "로맨틱"]
    intent_keywords = extract_intent_keywords(user_intent)
    restaurant_atmosphere = restaurant.metadata['atmosphere']

    matches = len(set(intent_keywords) & set(restaurant_atmosphere))
    return matches / len(intent_keywords)
```

### 5.4 데이터 소스

| 소스 | 데이터 | 용도 |
|------|--------|------|
| **카카오맵 API** | 음식점 기본 정보, 리뷰 | 기본 데이터 |
| **네이버 플레이스 API** | 음식점 정보, 예약 | 기본 데이터 |
| **망고플레이트** | 평점, 리뷰 | 평점 데이터 |
| **다이닝코드** | 미식 평가 | 전문 평가 |
| **캐치테이블** | 예약 정보 | 예약 연동 |
| **배달의민족/요기요** | 메뉴, 가격 | 메뉴 데이터 |

### 5.5 쿼리 확장 예시

**입력**: "홍대 근처 분위기 좋은 파스타집 2인 예약 가능한 곳"

**파싱 결과**:
```json
{
  "location": {"name": "홍대", "lat": 37.556, "lon": 126.923},
  "cuisine": ["이탈리안", "파스타"],
  "atmosphere": ["분위기", "데이트"],
  "filters": {
    "reservation": true,
    "capacity_min": 2
  },
  "radius_m": 500
}
```

**SQL 쿼리**:
```sql
SELECT *, hybrid_score_restaurant(...) AS score
FROM restaurants
WHERE cuisine_type && ARRAY['이탈리안', '파스타']
  AND (metadata->'features'->>'reservation')::boolean = true
  AND ST_DWithin(geom::geography, ST_Point(126.923, 37.556)::geography, 500)
ORDER BY score DESC
LIMIT 10;
```

### 5.6 추가 기능 아이디어

1. **웨이팅 시간 예측**: "지금 가면 얼마나 기다려야 할까?"
2. **메뉴 추천**: "이 집 시그니처 메뉴가 뭐야?"
3. **예약 연동**: "오늘 저녁 7시 2명 예약해줘"
4. **코스 추천**: "홍대에서 카페-저녁-바 코스 추천"
5. **유사 맛집 추천**: "여기랑 비슷한 다른 맛집은?"
6. **영업시간 필터**: "지금 열려있는 곳만 보여줘"

---

## 6. 공통 확장 고려사항

### 6.1 한국어 임베딩 모델

현재 시스템은 영어 모델(BGE-small-en-v1.5)을 사용하지만, 한국 서비스를 위해 한국어 모델로 전환이 필요합니다.

| 모델 | 차원 | 특징 | 추천 용도 |
|------|------|------|----------|
| **KoSimCSE** | 768 | 한국어 문장 유사도 최적화 | 일반 검색 |
| **KoBERT** | 768 | SKT 개발, 범용 | 범용 |
| **multilingual-e5** | 768 | 다국어 지원 | 다국어 서비스 |
| **BGE-m3** | 1024 | 다국어 + 고성능 | 고품질 검색 |

**embeddings.py 수정 예시:**

```python
class KoreanEmbeddingModel:
    MODEL_NAME = "BM-K/KoSimCSE-roberta-multitask"
    DIMENSION = 768

    def embed_query(self, query: str) -> List[float]:
        # 한국어는 query/passage 접두사 불필요
        return self._encode(query)
```

### 6.2 한국 주소 체계 지원

#### 도로명 주소 ↔ 지번 주소 변환

```python
from vworld_api import VWorldGeocoder

class KoreanAddressParser:
    def __init__(self):
        self.geocoder = VWorldGeocoder(api_key="...")

    def parse(self, address: str) -> dict:
        """주소 → 좌표 + 정규화된 주소"""
        result = self.geocoder.geocode(address)
        return {
            "lat": result.lat,
            "lon": result.lon,
            "road_address": result.road_address,
            "jibun_address": result.jibun_address,
            "sido": result.sido,
            "sigungu": result.sigungu,
            "dong": result.dong
        }
```

#### 행정구역 기반 검색

```sql
-- 강남구 내 모든 매물
SELECT * FROM properties
WHERE metadata->>'sigungu' = '강남구';

-- 역삼동 주변 음식점
SELECT * FROM restaurants
WHERE metadata->>'dong' = '역삼동'
   OR ST_DWithin(geom::geography, dong_center, 500);
```

### 6.3 한국 지도 서비스 연동

#### 카카오맵 연동

```typescript
// frontend/app/components/KakaoMap.tsx
import { Map, MapMarker } from 'react-kakao-maps-sdk';

export function KakaoMap({ center, markers }) {
  return (
    <Map center={center} level={3}>
      {markers.map(marker => (
        <MapMarker
          key={marker.id}
          position={{ lat: marker.lat, lng: marker.lng }}
          onClick={() => handleMarkerClick(marker)}
        />
      ))}
    </Map>
  );
}
```

#### 네이버 지도 연동

```typescript
// 네이버 지도 Static API 활용
const staticMapUrl = `https://naveropenapi.apigw.ntruss.com/map-static/v2/raster?
  center=${lon},${lat}&level=16&w=500&h=400&
  markers=type:d|size:mid|pos:${lon} ${lat}`;
```

### 6.4 한글 자연어 처리 (위치 추출)

```python
import re
from konlpy.tag import Okt

class KoreanLocationExtractor:
    LOCATION_PATTERNS = [
        r"(.+?역)\s*(근처|주변|앞|뒤)",
        r"(.+?동)\s*(에서|에|내)",
        r"(.+?로)\s*(\d+번지?)?",
        r"(.+?구)\s*(.+?동)?",
    ]

    def extract(self, query: str) -> list:
        """쿼리에서 위치 정보 추출"""
        locations = []

        for pattern in self.LOCATION_PATTERNS:
            matches = re.findall(pattern, query)
            locations.extend(matches)

        return self._geocode_locations(locations)
```

### 6.5 성능 최적화

#### 한국 지역 특화 H3 해상도

```python
# 도심 지역: 해상도 9 (~175m) - 더 세밀한 검색
# 외곽 지역: 해상도 8 (~460m) - 기존 유지
# 농촌 지역: 해상도 7 (~1.2km) - 넓은 범위

def get_h3_resolution(lat, lon):
    if is_urban_area(lat, lon):
        return 9
    elif is_suburban_area(lat, lon):
        return 8
    else:
        return 7
```

#### 캐싱 전략

```python
from functools import lru_cache
import redis

# 자주 검색되는 지역 임베딩 캐싱
@lru_cache(maxsize=1000)
def get_cached_embedding(location_name: str):
    return embedding_model.embed_query(location_name)

# Redis로 검색 결과 캐싱
def cache_search_results(query_hash, results, ttl=3600):
    redis_client.setex(f"search:{query_hash}", ttl, json.dumps(results))
```

---

## 마무리

Spatial-RAG는 공간 지능과 의미 검색을 결합한 강력한 프레임워크입니다. 한국 부동산과 맛집 서비스로 확장할 때 핵심은:

1. **한국어 임베딩 모델** 전환
2. **한국 주소 체계** 지원
3. **도메인별 스코어링** 공식 조정
4. **한국 지도 서비스** 연동
5. **적절한 데이터 소스** 확보

이 문서가 프로젝트 이해와 확장 계획 수립에 도움이 되길 바랍니다.
