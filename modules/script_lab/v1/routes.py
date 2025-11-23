"""Script Lab API Routes - Analyze and improve sales scripts"""
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .evaluator import get_evaluator
from core.state import get_state, set_state
from core.llm_gateway import get_llm_gateway

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/script_lab", tags=["script-lab"])

# Constants
SCORE_SCALE_FACTOR = 10  # Scale 0-10 scores to 0-100


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


# =======================
# Interactive Training Endpoints
# =======================

class TrainingStartRequest(BaseModel):
    """Start training session request"""
    role: Optional[str] = "manager"
    topic: Optional[str] = "song"


class TurnRequest(BaseModel):
    """Manager turn request"""
    text: str


@router.post("/start/{session_id}")
async def start_training(session_id: str, request: TrainingStartRequest = TrainingStartRequest()):
    """
    Start interactive script training session.
    
    The system plays both client and coach roles for realistic practice.
    
    Args:
        session_id: Session identifier
        request: Training parameters (role, topic)
        
    Returns:
        Initial scenario with coach intro and client first message
    """
    try:
        # Initialize session state
        session_state = {
            "role": request.role,
            "topic": request.topic,
            "stage": "greeting",
            "turn_count": 0,
            "dialog_history": [],
            "client_profile": _get_client_profile(request.topic),
            "scores": {
                "warmth": 0,
                "clarity": 0,
                "questions": 0,
                "structure": 0,
                "pressure_free": 0
            }
        }
        
        await set_state(f"script_lab:{session_id}", session_state)
        
        # Generate coach intro and first client message
        llm = get_llm_gateway()
        
        coach_message = _get_coach_intro(request.topic)
        
        # Generate first client message
        client_message = await llm.generate_client_reply({
            "dialog_history": [],
            "client_profile": session_state["client_profile"],
            "manager_message": ""
        })
        
        return {
            "success": True,
            "status": "active",
            "stage": "greeting",
            "coach_message": coach_message,
            "client_message": client_message,
            "hints": [
                "Начни с тёплого приветствия",
                "Узнай контекст: откуда клиент о нас узнал",
                "Не спеши с предложением — сначала выясни потребности"
            ]
        }
    except Exception as e:
        logger.error(f"Failed to start training session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/turn/{session_id}")
async def process_turn(session_id: str, request: TurnRequest):
    """
    Process manager's message in training session.
    
    Generates client response and coach feedback.
    
    Args:
        session_id: Session identifier
        request: Manager's message
        
    Returns:
        Client reply, coach feedback, current scores
    """
    try:
        # Get session state
        session_state = await get_state(f"script_lab:{session_id}")
        
        if not session_state:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Add manager message to history
        session_state["dialog_history"].append({
            "from": "manager",
            "text": request.text,
            "turn": session_state["turn_count"]
        })
        
        session_state["turn_count"] += 1
        
        # Generate client reply
        llm = get_llm_gateway()
        
        client_reply = await llm.generate_client_reply({
            "dialog_history": session_state["dialog_history"],
            "client_profile": session_state["client_profile"],
            "manager_message": request.text
        })
        
        # Add client reply to history
        session_state["dialog_history"].append({
            "from": "client",
            "text": client_reply,
            "turn": session_state["turn_count"]
        })
        
        # Generate coach feedback
        coach_feedback = await llm.generate_coach_feedback({
            "dialog_history": session_state["dialog_history"],
            "manager_message": request.text,
            "evaluation_criteria": "теплота, структура, вопросы, без давления",
            "stage": session_state["stage"]
        })
        
        # Update scores
        _update_scores(session_state, request.text, coach_feedback)
        
        # Update stage
        _update_stage(session_state)
        
        # Check if final
        is_final = session_state["turn_count"] >= 10 or session_state["stage"] == "closing"
        
        # Save state
        await set_state(f"script_lab:{session_id}", session_state)
        
        return {
            "success": True,
            "status": "active" if not is_final else "ready_for_result",
            "stage": session_state["stage"],
            "client_reply": client_reply,
            "coach_tip": coach_feedback,  # Use coach_tip for compatibility with bot
            "scores": session_state["scores"],
            "is_final": is_final,
            "turn_count": session_state["turn_count"]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process turn for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/result/{session_id}")
async def get_result(session_id: str):
    """
    Get final training result with score and feedback.
    
    Args:
        session_id: Session identifier
        
    Returns:
        Final evaluation with grade and advice
    """
    try:
        session_state = await get_state(f"script_lab:{session_id}")
        
        if not session_state:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Calculate final score
        scores = session_state["scores"]
        final_score = sum(scores.values()) / len(scores) * SCORE_SCALE_FACTOR
        
        # Determine grade
        if final_score >= 85:
            grade = "A"
            verdict = "Отлично! Ты показал профессиональный уровень общения."
        elif final_score >= 70:
            grade = "B"
            verdict = "Хорошо! Есть над чем работать, но база крепкая."
        elif final_score >= 55:
            grade = "C"
            verdict = "Неплохо, но нужно больше практики."
        else:
            grade = "D"
            verdict = "Требуется серьёзная работа над техникой общения."
        
        # Identify strengths and weaknesses
        strong_sides = []
        weak_sides = []
        
        for criteria, score in scores.items():
            if score >= 8:
                strong_sides.append(_criteria_name(criteria))
            elif score <= 5:
                weak_sides.append(_criteria_name(criteria))
        
        advice = _generate_advice(weak_sides, session_state["stage"])
        
        return {
            "success": True,
            "status": "finished",
            "final_score": round(final_score, 1),
            "grade": grade,
            "verdict": verdict,
            "scores_detail": {
                "теплота общения": scores["warmth"],
                "ясность изложения": scores["clarity"],
                "качество вопросов": scores["questions"],
                "структурированность": scores["structure"],
                "без давления": scores["pressure_free"]
            },
            "strong_sides": strong_sides if strong_sides else ["базовые навыки общения"],
            "weak_sides": weak_sides if weak_sides else ["нет критичных слабостей"],
            "advice": advice,
            "total_turns": session_state["turn_count"]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get result for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _get_client_profile(topic: str) -> dict:
    """Get client profile based on topic"""
    profiles = {
        "song": {
            "traits": "заинтересованный, но осторожный",
            "mood": "positive",
            "context": "Узнал о сервисе из рекламы, хочет подарок жене/мужу"
        },
        "photo": {
            "traits": "эмоциональный, ностальгирующий",
            "mood": "sentimental",
            "context": "Есть старое фото близкого человека, хочет оживить память"
        },
        "cartoon": {
            "traits": "креативный, ищет wow-эффект",
            "mood": "excited",
            "context": "Хочет необычный подарок, видел примеры работ"
        },
        "custom": {
            "traits": "любопытный, открытый к диалогу",
            "mood": "neutral",
            "context": "Впервые на сайте, изучает возможности"
        }
    }
    return profiles.get(topic, profiles["custom"])


def _get_coach_intro(topic: str) -> str:
    """Get coach introduction message"""
    intros = {
        "song": "Привет! Сегодня мы потренируем твой скрипт продажи персональных песен. Я буду играть роль клиента, а ты — менеджера. После каждого твоего сообщения я дам обратную связь. Начнём с самого начала — представь, что клиент только что написал тебе в чат.",
        "photo": "Давай потренируем продажу оживления фотографий. Это деликатная тема, часто связанная с памятью. Покажи, как ты умеешь быть тёплым и тактичным. Я буду клиентом, ты — менеджером. Поехали!",
        "cartoon": "Мультфильмы по песням — это апсейл и креатив. Посмотрим, как ты умеешь показать ценность этого продукта. Я — клиент, который уже заказал песню. Попробуй продать ему мультфильм!",
        "custom": "Сегодня свободная тренировка. Я буду клиентом, который пришёл с общим запросом. Покажи, как ты ведёшь диалог от начала до конца. Готов? Начинай!"
    }
    return intros.get(topic, intros["custom"])


def _update_scores(session_state: dict, manager_text: str, coach_feedback: str):
    """Update scores based on manager's message"""
    scores = session_state["scores"]
    turn_count = session_state["turn_count"]
    
    # Simple heuristics
    text_lower = manager_text.lower()
    
    # Warmth: check for friendly words
    warmth_words = ["привет", "здравствуй", "рад", "приятно", "спасибо", "понимаю"]
    warmth_score = min(10, sum(2 for word in warmth_words if word in text_lower))
    scores["warmth"] = (scores["warmth"] * (turn_count - 1) + warmth_score) / turn_count
    
    # Questions: check for question marks
    questions_count = manager_text.count("?")
    questions_score = min(10, questions_count * 3)
    scores["questions"] = (scores["questions"] * (turn_count - 1) + questions_score) / turn_count
    
    # Pressure-free: penalize if pushing too hard
    pressure_words = ["срочно", "акция", "скидка", "только сегодня", "успей"]
    pressure_count = sum(1 for word in pressure_words if word in text_lower)
    pressure_score = max(0, 10 - pressure_count * 3)
    scores["pressure_free"] = (scores["pressure_free"] * (turn_count - 1) + pressure_score) / turn_count
    
    # Clarity: longer, structured messages get points
    clarity_score = 7 if 50 < len(manager_text) < 300 else 5
    scores["clarity"] = (scores["clarity"] * (turn_count - 1) + clarity_score) / turn_count
    
    # Structure: based on presence of structure elements
    structure_score = 5
    if "?" in manager_text:
        structure_score += 2
    if len(manager_text) > 50:
        structure_score += 2
    scores["structure"] = (scores["structure"] * (turn_count - 1) + min(10, structure_score)) / turn_count
    
    # Normalize scores to 0-10 range
    for key in scores:
        scores[key] = max(0, min(10, scores[key]))


def _update_stage(session_state: dict):
    """Update conversation stage based on turn count"""
    turn_count = session_state["turn_count"]
    
    if turn_count <= 2:
        session_state["stage"] = "greeting"
    elif turn_count <= 5:
        session_state["stage"] = "discovery"
    elif turn_count <= 8:
        session_state["stage"] = "presentation"
    else:
        session_state["stage"] = "closing"


def _criteria_name(criteria: str) -> str:
    """Get human-readable criteria name"""
    names = {
        "warmth": "теплота общения",
        "clarity": "ясность изложения",
        "questions": "качество вопросов",
        "structure": "структурированность",
        "pressure_free": "общение без давления"
    }
    return names.get(criteria, criteria)


def _generate_advice(weak_sides: list, final_stage: str) -> str:
    """Generate personalized advice"""
    if not weak_sides:
        return "Продолжай в том же духе! Твоя техника на высоком уровне."
    
    advice_parts = ["Рекомендации для улучшения:"]
    
    if "теплота общения" in weak_sides:
        advice_parts.append("• Добавь больше тёплых слов, обращайся к клиенту по-дружески")
    
    if "качество вопросов" in weak_sides:
        advice_parts.append("• Задавай больше открытых вопросов, которые раскрывают историю клиента")
    
    if "общение без давления" in weak_sides:
        advice_parts.append("• Убери агрессивные триггеры (акции, срочность). Дай клиенту пространство для решения")
    
    if "ясность изложения" in weak_sides:
        advice_parts.append("• Структурируй сообщения: сначала резюме, потом детали, потом вопрос")
    
    if final_stage == "greeting":
        advice_parts.append("• Ты не дошёл до стадии презентации — работай над выяснением потребностей")
    
    return "\n".join(advice_parts)
