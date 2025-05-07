from functools import lru_cache
from langchain_openai import OpenAIEmbeddings
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

@lru_cache(maxsize=1)
def get_embeddings_service():
    """OpenAI 임베딩 서비스 인스턴스 제공 (싱글톤)"""
    logger.info(f"임베딩 모델 '{settings.EMBEDDING_MODEL_NAME}'을(를) 로드하는 중...")
    
    # OpenAI 임베딩 모델 초기화
    embeddings = OpenAIEmbeddings(
        model=settings.EMBEDDING_MODEL_NAME,
        openai_api_key=settings.OPENAI_API_KEY,
        dimensions=1536,  # text-embedding-3-small 모델의 기본 차원 크기
    )
    
    logger.info("임베딩 모델 로드 완료!")
    return embeddings