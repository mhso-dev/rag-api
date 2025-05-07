from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import JSONResponse
from app.models.request import DeleteDocumentRequest, DocumentUploadRequest
from app.models.response import DocumentInfo, ApiResponse
from app.services.document_service import DocumentService
from app.exceptions import DocumentProcessingError, InvalidFileFormatError
import shutil
import os
import tempfile
import json
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])

# DocumentService 의존성
def get_document_service():
    return DocumentService()

@router.post("/upload", response_model=ApiResponse[DocumentInfo])
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    metadata: Optional[str] = Form(None),
    document_service: DocumentService = Depends(get_document_service)
):
    """
    문서를 업로드하고 RAG 시스템의 Vector Store에 추가합니다.
    
    - **file**: 업로드할 문서 파일 (PDF, TXT, CSV, HTML 형식 지원)
    - **description**: (선택 사항) 문서 설명
    - **metadata**: (선택 사항) 문서 메타데이터 (JSON 문자열)
    """
    # 메타데이터 파싱
    doc_metadata = {}
    if metadata:
        try:
            doc_metadata = json.loads(metadata)
        except json.JSONDecodeError:
            return ApiResponse(
                success=False,
                error={"message": "잘못된 메타데이터 형식입니다. 유효한 JSON 문자열이어야 합니다."}
            )
    
    try:
        # 임시 파일 생성
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
            # 업로드된 파일 내용 읽기
            contents = await file.read()
            # 임시 파일에 쓰기
            temp_file.write(contents)
            temp_file_path = temp_file.name
        
        # 백그라운드에서 문서 처리 (비동기)
        result = await document_service.process_document(
            file_path=temp_file_path,
            original_filename=file.filename,
            description=description,
            metadata=doc_metadata
        )
        
        # 임시 파일 삭제
        try:
            os.unlink(temp_file_path)
        except Exception as e:
            logger.warning(f"임시 파일 삭제 중 오류: {e}")
        
        return ApiResponse(
            success=True,
            data=result,
            meta={"filename": file.filename}
        )
        
    except InvalidFileFormatError as e:
        return ApiResponse(
            success=False,
            error={
                "type": "InvalidFileFormatError",
                "message": str(e),
                "status_code": 400
            }
        )
        
    except DocumentProcessingError as e:
        return ApiResponse(
            success=False,
            error={
                "type": "DocumentProcessingError",
                "message": str(e),
                "status_code": 500
            }
        )
        
    except Exception as e:
        logger.error(f"문서 업로드 중 오류: {e}")
        return ApiResponse(
            success=False,
            error={
                "type": "InternalServerError",
                "message": f"문서 업로드 중 오류 발생: {str(e)}",
                "status_code": 500
            }
        )

@router.get("/", response_model=ApiResponse[List[DocumentInfo]])
async def get_documents(
    document_service: DocumentService = Depends(get_document_service)
):
    """
    시스템에 등록된 모든 문서 목록을 조회합니다.
    """
    try:
        documents = await document_service.get_all_documents()
        
        return ApiResponse(
            success=True,
            data=documents,
            meta={"total": len(documents)}
        )
        
    except Exception as e:
        logger.error(f"문서 목록 조회 중 오류: {e}")
        return ApiResponse(
            success=False,
            error={
                "type": "InternalServerError",
                "message": f"문서 목록 조회 중 오류 발생: {str(e)}",
                "status_code": 500
            }
        )

@router.delete("/", response_model=ApiResponse)
async def delete_document(
    request: DeleteDocumentRequest,
    document_service: DocumentService = Depends(get_document_service)
):
    """
    문서를 삭제합니다.
    
    - **document_id**: 삭제할 문서 ID
    """
    try:
        success = await document_service.delete_document(request.document_id)
        
        if success:
            return ApiResponse(
                success=True,
                meta={"document_id": request.document_id, "message": "문서가 성공적으로 삭제되었습니다."}
            )
        else:
            return ApiResponse(
                success=False,
                error={
                    "type": "DocumentNotFoundError",
                    "message": f"문서 ID {request.document_id}를 찾을 수 없습니다.",
                    "status_code": 404
                }
            )
            
    except Exception as e:
        logger.error(f"문서 삭제 중 오류: {e}")
        return ApiResponse(
            success=False,
            error={
                "type": "InternalServerError",
                "message": f"문서 삭제 중 오류 발생: {str(e)}",
                "status_code": 500
            }
        )