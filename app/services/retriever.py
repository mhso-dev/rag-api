from functools import lru_cache
from langchain_community.vectorstores import Chroma
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import EmbeddingsFilter
from app.core.config import settings
from app.services.embeddings import get_embeddings_service
import os
import logging

logger = logging.getLogger(__name__)

@lru_cache(maxsize=1)
def get_retriever_service():
    """Vector Store Retriever 서비스 인스턴스 제공 (싱글톤)"""
    logger.info("Vector Store와 Retriever를 초기화하는 중...")
    
    # 임베딩 모델 가져오기
    embeddings = get_embeddings_service()
    
    vector_store_dir = settings.VECTOR_STORE_DIR
    
    # 벡터 스토어 디렉토리가 없으면 생성
    os.makedirs(vector_store_dir, exist_ok=True)
    
    # Chroma 벡터 스토어 초기화 또는 로드
    try:
        # 기존 벡터 스토어 로드 시도
        vector_store = Chroma(
            persist_directory=vector_store_dir,
            embedding_function=embeddings
        )
        logger.info(f"기존 Vector Store를 '{vector_store_dir}'에서 로드했습니다.")
    except Exception as e:
        # 로드 실패 시 새로 생성
        logger.warning(f"Vector Store 로드 실패: {e}. 새로 생성합니다.")
        vector_store = Chroma(
            persist_directory=vector_store_dir,
            embedding_function=embeddings
        )
        vector_store.persist()
        logger.info(f"새 Vector Store를 '{vector_store_dir}'에 생성했습니다.")
    
    # 기본 검색기 생성
    base_retriever = vector_store.as_retriever(
        search_type="similarity",  # 유사도 기반 검색
        search_kwargs={"k": settings.RETRIEVER_K}  # 상위 k개 결과 반환
    )
    
    # 참고: 컨텍스트 압축 검색기가 필요한 경우 아래 주석을 해제하세요
    # 현재는 압축 검색기 없이 기본 검색기만 사용합니다
    """
    # 임베딩 필터를 사용한 컨텍스트 압축 검색기 생성
    # 이 부분에서 오류가 발생하고 있습니다
    embeddings_filter = EmbeddingsFilter(
        embeddings=embeddings,
        similarity_threshold=0.7  # 유사도 임계값 (0.0 ~ 1.0)
    )
    
    retriever = ContextualCompressionRetriever(
        base_compressor=embeddings_filter,
        base_retriever=base_retriever
    )
    """
    
    # 임시 해결책: 기본 검색기를 그대로 사용
    retriever = base_retriever
    
    logger.info("Retriever 초기화 완료!")
    return retriever