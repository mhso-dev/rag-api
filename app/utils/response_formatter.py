from app.models.response import ChatResponse, SourceDocument, Citation
from app.utils.answer_enhancer import enhance_answer
from app.utils.quality_evaluator import evaluate_answer_quality
from typing import Dict, List, Any
import re
import os
import logging

logger = logging.getLogger(__name__)

def format_rag_response(
    rag_result: Dict[str, Any], 
    enhance: bool = True, 
    evaluate_quality: bool = False
) -> Dict[str, Any]:
    """RAG 서비스 결과를 응답 모델에 맞게 변환"""
    # 기본 필드 추출
    answer = rag_result.get("answer", "")
    sources = rag_result.get("sources", [])
    processing_time = rag_result.get("processing_time", 0.0)
    
    # 토큰 정보 추출 (있는 경우)
    prompt_tokens = rag_result.get("prompt_tokens")
    completion_tokens = rag_result.get("completion_tokens")
    
    # 소스 문서 포맷팅
    formatted_sources = format_sources_for_display(sources)
    
    # 답변 텍스트 강화 (선택 사항)
    if enhance:
        answer = enhance_answer(answer, sources)
    
    # 인용 정보 추출
    citations = extract_citations(answer, formatted_sources)
    
    # 응답 데이터 준비
    response_data = {
        "answer": answer,
        "sources": formatted_sources,
        "processing_time": processing_time,
        "citations": citations
    }
    
    # 토큰 정보 추가 (있는 경우)
    if prompt_tokens is not None:
        response_data["prompt_tokens"] = prompt_tokens
    if completion_tokens is not None:
        response_data["completion_tokens"] = completion_tokens
    
    # 품질 평가 (선택 사항)
    if evaluate_quality:
        quality_metrics = evaluate_answer_quality(answer, sources)
        response_data["quality_metrics"] = quality_metrics
    
    return response_data

def extract_citations(answer: str, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """답변 텍스트에서 인용 정보 추출"""
    citations = []
    
    # 인용 패턴: [1], [2], 등
    citation_pattern = r'\[(\d+)\]'
    matches = re.findall(citation_pattern, answer)
    
    for match in matches:
        try:
            index = int(match) - 1
            if 0 <= index < len(sources):
                source = sources[index]
                
                # 인용 정보 생성
                citation = {
                    "text": source.get("snippet", source.get("context", "")),
                    "document_id": source.get("metadata", {}).get("document_id", f"doc_{index}"),
                    "document_name": source.get("display_name", os.path.basename(
                        source.get("metadata", {}).get("source", f"document_{index}")
                    )),
                    "page": source.get("metadata", {}).get("page")
                }
                
                citations.append(citation)
        except (ValueError, IndexError) as e:
            logger.warning(f"인용 정보 추출 중 오류: {e}")
    
    return citations

def format_sources_for_display(sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """소스 정보를 사용자 친화적으로 포맷팅"""
    formatted_sources = []
    
    for i, source in enumerate(sources):
        content = source.get("content", "")
        metadata = source.get("metadata", {})
        score = source.get("score", 0.0)
        
        # 텍스트 컨텍스트 추출
        context = content
        if len(context) > 300:
            context = context[:297] + "..."
        
        # 메타데이터 가공
        display_metadata = {}
        
        # 파일 정보
        if "source" in metadata:
            filename = os.path.basename(metadata["source"])
            display_metadata["파일명"] = filename
        
        # 문서 ID
        if "document_id" in metadata:
            display_metadata["문서 ID"] = metadata["document_id"]
        
        # 페이지 정보
        if "page" in metadata:
            display_metadata["페이지"] = metadata["page"]
        
        # 날짜 정보
        if "created_at" in metadata:
            from datetime import datetime
            try:
                if isinstance(metadata["created_at"], str):
                    dt = datetime.fromisoformat(metadata["created_at"].replace("Z", "+00:00"))
                    display_metadata["작성일"] = dt.strftime("%Y년 %m월 %d일")
                else:
                    display_metadata["작성일"] = metadata["created_at"]
            except (ValueError, TypeError) as e:
                # 날짜 형식이 맞지 않으면 원본 그대로 사용
                display_metadata["작성일"] = str(metadata["created_at"])
        
        # 저자 정보
        if "author" in metadata:
            display_metadata["저자"] = metadata["author"]
        
        # 유사도 점수 포맷팅 (0.0-1.0 범위의 백분율로 변환)
        display_metadata["관련도"] = f"{score * 100:.1f}%"
        
        # 결과 추가
        formatted_source = {
            "reference_id": i + 1,  # 1부터 시작하는 인용 ID
            "content": content,  # 원본 내용 (API 응답용)
            "context": context,  # 사용자 표시용 요약 내용
            "metadata": metadata,  # 원본 메타데이터 (API 응답용)
            "display_metadata": display_metadata,  # 사용자 표시용 메타데이터
            "score": score,  # 원본 점수
            "snippet": context[:100] + ("..." if len(context) > 100 else ""),  # 미리보기
            "display_name": display_metadata.get("파일명", f"문서 {i+1}")  # 표시용 이름
        }
        
        formatted_sources.append(formatted_source)
    
    # 점수 기준으로 정렬 (높은 점수가 먼저 오도록)
    formatted_sources.sort(key=lambda x: x["score"], reverse=True)
    
    return formatted_sources