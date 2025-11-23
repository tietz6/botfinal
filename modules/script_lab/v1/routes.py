"""Script Lab API Routes - Analyze and improve sales scripts"""
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .evaluator import get_evaluator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/script_lab/v1", tags=["script-lab"])


class ScriptRequest(BaseModel):
    """Request to analyze a script"""
    script: str
    scenario: Optional[str] = "full_sale"


class ScriptResponse(BaseModel):
    """Response with script analysis"""
    success: bool
    overall_score: float
    scores: dict
    strengths: list
    weaknesses: list
    suggestions: list
    improved_version: Optional[str] = None


@router.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy", "module": "script_lab"}


@router.post("/analyze")
async def analyze_script(request: ScriptRequest):
    """
    Analyze a sales script and provide detailed feedback.
    
    Evaluates:
    - Structure (greeting, intro, body, closing)
    - Psychology (empathy, benefits, social proof)
    - Softness (non-aggressive, gentle approach)
    - Engagement (questions, emotions, storytelling)
    - CTA (clear call-to-action)
    
    Args:
        request: Script text and scenario type
        
    Returns:
        Detailed analysis with scores, feedback, and improved version
    """
    try:
        evaluator = get_evaluator()
        
        # Validate input
        if not request.script or len(request.script.strip()) < 10:
            raise HTTPException(
                status_code=400,
                detail="Script is too short. Please provide a meaningful script (at least 10 characters)."
            )
        
        # Analyze script
        analysis = await evaluator.evaluate_script(
            script=request.script,
            scenario=request.scenario
        )
        
        return {
            "success": True,
            "overall_score": analysis.overall_score,
            "scores": {
                "structure": analysis.structure_score,
                "psychology": analysis.psychology_score,
                "softness": analysis.softness_score,
                "engagement": analysis.engagement_score,
                "cta": analysis.cta_score
            },
            "strengths": analysis.strengths,
            "weaknesses": analysis.weaknesses,
            "suggestions": analysis.suggestions,
            "improved_version": analysis.improved_version,
            "feedback": {
                "overall": _get_overall_feedback(analysis.overall_score),
                "structure": _get_score_feedback(analysis.structure_score, "structure"),
                "psychology": _get_score_feedback(analysis.psychology_score, "psychology"),
                "softness": _get_score_feedback(analysis.softness_score, "softness"),
                "engagement": _get_score_feedback(analysis.engagement_score, "engagement"),
                "cta": _get_score_feedback(analysis.cta_score, "cta")
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to analyze script: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scenarios")
async def get_scenarios():
    """
    Get list of available script scenarios.
    
    Returns:
        List of supported scenario types
    """
    return {
        "success": True,
        "scenarios": [
            {
                "id": "full_sale",
                "name": "Полная продажа",
                "description": "Весь процесс от первого касания до закрытия сделки"
            },
            {
                "id": "first_contact",
                "name": "Первый контакт",
                "description": "Приветствие и установление контакта"
            },
            {
                "id": "objection_handling",
                "name": "Работа с возражениями",
                "description": "Ответы на возражения клиента"
            },
            {
                "id": "upsell",
                "name": "Допродажа",
                "description": "Предложение дополнительных продуктов"
            },
            {
                "id": "closing",
                "name": "Закрытие сделки",
                "description": "Финализация и получение оплаты"
            }
        ]
    }


def _get_overall_feedback(score: float) -> str:
    """Get overall feedback based on score"""
    if score >= 85:
        return "🌟 Отличный скрипт! Профессиональный уровень."
    elif score >= 70:
        return "👍 Хороший скрипт с небольшими замечаниями."
    elif score >= 55:
        return "📝 Средний уровень. Есть что улучшить."
    else:
        return "⚠️ Требуется серьезная доработка."


def _get_score_feedback(score: float, category: str) -> str:
    """Get category-specific feedback"""
    
    feedback_map = {
        "structure": {
            "high": "Структура скрипта отличная - все элементы на месте",
            "medium": "Структура в целом хороша, но можно улучшить",
            "low": "Структура требует доработки - не хватает ключевых элементов"
        },
        "psychology": {
            "high": "Превосходное использование психологических триггеров",
            "medium": "Психология присутствует, но можно усилить",
            "low": "Недостаточно психологических элементов"
        },
        "softness": {
            "high": "Мягкий и располагающий стиль общения",
            "medium": "Тон в целом нормальный, но есть жесткие формулировки",
            "low": "Слишком агрессивный подход - нужно смягчить"
        },
        "engagement": {
            "high": "Отлично вовлекает клиента в диалог",
            "medium": "Вовлечение есть, но можно усилить",
            "low": "Слабая вовлеченность - добавьте вопросы и эмоции"
        },
        "cta": {
            "high": "Четкий и понятный призыв к действию",
            "medium": "CTA присутствует, но можно сделать яснее",
            "low": "Нечеткий призыв к действию - клиент не понимает, что делать дальше"
        }
    }
    
    level = "high" if score >= 75 else "medium" if score >= 60 else "low"
    return feedback_map.get(category, {}).get(level, "")
