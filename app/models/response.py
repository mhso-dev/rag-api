from pydantic import BaseModel, Field, computed_field
from typing import List, Dict, Optional, Any, Generic, TypeVar
from datetime import datetime
import os

T = TypeVar('T')

class SourceDocument(BaseModel):
    """검색된 소스 문서 정보"""
    content: str = Field(..., description="문서 내용")
    metadata: Dict[str, Any] = Field(..., description="문서 메타데이터")
    score: Optional[float] = Field(None, description="검색 유사도 점수")
    
    @computed_field
    def display_name(self) -> str:
        """표시용 문서 이름"""
        if "filename" in self.metadata:
            return self.metadata["filename"]
        elif "source" in self.metadata:
            return os.path.basename(self.metadata["source"])
        else:
            return "Unknown document"
    
    @computed_field
    def snippet(self) -> str:
        """문서 내용 미리보기 (최대 100자)"""
        if len(self.content) > 100:
            return self.content[:97] + "..."
        return self.content

class Citation(BaseModel):
    """인용 정보"""
    text: str = Field(..., description="인용된 텍스트")
    document_id: str = Field(..., description="문서 식별자")
    document_name: Optional[str] = Field(None, description="문서 이름")
    page: Optional[int] = Field(None, description="페이지 번호")

class QualityMetrics(BaseModel):
    """응답 품질 메트릭"""
    reliability_score: float = Field(..., description="신뢰도 점수 (0.0-1.0)")
    reliability_grade: str = Field(..., description="신뢰도 등급")
    citation_count: int = Field(..., description="인용 수")
    answer_length: int = Field(..., description="답변 길이")
    quality_flags: List[str] = Field(default=[], description="품질 관련 플래그")

class ChatResponse(BaseModel):
    """채팅 응답 모델"""
    answer: str = Field(..., description="생성된 답변")
    sources: List[SourceDocument] = Field(..., description="검색된 소스 문서들")
    processing_time: float = Field(..., description="처리 시간(초)")
    prompt_tokens: Optional[int] = Field(None, description="프롬프트 토큰 수")
    completion_tokens: Optional[int] = Field(None, description="생성된 토큰 수")
    citations: Optional[List[Citation]] = Field(None, description="답변 내 인용 정보")
    quality_metrics: Optional[QualityMetrics] = Field(None, description="응답 품질 메트릭")
    timestamp: datetime = Field(default_factory=datetime.now, description="응답 생성 시간")

class DocumentInfo(BaseModel):
    """문서 정보 모델"""
    document_id: str = Field(..., description="문서 ID")
    filename: str = Field(..., description="파일명")
    description: Optional[str] = Field(None, description="문서 설명")
    metadata: Dict[str, Any] = Field(..., description="문서 메타데이터")
    created_at: datetime = Field(..., description="생성 시간")
    updated_at: Optional[datetime] = Field(None, description="최종 수정 시간")
    chunks_count: int = Field(..., description="청크 수")

# BaseModel이 Generic[T] 앞에 와야 함
class ApiResponse(BaseModel, Generic[T]):
    """API 표준 응답 모델"""
    success: bool = Field(..., description="요청 성공 여부")
    data: Optional[T] = Field(None, description="응답 데이터")
    error: Optional[Dict[str, Any]] = Field(None, description="오류 정보")
    meta: Optional[Dict[str, Any]] = Field(None, description="메타데이터")