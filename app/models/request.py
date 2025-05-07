from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any

class ChatRequest(BaseModel):
    """채팅 요청 모델"""
    query: str = Field(..., description="사용자 질문", min_length=1)
    history: Optional[List[Dict[str, str]]] = Field(
        default=None, 
        description="대화 내역 (선택 사항)"
    )
    
class DocumentUploadRequest(BaseModel):
    """문서 업로드 요청 메타데이터 모델"""
    description: Optional[str] = Field(
        default=None, 
        description="문서에 대한 설명"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, 
        description="추가 메타데이터"
    )
    
class DeleteDocumentRequest(BaseModel):
    """문서 삭제 요청 모델"""
    document_id: str = Field(..., description="삭제할 문서 ID")