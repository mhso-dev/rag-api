from functools import lru_cache
from langchain_openai import ChatOpenAI
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

@lru_cache(maxsize=1)
def get_llm_service():
    """OpenAI LLM 서비스 인스턴스 제공 (싱글톤)"""
    logger.info(f"LLM 모델 '{settings.LLM_MODEL_NAME}'을(를) 로드하는 중...")
    
    # OpenAI GPT-4o 모델 초기화
    llm = ChatOpenAI(
        model=settings.LLM_MODEL_NAME,
        openai_api_key=settings.OPENAI_API_KEY,
        temperature=0.2,  # 낮은 온도로 일관된 응답 생성
        max_tokens=1000,  # 최대 토큰 수 제한
        verbose=settings.DEBUG,  # 디버그 모드에서 상세 로그 활성화
    )
    
    logger.info("LLM 모델 로드 완료!")
    return llm