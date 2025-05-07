from fastapi import FastAPI, Request, status, Response, Cookie
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.api import chat, documents
from app.exceptions import RAGServiceError
from app.models.response import ApiResponse
from app.core.config import settings
import logging
import os
from datetime import datetime
import uuid
from app.session_memory import SESSION_MEMORY, SESSION_COOKIE_NAME

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# FastAPI 앱 생성
app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS 미들웨어 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 배포 시에는 구체적인 오리진 목록으로 변경 필요
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 파일 설정
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# 템플릿 설정
templates = Jinja2Templates(directory="app/templates")

# 라우터 등록
app.include_router(chat.router)
app.include_router(documents.router)

# 전역 예외 처리기
@app.exception_handler(RAGServiceError)
async def rag_service_exception_handler(request: Request, exc: RAGServiceError):
    """RAG 서비스 예외 처리기"""
    return JSONResponse(
        status_code=exc.status_code,
        content=ApiResponse(
            success=False,
            error={
                "type": type(exc).__name__,
                "message": exc.message,
                "status_code": exc.status_code
            },
            meta={"path": str(request.url)}
        ).model_dump()
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """전역 예외 처리기"""
    logger.error(f"처리되지 않은 예외: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ApiResponse(
            success=False,
            error={
                "type": type(exc).__name__,
                "message": "서버 내부 오류가 발생했습니다",
                "status_code": 500
            },
            meta={"path": str(request.url)}
        ).model_dump()
    )

# 앱 시작 시 디렉토리 생성
@app.on_event("startup")
async def startup_event():
    logger.info("애플리케이션을 시작합니다...")
    
    # Vector Store 디렉토리 생성
    os.makedirs(settings.VECTOR_STORE_DIR, exist_ok=True)
    
    # 문서 저장 디렉토리 생성
    documents_dir = os.path.join("data", "documents")
    os.makedirs(documents_dir, exist_ok=True)
    
    logger.info(f"애플리케이션이 시작되었습니다. (버전: {settings.APP_VERSION})")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("애플리케이션을 종료합니다...")

@app.get("/", response_model=ApiResponse)
async def root(request: Request, response: Response, rag_session_id: str = Cookie(default=None)):
    """메인 페이지 렌더링 및 세션 쿠키 발급"""
    ####메모리 관련 수정#####
    # 세션 ID가 없으면 새로 발급
    if not rag_session_id:
        rag_session_id = str(uuid.uuid4())
        response.set_cookie(key=SESSION_COOKIE_NAME, value=rag_session_id, httponly=True)
    ####################
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )

# 앱 상태 확인 엔드포인트
@app.get("/health", response_model=ApiResponse)
async def health_check():
    """API 서버 상태 확인"""
    return ApiResponse(
        success=True,
        data={
            "status": "healthy",
            "timestamp": datetime.now().isoformat()
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )