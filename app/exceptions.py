class RAGServiceError(Exception):
    """RAG 서비스 관련 기본 예외"""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class DocumentNotFoundError(RAGServiceError):
    """문서를 찾을 수 없을 때 발생하는 예외"""
    def __init__(self, message: str = "요청한 문서를 찾을 수 없습니다"):
        super().__init__(message, status_code=404)


class RAGProcessingError(RAGServiceError):
    """RAG 처리 과정에서 발생하는 예외"""
    def __init__(self, message: str = "RAG 처리 중 오류가 발생했습니다"):
        super().__init__(message, status_code=500)


class LLMServiceError(RAGServiceError):
    """LLM 서비스 관련 예외"""
    def __init__(self, message: str = "LLM 서비스 호출 중 오류가 발생했습니다"):
        super().__init__(message, status_code=503)


class RateLimitError(RAGServiceError):
    """API 호출 제한에 도달했을 때 발생하는 예외"""
    def __init__(self, message: str = "API 호출 제한에 도달했습니다"):
        super().__init__(message, status_code=429)


class DocumentProcessingError(RAGServiceError):
    """문서 처리 중 발생하는 예외"""
    def __init__(self, message: str = "문서 처리 중 오류가 발생했습니다"):
        super().__init__(message, status_code=500)


class InvalidFileFormatError(RAGServiceError):
    """잘못된 파일 형식에 대한 예외"""
    def __init__(self, message: str = "지원하지 않는 파일 형식입니다"):
        super().__init__(message, status_code=400)
