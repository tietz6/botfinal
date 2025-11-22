"""Training Scripts API Routes"""
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.state import get_state, set_state
from core.llm_gateway import get_llm_gateway

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/training_scripts/v1", tags=["training-scripts"])


class StartRequest(BaseModel):
    """Start training session request"""
    role: Optional[str] = "manager"  # manager or generator
    topic: Optional[str] = "song"  # song, photo, cartoon, custom


class TurnRequest(BaseModel):
    """Manager turn request"""
    text: str


@router.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy", "module": "training_scripts"}


@router.post("/start/{session_id}")
async def start_training(session_id: str, request: StartRequest = StartRequest()):
    """
    Start sales script training session.
    
    The system will play both the client and coach roles:
    - Client: responds to manager's pitches realistically
    - Coach: provides feedback on technique
    
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
        
        await set_state(f"training_script:{session_id}", session_state)
        
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
    
    System will:
    1. Generate client's response to manager
    2. Generate coach feedback
    3. Update scores
    4. Determine if moving to next stage
    
    Args:
        session_id: Session identifier
        request: Manager's message
        
    Returns:
        Client reply, coach feedback, current scores
    """
    try:
        # Get session state
        session_state = await get_state(f"training_script:{session_id}")
        
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
        
        # Update scores (simple heuristics + LLM insights)
        _update_scores(session_state, request.text, coach_feedback)
        
        # Determine stage progression
        _update_stage(session_state)
        
        # Check if final
        is_final = session_state["turn_count"] >= 10 or session_state["stage"] == "closing"
        
        # Save state
        await set_state(f"training_script:{session_id}", session_state)
        
        return {
            "success": True,
            "status": "active" if not is_final else "ready_for_result",
            "stage": session_state["stage"],
            "client_reply": client_reply,
            "coach_feedback": coach_feedback,
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
        session_state = await get_state(f"training_script:{session_id}")
        
        if not session_state:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Calculate final score
        scores = session_state["scores"]
        final_score = sum(scores.values()) / len(scores) * 10  # Scale to 100
        
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
    
    # Simple heuristics - calculate per-turn score and average with existing
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
