from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader, PyPDFLoader, CSVLoader, UnstructuredHTMLLoader
from langchain_community.vectorstores import Chroma
from app.services.embeddings import get_embeddings_service
from app.core.config import settings
from app.exceptions import DocumentProcessingError, InvalidFileFormatError
import os
import uuid
import shutil
from datetime import datetime
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class DocumentService:
    """문서 관리 서비스 클래스"""
    
    def __init__(self, embeddings=None):
        self.embeddings = embeddings or get_embeddings_service()
        self.vector_store_dir = settings.VECTOR_STORE_DIR
        
        # 벡터 스토어 디렉토리 생성
        os.makedirs(self.vector_store_dir, exist_ok=True)
        
        # 문서 저장 디렉토리 생성
        self.documents_dir = os.path.join("data", "documents")
        os.makedirs(self.documents_dir, exist_ok=True)
    
    def load_document(self, file_path: str) -> List[Any]:
        """다양한 형식의 문서를 로드하는 함수"""
        logger.info(f"문서 로드 중: {file_path}")
        
        if file_path.endswith('.pdf'):
            loader = PyPDFLoader(file_path)
            return loader.load()
            
        elif file_path.endswith('.txt'):
            loader = TextLoader(file_path)
            return loader.load()
            
        elif file_path.endswith('.csv'):
            loader = CSVLoader(file_path)
            return loader.load()
            
        elif file_path.endswith('.html'):
            loader = UnstructuredHTMLLoader(file_path)
            return loader.load()
            
        else:
            supported_formats = ['.pdf', '.txt', '.csv', '.html']
            raise InvalidFileFormatError(
                f"지원하지 않는 파일 형식입니다. 지원되는 형식: {', '.join(supported_formats)}"
            )
    
    def split_documents(self, documents: List[Any], chunk_size: int = 1000, chunk_overlap: int = 200) -> List[Any]:
        """문서를 청크로 분할하는 함수"""
        logger.info(f"문서를 청크로 분할 중 (chunk_size={chunk_size}, chunk_overlap={chunk_overlap})")
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        chunks = text_splitter.split_documents(documents)
        logger.info(f"총 {len(documents)}개의 문서가 {len(chunks)}개의 청크로 분할되었습니다.")
        return chunks
    
    async def process_document(self, file_path: str, original_filename: str, description: Optional[str] = None, 
                              metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """문서 처리 및 벡터 스토어에 추가"""
        try:
            # 문서 ID 생성
            document_id = str(uuid.uuid4())
            
            # 문서 저장 경로 생성
            document_dir = os.path.join(self.documents_dir, document_id)
            os.makedirs(document_dir, exist_ok=True)
            
            # 파일 복사
            target_file_path = os.path.join(document_dir, original_filename)
            shutil.copy2(file_path, target_file_path)
            
            # 문서 로드
            documents = self.load_document(target_file_path)
            
            # 문서에 메타데이터 추가
            doc_metadata = metadata or {}
            doc_metadata.update({
                "document_id": document_id,
                "filename": original_filename,
                "description": description,
                "source": target_file_path,
                "created_at": datetime.now().isoformat()
            })
            
            for doc in documents:
                doc.metadata.update(doc_metadata)
            
            # 문서 분할
            chunks = self.split_documents(documents)
            
            # Vector Store 생성/로드
            vector_store = Chroma(
                persist_directory=self.vector_store_dir,
                embedding_function=self.embeddings
            )
            
            # 청크 추가
            vector_store.add_documents(chunks)
            vector_store.persist()
            
            # 응답 생성
            return {
                "document_id": document_id,
                "filename": original_filename,
                "description": description,
                "metadata": doc_metadata,
                "created_at": datetime.now(),
                "chunks_count": len(chunks)
            }
            
        except Exception as e:
            # 오류 발생 시 생성된 디렉토리 정리
            try:
                if 'document_dir' in locals() and os.path.exists(document_dir):
                    shutil.rmtree(document_dir)
            except Exception as cleanup_error:
                logger.error(f"문서 디렉토리 정리 중 오류: {cleanup_error}")
            
            # 적절한 예외 발생
            if isinstance(e, InvalidFileFormatError):
                raise
            else:
                logger.error(f"문서 처리 중 오류: {e}")
                raise DocumentProcessingError(f"문서 처리 중 오류 발생: {str(e)}")
    
    async def get_all_documents(self) -> List[Dict[str, Any]]:
        """모든 문서 목록 조회"""
        documents = []
        
        try:
            # 문서 디렉토리 순회
            for doc_id in os.listdir(self.documents_dir):
                doc_path = os.path.join(self.documents_dir, doc_id)
                
                # 디렉토리인 경우만 처리
                if os.path.isdir(doc_path):
                    try:
                        # 디렉토리 내 첫 번째 파일 정보 추출
                        files = os.listdir(doc_path)
                        if files:
                            filename = files[0]
                            file_path = os.path.join(doc_path, filename)
                            
                            # 파일 생성 시간 및 수정 시간 가져오기
                            stat = os.stat(file_path)
                            created_at = datetime.fromtimestamp(stat.st_ctime)
                            updated_at = datetime.fromtimestamp(stat.st_mtime)
                            
                            # 문서 정보 생성
                            documents.append({
                                "document_id": doc_id,
                                "filename": filename,
                                "description": None,  # 메타데이터 파일 필요
                                "metadata": {"source": file_path},
                                "created_at": created_at,
                                "updated_at": updated_at,
                                "chunks_count": 0  # 실제 계산 필요
                            })
                    except Exception as e:
                        logger.warning(f"문서 {doc_id} 정보 추출 중 오류: {e}")
        
        except Exception as e:
            logger.error(f"문서 목록 조회 중 오류: {e}")
            raise DocumentProcessingError(f"문서 목록 조회 중 오류 발생: {str(e)}")
        
        return documents
    
    async def delete_document(self, document_id: str) -> bool:
        """문서 삭제"""
        document_dir = os.path.join(self.documents_dir, document_id)
        
        # 문서 존재 여부 확인
        if not os.path.exists(document_dir):
            logger.warning(f"삭제할 문서를 찾을 수 없음: {document_id}")
            return False
        
        try:
            # 문서 디렉토리 삭제
            shutil.rmtree(document_dir)
            logger.info(f"문서 삭제 완료: {document_id}")
            
            # Vector Store 재생성 (삭제된 문서 반영)
            # 실제 구현에서는 더 효율적인 방법 고려 필요
            # ex: Chroma의 delete_collection 사용
            
            return True
            
        except Exception as e:
            logger.error(f"문서 삭제 중 오류: {e}")
            raise DocumentProcessingError(f"문서 삭제 중 오류 발생: {str(e)}")