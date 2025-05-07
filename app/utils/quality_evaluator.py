from typing import Dict, List, Any
import re
import logging

logger = logging.getLogger(__name__)

def evaluate_answer_quality(answer: str, sources: List[Dict[str, Any]]) -> Dict[str, Any]:
    """RAG 응답의 품질과 신뢰도 평가"""
    # 1. 기본 메트릭 계산
    metrics = {}
    
    # 답변 길이
    answer_length = len(answer)
    metrics["answer_length"] = answer_length
    
    # 소스 수
    num_sources = len(sources)
    metrics["num_sources"] = num_sources
    
    # 인용 수
    citation_count = len(re.findall(r'\[\d+\]', answer))
    metrics["citation_count"] = citation_count
    
    # 2. 신뢰도 점수 계산
    reliability_score = calculate_reliability_score(answer, sources, citation_count)
    metrics["reliability_score"] = reliability_score
    
    # 3. 신뢰도 등급 할당
    metrics["reliability_grade"] = get_reliability_grade(reliability_score)
    
    # 4. 품질 플래그
    quality_flags = get_quality_flags(answer, sources, citation_count)
    metrics["quality_flags"] = quality_flags
    
    return metrics

def calculate_reliability_score(answer: str, sources: List[Dict[str, Any]], citation_count: int) -> float:
    """신뢰도 점수 계산 (0.0-1.0 범위)"""
    # 기본 점수
    score = 0.5
    
    # 1. 소스 기반 점수
    if sources:
        source_score = min(len(sources) / 5, 1.0) * 0.3
        score += source_score
    
    # 2. 인용 기반 점수
    if citation_count > 0:
        citation_ratio = min(citation_count / 3, 1.0)
        score += citation_ratio * 0.2
    
    # 3. 텍스트 품질 기반 점수
    text_quality = 0.0
    
    # 불확실성 표현이 있으면 점수 감소
    uncertainty_phrases = ["알 수 없습니다", "확실하지 않습니다", "모릅니다", "불확실합니다"]
    for phrase in uncertainty_phrases:
        if phrase in answer:
            text_quality -= 0.1
    
    # 구체적인 데이터나 숫자가 있으면 점수 증가
    if re.search(r'\d+(\.\d+)?', answer):
        text_quality += 0.1
    
    # 답변 길이가 적절하면 점수 증가
    if 100 < len(answer) < 1000:
        text_quality += 0.1
    
    score += min(max(text_quality, -0.2), 0.2)
    
    # 최종 점수 범위 제한
    return max(0.0, min(score, 1.0))

def get_reliability_grade(score: float) -> str:
    """신뢰도 점수에 따른 등급 할당"""
    if score >= 0.9:
        return "매우 높음"
    elif score >= 0.7:
        return "높음"
    elif score >= 0.5:
        return "중간"
    elif score >= 0.3:
        return "낮음"
    else:
        return "매우 낮음"

def get_quality_flags(answer: str, sources: List[Dict[str, Any]], citation_count: int) -> List[str]:
    """응답 품질 관련 플래그 생성"""
    flags = []
    
    # 소스 부족
    if not sources:
        flags.append("소스_없음")
    elif len(sources) < 2:
        flags.append("소스_부족")
    
    # 인용 부족
    if citation_count == 0:
        flags.append("인용_없음")
    
    # 불확실성 감지
    uncertainty_phrases = ["알 수 없습니다", "확실하지 않습니다", "모릅니다", "불확실합니다"]
    for phrase in uncertainty_phrases:
        if phrase in answer:
            flags.append("불확실성_감지")
            break
    
    # 응답 길이 문제
    if len(answer) < 50:
        flags.append("응답_짧음")
    elif len(answer) > 1500:
        flags.append("응답_김")
    
    return flags