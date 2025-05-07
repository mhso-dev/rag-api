from fastapi import APIRouter, Depends, HTTPException, Query, Request, Cookie
from app.models.request import ChatRequest
from app.models.response import ChatResponse, ApiResponse
from app.services.rag import RAGService
from app.dependencies import get_rag_service
from app.utils.response_formatter import format_rag_response
from app.exceptions import RAGServiceError, DocumentNotFoundError, LLMServiceError, RateLimitError
from app.session_memory import SESSION_MEMORY, SESSION_COOKIE_NAME
import logging
from typing import Optional

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/", response_model=ApiResponse[ChatResponse])
async def chat(
    request: ChatRequest,
    rag_service: RAGService = Depends(get_rag_service),
    evaluate_quality: bool = Query(False, description="답변 품질 평가 활성화")
):
    """
    RAG 시스템을 사용하여 쿼리에 대한 답변을 생성합니다.
    
    - **query**: 사용자 질문
    - **history**: (선택 사항) 이전 대화 내역
    - **evaluate_quality**: (선택 사항) 답변 품질 평가 활성화
    """
    try:
        logger.info(f"채팅 요청 처리 중: {request.query}")
        
        # RAG 서비스에서 응답 생성
        rag_result = await rag_service.get_answer_with_sources(request.query)
        
        # 응답 포맷팅
        response_data = format_rag_response(
            rag_result, 
            enhance=True, 
            evaluate_quality=evaluate_quality
        )
        
        # 메타데이터 준비
        meta_info = {
            "query": request.query,
            "total_sources": len(response_data["sources"])
        }
        
        logger.info(f"채팅 응답 생성 완료: 소스 {len(response_data['sources'])}개, 처리 시간 {response_data['processing_time']:.2f}초")
        
        # 성공 응답 반환
        return ApiResponse(
            success=True,
            data=response_data,
            meta=meta_info
        )
        
    except DocumentNotFoundError as e:
        logger.warning(f"문서 없음 오류: {e}")
        return ApiResponse(
            success=False,
            error={
                "type": "DocumentNotFoundError",
                "message": str(e),
                "status_code": 404
            },
            meta={"query": request.query}
        )
        
    except (LLMServiceError, RateLimitError) as e:
        logger.error(f"LLM 서비스 오류: {e}")
        return ApiResponse(
            success=False,
            error={
                "type": type(e).__name__,
                "message": str(e),
                "status_code": e.status_code
            },
            meta={"query": request.query}
        )
        
    except RAGServiceError as e:
        logger.error(f"RAG 서비스 오류: {e}")
        return ApiResponse(
            success=False,
            error={
                "type": "RAGServiceError",
                "message": str(e),
                "status_code": e.status_code
            },
            meta={"query": request.query}
        )
        
    except Exception as e:
        logger.error(f"예상치 못한 오류: {e}")
        return ApiResponse(
            success=False,
            error={
                "type": "InternalServerError",
                "message": "서버 내부 오류가 발생했습니다",
                "status_code": 500
            },
            meta={"query": request.query}
        )

@router.post("/conversation", response_model=ApiResponse[ChatResponse])
async def conversation(
    request: ChatRequest,
    rag_service: RAGService = Depends(get_rag_service),
    evaluate_quality: bool = Query(False, description="답변 품질 평가 활성화"),
    fastapi_request: Request = None,
    rag_session_id: str = Cookie(default=None)
):
    """
    대화 내역을 고려한 RAG 기반 대화 엔드포인트
    
    - **query**: 사용자 질문
    - **history**: 이전 대화 내역
    - **evaluate_quality**: (선택 사항) 답변 품질 평가 활성화
    """
    try:
        ####메모리 관련 수정#####
        # 세션별 메모리 사용
        if not rag_session_id:
            rag_session_id = fastapi_request.cookies.get(SESSION_COOKIE_NAME)
        if not rag_session_id:
            import uuid
            rag_session_id = str(uuid.uuid4())
        # 세션별 대화 내역 가져오기
        session_history = SESSION_MEMORY.get(rag_session_id, [])
        # 새 질문 추가
        if request.history:
            session_history = request.history
        ####################
        logger.info(f"대화 요청 처리 중: {request.query}, 대화 내역 길이: {len(session_history)}")
        
        # RAG 서비스에서 대화 응답 생성
        rag_result = await rag_service.get_conversation_response(
            query=request.query,
            chat_history=session_history
        )
        
        # 응답 포맷팅
        response_data = format_rag_response(
            rag_result, 
            enhance=True, 
            evaluate_quality=evaluate_quality
        )
        
        # 메타데이터 준비
        meta_info = {
            "query": request.query,
            "total_sources": len(response_data["sources"]),
            "history_length": len(session_history)
        }
        
        # 세션별 메모리 갱신
        ####메모리 관련 수정#####
        session_history.append({"human": request.query, "ai": rag_result["answer"]})
        SESSION_MEMORY[rag_session_id] = session_history
        ####################
        logger.info(f"대화 응답 생성 완료: 소스 {len(response_data['sources'])}개, 처리 시간 {response_data['processing_time']:.2f}초")
        
        # 성공 응답 반환
        return ApiResponse(
            success=True,
            data=response_data,
            meta=meta_info
        )
        
    except Exception as e:
        # 예외 처리 (이전 엔드포인트와 유사)
        logger.error(f"대화 처리 중 오류: {e}")
        return ApiResponse(
            success=False,
            error={
                "type": type(e).__name__,
                "message": str(e),
                "status_code": getattr(e, "status_code", 500)
            },
            meta={"query": request.query}
        )