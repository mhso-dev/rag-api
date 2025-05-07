from langchain.chains import RetrievalQA, ConversationalRetrievalChain
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from app.exceptions import RAGProcessingError, DocumentNotFoundError, LLMServiceError, RateLimitError
import asyncio
import time
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class RAGService:
    """RAG 관련 기능을 제공하는 서비스 클래스"""
    
    def __init__(self, embeddings, llm, retriever, retriever_k=3, verbose=False):
        self.embeddings = embeddings
        self.llm = llm
        self.retriever = retriever
        self.retriever_k = retriever_k
        self.verbose = verbose  # 디버그 출력 여부
        
        # 기본 QA Chain 생성
        self.qa_chain = self._create_qa_chain()
        
        # 대화 Chain 생성
        self.conversation_chain = self._create_conversation_chain()
        
        logger.info("RAG 서비스가 성공적으로 초기화되었습니다.")
    
    def _create_qa_chain(self):
        """기본 QA Chain 생성"""
        # QA 프롬프트 템플릿
        template = """다음 문맥을 사용하여 질문에 답변하세요.
        
        만약 문맥에서 답을 찾을 수 없다면, '제공된 문맥에서는 이 질문에 대한 정보를 찾을 수 없습니다.'라고 말하고 
        알고 있는 정보를 기반으로 최선의 답변을 제공하세요. 답변을 지어내지 마세요.
        
        중요한 점은 답변을 마크다운 형식으로 작성해야 합니다. 제목, 목록, 코드 블록, 표, 강조 등의 마크다운 문법을 적절히 활용하세요.
        
        문맥: {context}
        
        질문: {question}
        
        답변(마크다운 형식):"""
        
        PROMPT = PromptTemplate(
            template=template,
            input_variables=["context", "question"]
        )
        
        # QA Chain 생성
        qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",  # 모든 문서를 하나의 프롬프트로 결합
            retriever=self.retriever,
            return_source_documents=True,  # 소스 문서 반환
            chain_type_kwargs={"prompt": PROMPT}
        )
        
        return qa_chain
    
    def _create_conversation_chain(self):
        """대화 Chain 생성"""
        # 메모리 초기화
        memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="answer"
        )
        
        # 시스템 메시지 설정
        system_message = """당신은 문서 기반 질의응답을 제공하는 AI 어시스턴트입니다.
        질문에 대한 답변을 주어진 문서를 기반으로 생성하세요.
        답변은 반드시 마크다운 형식으로 제공하고, 제목, 목록, 코드 블록, 표, 강조 등의 마크다운 문법을 적절히 활용하세요.
        답변을 모르거나 문서에 없는 경우 솔직하게 모른다고 인정하세요."""
        
        # 대화 Chain 생성
        conversation_chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=self.retriever,
            memory=memory,
            return_source_documents=True,  # 소스 문서 반환
            verbose=self.verbose
        )
        
        return conversation_chain
    
    async def get_answer(self, query: str) -> str:
        """쿼리에 대한 답변 생성 (기본 QA Chain 사용)"""
        try:
            # 비동기 래퍼
            answer = await self.run_chain_async(query)
            return answer
        except Exception as e:
            logger.error(f"답변 생성 중 오류 발생: {e}")
            self._handle_llm_error(e)
    
    async def get_answer_with_sources(self, query: str) -> Dict[str, Any]:
        """쿼리에 대한 답변과 소스 문서 정보를 반환"""
        start_time = time.time()
        
        try:
            # 1. 관련 문서 검색
            docs = await asyncio.to_thread(self.retriever.get_relevant_documents, query)
            
            # 검색된 문서가 없는 경우
            if not docs:
                raise DocumentNotFoundError("질문과 관련된 문서를 찾을 수 없습니다")
            
            # 2. LLM으로 답변 생성
            try:
                chain_result = await asyncio.to_thread(self.qa_chain, {"query": query})
            except Exception as llm_error:
                self._handle_llm_error(llm_error)
            
            # 결과 추출
            if isinstance(chain_result, dict):
                if "result" in chain_result:
                    answer = chain_result["result"]
                elif "answer" in chain_result:
                    answer = chain_result["answer"]
                else:
                    answer = str(chain_result)
            else:
                answer = str(chain_result)
            
            # 3. 소스 문서 정보 처리
            sources = []
            source_documents = chain_result.get("source_documents", docs)
            
            for i, doc in enumerate(source_documents):
                source_info = {
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": getattr(doc, "score", 1.0 - (i * 0.1))  # 임의 점수 부여
                }
                sources.append(source_info)
            
            # 4. 처리 시간 계산
            processing_time = time.time() - start_time
            
            # 5. 토큰 수 계산 (가능한 경우)
            token_info = {}
            try:
                import tiktoken
                encoding = tiktoken.encoding_for_model(self.llm.model_name)
                
                context_text = "\n\n".join([doc.page_content for doc in source_documents])
                prompt_text = context_text + query
                answer_text = answer
                
                prompt_tokens = len(encoding.encode(prompt_text))
                completion_tokens = len(encoding.encode(answer_text))
                
                token_info = {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens
                }
            except Exception as token_error:
                logger.warning(f"토큰 수 계산 중 오류: {token_error}")
            
            return {
                "answer": answer,
                "sources": sources,
                "processing_time": processing_time,
                **token_info
            }
        
        except (DocumentNotFoundError, LLMServiceError, RateLimitError):
            # 이미 적절한 예외가 발생한 경우 다시 발생
            raise
        except Exception as e:
            # 기타 모든 예외는 RAGProcessingError로 래핑
            logger.error(f"RAG 처리 중 예상치 못한 오류: {e}")
            raise RAGProcessingError(f"RAG 처리 중 예상치 못한 오류: {str(e)}")
    
    async def get_conversation_response(self, query: str, chat_history=None) -> Dict[str, Any]:
        """대화 내역을 고려한 답변 생성"""
        start_time = time.time()
        
        if chat_history is None:
            chat_history = []
        
        try:
            # 대화 내역 변환
            formatted_history = []
            for entry in chat_history:
                if isinstance(entry, dict) and "human" in entry and "ai" in entry:
                    formatted_history.append((entry["human"], entry["ai"]))
            
            # 비동기적으로 대화 Chain 실행
            result = await asyncio.to_thread(
                self.conversation_chain,
                {"question": query, "chat_history": formatted_history}
            )
            
            # 관련 문서 추출
            sources = []
            source_documents = result.get("source_documents", [])
            
            for i, doc in enumerate(source_documents):
                source_info = {
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": getattr(doc, "score", 1.0 - (i * 0.1))  # 임의 점수 부여
                }
                sources.append(source_info)
            
            # 처리 시간 계산
            processing_time = time.time() - start_time
            
            return {
                "answer": result["answer"],
                "sources": sources,
                "processing_time": processing_time
            }
        
        except Exception as e:
            logger.error(f"대화 응답 생성 중 오류 발생: {e}")
            self._handle_llm_error(e)
            raise RAGProcessingError(f"대화 응답 생성 중 오류: {str(e)}")
    
    async def run_chain_async(self, query: str) -> str:
        """QA Chain 비동기 실행 래퍼"""
        try:
            # 비동기적으로 Chain 실행
            result = await asyncio.to_thread(self.qa_chain.run, query)
            return result
        except Exception as e:
            self._handle_llm_error(e)
    
    def _handle_llm_error(self, error: Exception):
        """LLM 오류 처리"""
        error_str = str(error).lower()
        
        if "rate limit" in error_str or "quota" in error_str:
            raise RateLimitError("OpenAI API 호출 제한에 도달했습니다")
        elif "invalid api key" in error_str or "authentication" in error_str:
            raise LLMServiceError("OpenAI API 키가 유효하지 않습니다")
        else:
            raise LLMServiceError(f"LLM 처리 중 오류: {str(error)}")