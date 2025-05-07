# FastAPI + LangChain RAG 시스템

이 프로젝트는 FastAPI와 LangChain을 활용하여 Retrieval-Augmented Generation(RAG) 시스템을 구축한 웹 API 서비스입니다.

## 주요 기능

- 📝 문서 업로드 및 관리 (PDF, TXT, CSV, HTML 지원)
- 🔍 질문에 대한 관련 문서 검색
- 💬 대화 내역을 고려한 RAG 기반 응답 생성
- 📊 응답 품질 평가 및 개선

## 시작하기

### 필수 조건

- Python 3.9 이상
- OpenAI API 키

### 설치 방법

1. 저장소 클론하기

```bash
git clone https://github.com/yourusername/fastapi-rag-system.git
cd fastapi-rag-system
```

2. 가상 환경 생성 및 활성화

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. 의존성 패키지 설치

```bash
pip install -r requirements.txt
```

4. `.env` 파일 설정

```bash
cp .env.example .env
```

`.env` 파일을 편집하여 OpenAI API 키 및 기타 설정을 입력하세요.

### 실행 방법

```bash
python -m app.main
```

또는

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

서버가 실행되면 http://localhost:8000 에서 API에 접근할 수 있습니다.

### Docker를 사용한 실행

1. Docker와 Docker Compose 설치 (미설치 시)

2. Docker 이미지 빌드 및 컨테이너 실행

```bash
docker compose up -d --build
```

3. 서비스 상태 확인

```bash
docker compose ps
```

4. 로그 확인

```bash
docker compose logs -f
```

5. 서비스 중지

```bash
docker compose down
```

## API 문서

API 문서는 다음 URL에서 확인할 수 있습니다:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 주요 API 엔드포인트

### 문서 관리 API

- `POST /documents/upload` - 문서 업로드 및 Vector Store에 추가
- `GET /documents/` - 모든 문서 목록 조회
- `DELETE /documents/` - 특정 문서 삭제

### 채팅 API

- `POST /chat/` - RAG 기반 질의응답
- `POST /chat/conversation` - 대화 내역을 고려한 질의응답

## 프로젝트 구조

```
/rag_api
  /app
    main.py                # FastAPI 애플리케이션 엔트리 포인트
    config.py              # 환경 설정
    /api
      chat.py              # 채팅 관련 API 엔드포인트
      documents.py         # 문서 관리 API 엔드포인트
    /core
      config.py            # 설정 관리
      security.py          # 인증/권한 관리
    /models
      request.py           # 요청 Pydantic 모델
      response.py          # 응답 Pydantic 모델
    /services
      embeddings.py        # 임베딩 관련 기능
      retriever.py         # 검색 관련 기능
      llm.py               # LLM 관련 기능
      rag.py               # RAG 로직 통합
      document_service.py  # 문서 관리 서비스
    /utils
      response_formatter.py # 응답 포맷팅 유틸리티
      answer_enhancer.py    # 답변 강화 유틸리티
      quality_evaluator.py  # 품질 평가 유틸리티
    /exceptions.py         # 사용자 정의 예외
    /dependencies.py       # 의존성 주입 함수
  /data
    /documents             # 원본 문서 저장 디렉토리
    /chroma_db             # Vector Store 데이터 디렉토리
  Dockerfile               # Docker 이미지 빌드 파일
  docker-compose.yml       # Docker Compose 설정 파일
  .dockerignore            # Docker 빌드 제외 파일 목록
  requirements.txt         # 의존성 패키지 목록
  .env                     # 환경 변수 파일 (API 키 등)
  README.md                # 프로젝트 설명서
```

## 환경 변수 설정

`.env` 파일에서 다음 환경 변수를 설정할 수 있습니다:

- `OPENAI_API_KEY` - OpenAI API 키
- `DEBUG` - 디버그 모드 활성화 (True/False)
- `HOST` - 서버 호스트 (기본값: 0.0.0.0)
- `PORT` - 서버 포트 (기본값: 8000)
- `VECTOR_STORE_DIR` - Vector Store 데이터 디렉토리 경로
- `RETRIEVER_K` - 검색 결과 개수 (기본값: 3)
- `EMBEDDING_MODEL_NAME` - 임베딩 모델 이름 (기본값: text-embedding-3-small)
- `LLM_MODEL_NAME` - LLM 모델 이름 (기본값: gpt-4o)

## 도커 환경 구성

도커 환경에서는 다음 파일들이 사용됩니다:

- `Dockerfile`: 컨테이너 이미지 빌드 정의
- `docker-compose.yml`: 서비스 구성 및 네트워크 설정
- `.dockerignore`: 빌드 컨텍스트에서 제외할 파일 목록

데이터 지속성을 위해 다음 볼륨이 마운트됩니다:
- `./data:/app/data`: 문서 및 벡터 저장소 데이터
- `./.env:/app/.env`: 환경 변수 파일

### 도커 컨테이너 관리

```bash
# 컨테이너 로그 확인
docker compose logs -f rag-api

# 컨테이너 내부 접속
docker compose exec rag-api bash

# 컨테이너 재시작
docker compose restart rag-api

# 서비스 업데이트 (코드 변경 후)
docker compose up -d --build rag-api
```

## 예제 요청

### 문서 업로드

```bash
curl -X 'POST' \
  'http://localhost:8000/documents/upload' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'file=@sample.pdf;type=application/pdf' \
  -F 'description=샘플 문서' \
  -F 'metadata={"author": "홍길동", "category": "기술 문서"}'
```

### 질의응답

```bash
curl -X 'POST' \
  'http://localhost:8000/chat/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "query": "FastAPI의 주요 특징은 무엇인가요?",
  "history": []
}'
```

## 참고 사항

- 모든 문서는 `data/documents` 디렉토리에 저장됩니다.
- Vector Store 데이터는 `data/chroma_db` 디렉토리에 저장됩니다.
- API 응답은 항상 표준화된 형식(`ApiResponse`)으로 반환됩니다.

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 LICENSE 파일을 참조하세요.