"""Exams API Routes"""
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.state import get_state, set_state
from core.llm_gateway import get_llm_gateway

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/exams/v1", tags=["exams"])


class StartRequest(BaseModel):
    """Start exam request"""
    scenario: Optional[str] = "song"  # song, photo, cartoon, full


class TurnRequest(BaseModel):
    """Exam turn request"""
    text: str


# Predefined scenarios
SCENARIOS = {
    "song": {
        "name": "Продажа персональной песни",
        "rounds": 5,
        "client_profile": {
            "traits": "осторожный, задаёт много вопросов",
            "mood": "skeptical",
            "context": "Хочет подарок, но сомневается в ценности"
        }
    },
    "photo": {
        "name": "Оживление фото",
        "rounds": 4,
        "client_profile": {
            "traits": "эмоциональный, ностальгирующий",
            "mood": "sentimental",
            "context": "Есть фото ушедшего близкого, хочет сохранить память"
        }
    },
    "cartoon": {
        "name": "Мультфильм как апсейл",
        "rounds": 3,
        "client_profile": {
            "traits": "уже заказал песню, открыт к предложениям",
            "mood": "positive",
            "context": "Слушает предложение по мультфильму"
        }
    },
    "full": {
        "name": "Полный цикл продажи",
        "rounds": 7,
        "client_profile": {
            "traits": "смешанный тип, реалистичный",
            "mood": "neutral",
            "context": "Первый контакт, ничего не знает о продукте"
        }
    }
}


@router.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy", "module": "exams"}


@router.post("/start/{session_id}")
async def start_exam(session_id: str, request: StartRequest = StartRequest()):
    """
    Start exam session.
    
    Exam is a comprehensive test where the manager must handle
    the full sales cycle under evaluation.
    
    Args:
        session_id: Session identifier
        request: Exam parameters (scenario type)
        
    Returns:
        Exam introduction and first client message
    """
    try:
        scenario = SCENARIOS.get(request.scenario, SCENARIOS["song"])
        
        # Initialize exam state
        exam_state = {
            "scenario": request.scenario,
            "scenario_name": scenario["name"],
            "max_rounds": scenario["rounds"],
            "current_round": 0,
            "dialog_history": [],
            "client_profile": scenario["client_profile"],
            "round_scores": [],
            "status": "in_progress"
        }
        
        await set_state(f"exam:{session_id}", exam_state)
        
        # Generate first client message
        llm = get_llm_gateway()
        
        client_message = await llm.generate_client_reply({
            "dialog_history": [],
            "client_profile": exam_state["client_profile"],
            "manager_message": ""
        })
        
        exam_intro = f"""🎓 ЭКЗАМЕН: {scenario['name']}

Условия:
• Раундов: {scenario['rounds']}
• Оценка по всем критериям
• Ошибки снижают балл
• Финальная оценка в конце

Ты готов? Начинаем!"""
        
        return {
            "success": True,
            "status": "in_progress",
            "exam_intro": exam_intro,
            "scenario_name": scenario["name"],
            "client_message": client_message,
            "current_round": 1,
            "max_rounds": scenario["rounds"]
        }
    except Exception as e:
        logger.error(f"Failed to start exam {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/turn/{session_id}")
async def exam_turn(session_id: str, request: TurnRequest):
    """
    Process exam turn.
    
    Each turn is evaluated and scored. After all rounds,
    the exam can be finalized.
    
    Args:
        session_id: Session identifier
        request: Manager's answer
        
    Returns:
        Client reply, round evaluation, progress
    """
    try:
        exam_state = await get_state(f"exam:{session_id}")
        
        if not exam_state:
            raise HTTPException(status_code=404, detail="Exam session not found")
        
        if exam_state["status"] == "finished":
            raise HTTPException(status_code=400, detail="Exam already finished")
        
        # Add manager message to history
        exam_state["dialog_history"].append({
            "from": "manager",
            "text": request.text,
            "round": exam_state["current_round"]
        })
        
        # Generate client reply
        llm = get_llm_gateway()
        
        client_reply = await llm.generate_client_reply({
            "dialog_history": exam_state["dialog_history"],
            "client_profile": exam_state["client_profile"],
            "manager_message": request.text
        })
        
        # Add client reply to history
        exam_state["dialog_history"].append({
            "from": "client",
            "text": client_reply,
            "round": exam_state["current_round"]
        })
        
        # Evaluate round
        round_score = _evaluate_turn(request.text, exam_state["current_round"])
        exam_state["round_scores"].append(round_score)
        
        # Move to next round
        exam_state["current_round"] += 1
        
        # Check if exam is complete
        is_final = exam_state["current_round"] > exam_state["max_rounds"]
        if is_final:
            exam_state["status"] = "finished"
        
        # Save state
        await set_state(f"exam:{session_id}", exam_state)
        
        coach_note = f"Раунд {exam_state['current_round'] - 1}: балл {round_score}/10"
        
        return {
            "success": True,
            "status": exam_state["status"],
            "client_reply": client_reply,
            "coach_note": coach_note,
            "round_score": round_score,
            "current_round": exam_state["current_round"],
            "max_rounds": exam_state["max_rounds"],
            "is_final_round": is_final
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process exam turn {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/result/{session_id}")
async def get_exam_result(session_id: str):
    """
    Get final exam result.
    
    Args:
        session_id: Session identifier
        
    Returns:
        Final score, grade, and detailed feedback
    """
    try:
        exam_state = await get_state(f"exam:{session_id}")
        
        if not exam_state:
            raise HTTPException(status_code=404, detail="Exam session not found")
        
        if exam_state["status"] != "finished":
            return {
                "success": True,
                "status": "in_progress",
                "message": "Exam not finished yet. Complete all rounds first."
            }
        
        # Calculate final score
        round_scores = exam_state["round_scores"]
        if not round_scores:
            final_score = 0
        else:
            final_score = sum(round_scores) / len(round_scores) * 10
        
        # Determine grade
        if final_score >= 85:
            grade = "A - Отлично"
            verdict = "🎉 Поздравляю! Ты сдал экзамен на отлично. Твоя техника на высоком уровне."
        elif final_score >= 70:
            grade = "B - Хорошо"
            verdict = "👍 Хороший результат! Есть моменты для улучшения, но база крепкая."
        elif final_score >= 55:
            grade = "C - Удовлетворительно"
            verdict = "📚 Ты справился, но нужно больше практики. Пройди тренировки ещё раз."
        else:
            grade = "D - Требуется доработка"
            verdict = "💪 Не расстраивайся. Вернись к базовым модулям и потренируйся ещё."
        
        return {
            "success": True,
            "status": "finished",
            "scenario_name": exam_state["scenario_name"],
            "final_score": round(final_score, 1),
            "grade": grade,
            "verdict": verdict,
            "round_scores": round_scores,
            "total_rounds": len(round_scores)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get exam result {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scenarios")
async def get_scenarios():
    """
    Get available exam scenarios.
    
    Returns:
        List of scenarios with descriptions
    """
    return {
        "success": True,
        "scenarios": [
            {
                "id": scenario_id,
                "name": scenario["name"],
                "rounds": scenario["rounds"],
                "difficulty": _get_difficulty(scenario["rounds"])
            }
            for scenario_id, scenario in SCENARIOS.items()
        ]
    }


def _evaluate_turn(manager_text: str, round_num: int) -> int:
    """Simple evaluation of manager's turn"""
    score = 5  # Base score
    
    text_lower = manager_text.lower()
    
    # Positive indicators
    if "?" in manager_text:
        score += 1
    if any(word in text_lower for word in ["привет", "здравств", "рад", "понимаю"]):
        score += 1
    if len(manager_text) > 50 and len(manager_text) < 300:
        score += 1
    if round_num > 2 and any(word in text_lower for word in ["песн", "подарок", "память"]):
        score += 1
    
    # Negative indicators
    if any(word in text_lower for word in ["акция", "скидка", "срочно", "успей"]):
        score -= 2
    if round_num == 1 and any(word in text_lower for word in ["цена", "стоимость", "рубл"]):
        score -= 1
    
    return max(1, min(10, score))


def _get_difficulty(rounds: int) -> str:
    """Get difficulty level based on rounds"""
    if rounds <= 3:
        return "Лёгкий"
    elif rounds <= 5:
        return "Средний"
    else:
        return "Сложный"
