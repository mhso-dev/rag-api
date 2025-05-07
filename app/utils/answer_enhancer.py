import re
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

def enhance_answer(answer: str, sources: List[Dict[str, Any]]) -> str:
    """답변 텍스트를 강화하여 더 유용하게 만듦"""
    # 1. 인용 표시 추가
    enhanced_answer = add_citations(answer, sources)
    
    # 2. 마크다운 형식 적용
    enhanced_answer = apply_markdown(enhanced_answer)
    
    # 3. 주요 개념 강조
    enhanced_answer = highlight_key_concepts(enhanced_answer)
    
    return enhanced_answer

def add_citations(answer: str, sources: List[Dict[str, Any]]) -> str:
    """답변에 인용 표시 추가"""
    # 이미 인용이 있는 경우 그대로 반환
    if re.search(r'\[\d+\]', answer):
        return answer
    
    # 간단한 인용 추가 로직
    enhanced_answer = answer
    
    for i, source in enumerate(sources):
        content = source.get("content", "")
        # 소스 내용이 답변에 포함되어 있는지 확인
        sentences = content.split('. ')
        
        for sentence in sentences:
            if len(sentence) > 20 and sentence in answer:
                # 인용 추가
                citation = f" [{i+1}]"
                if sentence + citation not in enhanced_answer:
                    enhanced_answer = enhanced_answer.replace(
                        sentence,
                        sentence + citation
                    )
    
    # 인용 참조 섹션 추가
    if re.search(r'\[\d+\]', enhanced_answer):
        enhanced_answer += "\n\n**참고 문헌:**\n"
        for i, source in enumerate(sources):
            metadata = source.get("metadata", {})
            filename = metadata.get("filename", os.path.basename(metadata.get("source", f"문서 {i+1}")))
            page = metadata.get("page", "")
            page_info = f"p.{page}" if page else ""
            
            enhanced_answer += f"[{i+1}] {filename} {page_info}\n"
    
    return enhanced_answer

def apply_markdown(text: str) -> str:
    """텍스트에 마크다운 형식 적용"""
    # 제목 포맷팅
    lines = text.split('\n')
    formatted_lines = []
    
    for line in lines:
        # 제목 형식 감지 및 변환
        if re.match(r'^(주요 기능|특징|장점|단점|결론|요약):', line):
            formatted_lines.append(f"\n### {line}")
        elif re.match(r'^([0-9]+\.)(.+)', line):
            # 번호 목록 항목
            formatted_lines.append(line)
        else:
            formatted_lines.append(line)
    
    text = '\n'.join(formatted_lines)
    
    # 굵은 텍스트 강조 (특정 패턴)
    important_terms = [
        "FastAPI", "Pydantic", "비동기", "async", "await", "의존성 주입",
        "자동 문서화", "타입 힌트", "성능", "속도", "OpenAPI", "JSON Schema",
        "RAG", "LLM", "GPT-4", "임베딩", "벡터", "검색", "생성", "Retrieval",
        "Vector Store", "Chroma", "Chain", "OpenAI"
    ]
    
    for term in important_terms:
        # 이미 마크다운으로 강조된 경우 제외
        pattern = r'(?<!\*\*)' + re.escape(term) + r'(?!\*\*)'
        text = re.sub(pattern, f"**{term}**", text)
    
    return text

def highlight_key_concepts(text: str) -> str:
    """주요 개념 강조"""
    # 이미 충분히 강조되어 있으면 그대로 반환
    if text.count('**') > 10:
        return text
    
    # 주요 개념을 감지하고 굵게 표시
    concepts = {
        "API": "Application Programming Interface",
        "REST": "Representational State Transfer",
        "HTTP": "Hypertext Transfer Protocol",
        "JSON": "JavaScript Object Notation",
        "ASGI": "Asynchronous Server Gateway Interface",
        "OAuth": "Open Authorization",
        "RAG": "Retrieval-Augmented Generation",
        "LLM": "Large Language Model",
        "NLP": "Natural Language Processing"
    }
    
    for concept, full_form in concepts.items():
        # 약어가 등장하면 전체 용어 추가
        if re.search(r'\b' + re.escape(concept) + r'\b', text) and full_form not in text:
            # 첫 등장 위치에 전체 용어 추가
            match = re.search(r'\b' + re.escape(concept) + r'\b', text)
            if match:
                pos = match.start()
                text = text[:pos] + f"{concept} ({full_form})" + text[pos+len(concept):]
    
    return text