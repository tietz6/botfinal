"""
Sleeping Dragon Analysis Engine
Analyzes manager's dialogue and provides warm, constructive feedback
"""
import logging
import json
import random
from typing import List, Dict, Any
from core.voice_gateway.v1.pipeline import get_pipeline

logger = logging.getLogger(__name__)


ANALYSIS_SYSTEM_PROMPT = """Ты — мудрый и опытный наставник в проекте "На Счастье".
Твоя задача — проанализировать диалог менеджера с клиентом и дать тёплую, но честную обратную связь.

Оцени диалог по следующим критериям (по шкале 0-10):
1. Тепло и эмпатия — насколько искренне и по-человечески менеджер общается
2. Открытые вопросы — задаёт ли менеджер вопросы, которые помогают клиенту открыться
3. Структура диалога — есть ли логичный переход от этапа к этапу
4. Отсутствие давления — не давит ли менеджер на клиента
5. Активное слушание — показывает ли менеджер, что слышит и понимает клиента

После оценки дай конструктивные советы в тёплом, поддерживающем тоне (2-3 предложения).
Формат ответа: JSON с полями scores (dict), total_score (int 0-10), issues (list), advice (str).
"""


async def analyze_dialogue(
    history: List[Dict[str, str]],
    manager_reply: str
) -> Dict[str, Any]:
    """
    Analyze manager's dialogue quality using DeepSeek.
    
    Args:
        history: Conversation history [{"role": "...", "content": "..."}]
        manager_reply: Latest manager's message to analyze
    
    Returns:
        Analysis result with scores, issues, and advice
    """
    try:
        pipeline = get_pipeline()
        
        # Build analysis prompt
        dialog_text = "История диалога:\n"
        for msg in history:
            role_name = "Менеджер" if msg["role"] == "assistant" else "Клиент"
            dialog_text += f"{role_name}: {msg['content']}\n"
        
        dialog_text += f"\nПоследнее сообщение менеджера:\n{manager_reply}\n"
        
        # Request analysis from LLM
        messages = [
            {"role": "system", "content": ANALYSIS_SYSTEM_PROMPT},
            {"role": "user", "content": dialog_text}
        ]
        
        response = await pipeline.chat(messages, temperature=0.5)
        
        # Try to parse JSON response
        try:
            # Try to extract JSON from response
            if "{" in response and "}" in response:
                json_start = response.index("{")
                json_end = response.rindex("}") + 1
                json_str = response[json_start:json_end]
                analysis = json.loads(json_str)
            else:
                raise ValueError("No JSON in response")
        except (json.JSONDecodeError, ValueError):
            # Fallback: use heuristic analysis
            logger.warning("Failed to parse LLM response as JSON, using heuristic analysis")
            analysis = _heuristic_analysis(history, manager_reply)
        
        # Ensure all required fields exist
        if "scores" not in analysis:
            analysis["scores"] = {}
        if "total_score" not in analysis:
            scores = analysis["scores"]
            if scores:
                analysis["total_score"] = sum(scores.values()) / len(scores)
            else:
                analysis["total_score"] = 5
        if "issues" not in analysis:
            analysis["issues"] = []
        if "advice" not in analysis:
            analysis["advice"] = "Продолжай в том же духе! Обращай внимание на эмоции клиента и задавай открытые вопросы."
        
        # Round total score
        analysis["total_score"] = round(analysis["total_score"], 1)
        
        return analysis
        
    except Exception as e:
        logger.error(f"Dialogue analysis failed: {e}")
        # Return fallback analysis
        return _heuristic_analysis(history, manager_reply)


def _heuristic_analysis(
    history: List[Dict[str, str]],
    manager_reply: str
) -> Dict[str, Any]:
    """
    Fallback heuristic analysis when LLM is unavailable.
    """
    scores = {
        "warmth": 0,
        "questions": 0,
        "structure": 0,
        "no_pressure": 0,
        "active_listening": 0
    }
    
    issues = []
    
    msg_lower = manager_reply.lower()
    
    # Warmth check
    warm_words = ["добр", "рад", "приятно", "здравствуйте", "привет", "понимаю", "отлично"]
    if any(word in msg_lower for word in warm_words):
        scores["warmth"] = 7
    else:
        scores["warmth"] = 4
        issues.append("Добавь больше тепла в общение")
    
    # Questions check
    question_count = manager_reply.count("?")
    if question_count > 0:
        scores["questions"] = min(10, question_count * 3)
    else:
        scores["questions"] = 2
        issues.append("Задавай открытые вопросы")
    
    # Length and clarity
    word_count = len(manager_reply.split())
    if 15 <= word_count <= 60:
        scores["structure"] = 8
    elif word_count < 15:
        scores["structure"] = 4
        issues.append("Сообщение слишком короткое")
    else:
        scores["structure"] = 6
        issues.append("Сообщение можно сократить")
    
    # No pressure check
    pressure_words = ["должны", "обязательно", "необходимо", "срочно", "сейчас"]
    if any(word in msg_lower for word in pressure_words):
        scores["no_pressure"] = 4
        issues.append("Убери давление на клиента")
    else:
        scores["no_pressure"] = 8
    
    # Active listening
    listening_words = ["понимаю", "слышу", "правильно", "верно", "интересно"]
    if any(word in msg_lower for word in listening_words):
        scores["active_listening"] = 8
    else:
        scores["active_listening"] = 5
        issues.append("Покажи, что слышишь клиента")
    
    # Calculate total score
    total_score = sum(scores.values()) / len(scores)
    
    # Generate advice
    if total_score >= 7:
        advice = "Отличная работа! Ты создаёшь тёплую атмосферу и показываешь искренний интерес к клиенту. Продолжай в том же духе!"
    elif total_score >= 5:
        advice = "Хорошее начало! " + " ".join(issues[:2]) + ". Это поможет клиенту чувствовать себя комфортнее."
    else:
        advice = "Давай улучшим диалог. " + " ".join(issues[:3]) + ". Помни: главное — создать доверительную атмосферу."
    
    return {
        "scores": scores,
        "total_score": round(total_score, 1),
        "issues": issues,
        "advice": advice
    }
