from pydantic_settings import BaseSettings
from pydantic import field_validator
import os
from typing import Optional
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

class Settings(BaseSettings):
    """애플리케이션 설정 클래스"""
    
    # 앱 기본 설정
    APP_NAME: str = "RAG API"
    APP_DESCRIPTION: str = "FastAPI와 LangChain을 활용한 RAG 시스템 API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # 로깅 설정
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # API 키
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # 서버 설정
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # 모델 설정
    EMBEDDING_MODEL_NAME: str = os.getenv("EMBEDDING_MODEL_NAME", "text-embedding-3-small")
    LLM_MODEL_NAME: str = os.getenv("LLM_MODEL_NAME", "gpt-4o")
    
    # Vector Store 설정
    VECTOR_STORE_DIR: str = os.getenv("VECTOR_STORE_DIR", "./data/chroma_db")
    
    # 검색 설정
    RETRIEVER_K: int = int(os.getenv("RETRIEVER_K", "3"))
    
    # 유효성 검사 메서드들
    @field_validator("OPENAI_API_KEY")
    def validate_openai_api_key(cls, v):
        if not v:
            raise ValueError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다!")
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

# 전역 설정 객체 생성
settings = Settings()