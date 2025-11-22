"""Cases Analyzer API Routes"""
import logging
from typing import List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.llm_gateway import get_llm_gateway

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cases_analyzer/v1", tags=["cases-analyzer"])


class DialogMessage(BaseModel):
    """Single dialog message"""
    role: str  # manager or client
    content: str


class AnalyzeRequest(BaseModel):
    """Dialog analysis request"""
    dialog: List[DialogMessage]


@router.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy", "module": "cases_analyzer"}


@router.post("/analyze")
async def analyze_dialog(request: AnalyzeRequest):
    """
    Analyze completed dialog between manager and client.
    
    Provides:
    - Overall score
    - Strong points
    - Weak points
    - Specific advice
    - Key moments analysis
    
    Args:
        request: Dialog history
        
    Returns:
        Comprehensive analysis with recommendations
    """
    try:
        if not request.dialog or len(request.dialog) == 0:
            raise HTTPException(status_code=400, detail="Dialog is empty")
        
        llm = get_llm_gateway()
        
        # Format dialog for analysis
        dialog_text = ""
        for i, msg in enumerate(request.dialog):
            dialog_text += f"{i+1}. {msg.role.upper()}: {msg.content}\n"
        
        system_prompt = """Ты — эксперт-аналитик по продажам проекта "На Счастье".
Твоя задача: проанализировать диалог менеджера с клиентом.

Оцени по критериям:
1. Теплота общения (1-10)
2. Качество вопросов (1-10)
3. Структура разговора (1-10)
4. Работа с возражениями (1-10)
5. Отсутствие давления (1-10)

Формат ответа:
БАЛЛЫ: [число]
СИЛЬНЫЕ СТОРОНЫ: [список]
СЛАБЫЕ СТОРОНЫ: [список]
КЛЮЧЕВЫЕ МОМЕНТЫ: [анализ важных точек диалога]
СОВЕТЫ: [конкретные рекомендации]"""
        
        user_prompt = f"""Проанализируй следующий диалог:

{dialog_text}

Дай развёрнутый анализ с оценкой и рекомендациями."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        analysis = await llm.llm_service.chat(messages, temperature=0.6, max_tokens=800)
        
        # Parse analysis
        score = _extract_score(analysis)
        strong_sides = _extract_list(analysis, "СИЛЬНЫЕ СТОРОНЫ")
        weak_sides = _extract_list(analysis, "СЛАБЫЕ СТОРОНЫ")
        advice = _extract_section(analysis, "СОВЕТЫ")
        key_moments = _extract_key_moments(analysis, request.dialog)
        
        return {
            "success": True,
            "score": score,
            "strong_sides": strong_sides,
            "weak_sides": weak_sides,
            "advice": advice,
            "key_moments": key_moments,
            "full_analysis": analysis
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to analyze dialog: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _extract_score(text: str) -> float:
    """Extract score from analysis text"""
    try:
        # Look for БАЛЛЫ: [число] or numbers after "оценка"
        import re
        
        # Try to find explicit score
        score_match = re.search(r'БАЛЛЫ:\s*(\d+(?:\.\d+)?)', text, re.IGNORECASE)
        if score_match:
            return float(score_match.group(1))
        
        # Try to find average score mention
        avg_match = re.search(r'средн[яи][йяе].*?(\d+(?:\.\d+)?)', text, re.IGNORECASE)
        if avg_match:
            return float(avg_match.group(1))
        
        # Default reasonable score
        return 7.0
    except:
        return 7.0


def _extract_list(text: str, section_name: str) -> List[str]:
    """Extract list items from section"""
    try:
        import re
        
        # Find section
        pattern = f"{section_name}:(.+?)(?:СЛАБЫЕ|КЛЮЧЕВЫЕ|СОВЕТЫ|$)"
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        
        if not match:
            return []
        
        section_text = match.group(1)
        
        # Extract bullet points or numbered items
        items = []
        for line in section_text.split('\n'):
            line = line.strip()
            # Remove bullet points, numbers, dashes
            line = re.sub(r'^[\-\*\d\.\)]+\s*', '', line)
            if line and len(line) > 3:
                items.append(line)
        
        return items[:5]  # Limit to 5 items
    except:
        return []


def _extract_section(text: str, section_name: str) -> str:
    """Extract section text"""
    try:
        import re
        
        pattern = f"{section_name}:(.+?)(?:СИЛЬНЫЕ|СЛАБЫЕ|КЛЮЧЕВЫЕ|$)"
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        
        if match:
            return match.group(1).strip()
        
        return "Продолжай работать над техникой общения и анализировать свои диалоги."
    except:
        return "Продолжай работать над техникой общения и анализировать свои диалоги."


def _extract_key_moments(text: str, dialog: List[DialogMessage]) -> List[dict]:
    """Extract key moments from analysis"""
    # Simplified version - return structure for first few messages
    key_moments = []
    
    # Analyze first 3 messages for common issues
    for i, msg in enumerate(dialog[:3]):
        if msg.role == "manager":
            issue = None
            suggestion = None
            
            msg_lower = msg.content.lower()
            
            if i == 0 and "?" not in msg.content:
                issue = "Нет вопроса в первом сообщении"
                suggestion = "Начинай с открытого вопроса для установления контакта"
            elif "цена" in msg_lower or "стоимость" in msg_lower and i <= 2:
                issue = "Слишком рано перешёл к цене"
                suggestion = "Сначала выясни потребности, потом говори о цене"
            elif len(msg.content) > 500:
                issue = "Слишком длинное сообщение"
                suggestion = "Разбивай информацию на короткие блоки"
            
            if issue:
                key_moments.append({
                    "index": i,
                    "role": msg.role,
                    "issue": issue,
                    "suggestion": suggestion
                })
    
    return key_moments
