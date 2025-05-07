from fastapi import Depends
from functools import lru_cache
from app.core.config import settings
from app.services.embeddings import get_embeddings_service
from app.services.llm import get_llm_service
from app.services.retriever import get_retriever_service
from app.services.rag import RAGService
import logging

logger = logging.getLogger(__name__)

@lru_cache(maxsize=1)
def get_settings():
    """애플리케이션 설정 제공 (싱글톤)"""
    logger.info("애플리케이션 설정을 불러오는 중...")
    return settings

@lru_cache(maxsize=1)
def get_rag_service():
    """RAG 서비스 인스턴스 제공 (싱글톤)"""
    logger.info("RAG 서비스를 초기화하는 중...")
    
    # 각 서비스 컴포넌트 가져오기
    embeddings = get_embeddings_service()
    llm = get_llm_service()
    retriever = get_retriever_service()
    
    # RAG 서비스 인스턴스 생성
    rag_service = RAGService(
        embeddings=embeddings,
        llm=llm,
        retriever=retriever,
        retriever_k=settings.RETRIEVER_K  # 직접 settings에서 값을 가져옴
    )
    
    return rag_service