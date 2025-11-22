"""
Exam V1
Final assessment of manager skills
"""
import random
from typing import Dict, Any, Optional
from modules.dialog_memory.v1 import start_session, append_message, get_session
from modules.deepseek_persona.v1 import persona_chat

# Exam scenarios (combines different training modules)
EXAM_SCENARIOS = [
    {
        "type": "master_path_short",
        "name": "Быстрый цикл сделки",
        "description": "Пройди основные этапы: приветствие, история, оплата",
        "rounds": 5,
        "weight": 3
    },
    {
        "type": "objection_handling",
        "name": "Комплексные возражения",
        "description": "Отработай 3 разных возражения подряд",
        "rounds": 3,
        "weight": 2
    },
    {
        "type": "upsell_combo",
        "name": "Связка допродаж",
        "description": "Сделай 2 допродажи в одном диалоге",
        "rounds": 4,
        "weight": 2
    },
    {
        "type": "mixed_arena",
        "name": "Смешанная арена",
        "description": "Работа с разными типами клиентов",
        "rounds": 5,
        "weight": 2
    }
]


async def init_exam_session(
    manager_id: str,
    session_id: str,
    scenario_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Initialize exam session.
    
    Args:
        manager_id: Manager identifier
        session_id: Session identifier
        scenario_type: Exam scenario type (random if not specified)
    
    Returns:
        Initial exam instructions
    """
    # Select scenario
    scenario = None
    if scenario_type:
        scenario = next((s for s in EXAM_SCENARIOS if s["type"] == scenario_type), None)
    
    if not scenario:
        scenario = random.choice(EXAM_SCENARIOS)
    
    # Create session
    await start_session(manager_id, "exam", session_id)
    
    # Exam introduction
    exam_intro = f"""📝 **ЭКЗАМЕН**

Сценарий: **{scenario["name"]}**
{scenario["description"]}

Раундов: {scenario["rounds"]}

Это финальная проверка твоих навыков. Я буду оценивать:
✓ Эмпатию и тепло
✓ Структуру диалога
✓ Работу с возражениями
✓ Естественность общения

В конце получишь балл 0-100 и вердикт.

Начинаем! Твой первый ход — приветствие клиенту."""
    
    # Save exam intro
    await append_message(
        manager_id, "exam", session_id,
        role="coach",
        content=exam_intro,
        stage="round_1"
    )
    
    # Store scenario in metadata
    from modules.dialog_memory.v1 import update_metadata
    await update_metadata(
        manager_id, "exam", session_id,
        {
            "scenario": scenario,
            "current_round": 1,
            "total_rounds": scenario["rounds"],
            "scores": []
        }
    )
    
    return {
        "scenario_type": scenario["type"],
        "scenario_name": scenario["name"],
        "total_rounds": scenario["rounds"],
        "current_round": 1,
        "exam_intro": exam_intro,
        "status": "active"
    }


async def process_exam_turn(
    manager_id: str,
    session_id: str,
    manager_text: str
) -> Dict[str, Any]:
    """
    Process manager's turn in exam.
    
    Args:
        manager_id: Manager identifier
        session_id: Session identifier
        manager_text: Manager's response
    
    Returns:
        Client response and round evaluation
    """
    # Get session
    session = await get_session(manager_id, "exam", session_id)
    if not session:
        raise ValueError("Session not found")
    
    metadata = session.get("metadata", {})
    scenario = metadata.get("scenario", {})
    current_round = metadata.get("current_round", 1)
    total_rounds = metadata.get("total_rounds", 5)
    
    # Save manager message
    await append_message(
        manager_id, "exam", session_id,
        role="manager",
        content=manager_text
    )
    
    # Evaluate round
    round_score = await _evaluate_exam_round(manager_text, current_round, scenario)
    
    # Build conversation context
    conversation_history = []
    for msg in session.get("messages", [])[-6:]:
        if msg["role"] != "coach":
            conversation_history.append({
                "role": msg["role"],
                "content": msg["content"]
            })
    
    conversation_history.append({
        "role": "user",
        "content": f"Экзамен, раунд {current_round}/{total_rounds}. Менеджер написал: {manager_text}"
    })
    
    # Generate client response
    client_reply = await persona_chat("client", conversation_history)
    
    # Save client reply
    await append_message(
        manager_id, "exam", session_id,
        role="client",
        content=client_reply
    )
    
    # Update metadata with score
    scores = metadata.get("scores", [])
    scores.append(round_score)
    
    is_final_round = current_round >= total_rounds
    next_round = current_round + 1 if not is_final_round else current_round
    
    from modules.dialog_memory.v1 import update_metadata
    await update_metadata(
        manager_id, "exam", session_id,
        {
            "current_round": next_round,
            "scores": scores,
            "completed": is_final_round
        }
    )
    
    # Generate brief coach note
    coach_note = f"Раунд {current_round}: {round_score}/10"
    if not is_final_round:
        coach_note += f"\nПродолжаем, раунд {next_round}/{total_rounds}"
    else:
        coach_note += "\n\nЭкзамен завершён! Запроси результат через /exam/result/{session_id}"
    
    await append_message(
        manager_id, "exam", session_id,
        role="coach",
        content=coach_note,
        stage=f"round_{next_round}" if not is_final_round else "completed"
    )
    
    return {
        "client_reply": client_reply,
        "coach_note": coach_note,
        "round": current_round,
        "round_score": round_score,
        "is_final_round": is_final_round,
        "next_round": next_round if not is_final_round else None
    }


async def _evaluate_exam_round(
    manager_text: str,
    round_num: int,
    scenario: Dict
) -> int:
    """Evaluate a single exam round"""
    
    # Basic evaluation criteria
    scores = []
    
    # Length check (should be substantial)
    word_count = len(manager_text.split())
    if word_count >= 20:
        scores.append(3)
    elif word_count >= 10:
        scores.append(2)
    else:
        scores.append(1)
    
    # Warmth check
    msg_lower = manager_text.lower()
    warm_words = ["добр", "привет", "рад", "здравств", "приятно", "😊", "🥰"]
    if any(word in msg_lower for word in warm_words):
        scores.append(2)
    else:
        scores.append(1)
    
    # Question check
    if "?" in manager_text:
        scores.append(2)
    else:
        scores.append(1)
    
    # Empathy check
    empathy_words = ["понимаю", "важно", "интересно", "расскажите", "хотели бы"]
    if any(word in msg_lower for word in empathy_words):
        scores.append(2)
    else:
        scores.append(1)
    
    # Structure check (no pressure words)
    pressure_words = ["должны", "обязательно", "срочно"]
    if not any(word in msg_lower for word in pressure_words):
        scores.append(1)
    
    return min(10, sum(scores))


async def get_exam_result(manager_id: str, session_id: str) -> Dict[str, Any]:
    """
    Get final exam result.
    
    Args:
        manager_id: Manager identifier
        session_id: Session identifier
    
    Returns:
        Final score and verdict
    """
    session = await get_session(manager_id, "exam", session_id)
    if not session:
        raise ValueError("Session not found")
    
    metadata = session.get("metadata", {})
    scores = metadata.get("scores", [])
    scenario = metadata.get("scenario", {})
    completed = metadata.get("completed", False)
    
    if not completed:
        return {
            "status": "in_progress",
            "message": "Экзамен ещё не завершён",
            "current_round": metadata.get("current_round", 1),
            "total_rounds": metadata.get("total_rounds", 5)
        }
    
    # Calculate final score
    if not scores:
        final_score = 0
    else:
        avg_score = sum(scores) / len(scores)
        final_score = int((avg_score / 10) * 100)
    
    # Determine verdict
    if final_score >= 85:
        verdict = "🏆 ОТЛИЧНО! Ты готов работать с реальными клиентами. Отличная эмпатия, структура и естественность."
        grade = "A"
    elif final_score >= 70:
        verdict = "✅ ХОРОШО! Базовые навыки на месте. Продолжай практиковаться для уверенности."
        grade = "B"
    elif final_score >= 55:
        verdict = "📚 УДОВЛЕТВОРИТЕЛЬНО. Есть понимание, но нужно больше практики. Повтори тренировки."
        grade = "C"
    else:
        verdict = "🔄 НУЖНА ПРАКТИКА. Вернись к базовым модулям и отработай навыки."
        grade = "D"
    
    return {
        "status": "completed",
        "final_score": final_score,
        "grade": grade,
        "verdict": verdict,
        "scenario_name": scenario.get("name", ""),
        "rounds_completed": len(scores),
        "round_scores": scores,
        "average_round_score": round(sum(scores) / len(scores), 1) if scores else 0
    }


async def get_exam_snapshot(manager_id: str, session_id: str) -> Dict[str, Any]:
    """Get exam session snapshot"""
    
    session = await get_session(manager_id, "exam", session_id)
    if not session:
        raise ValueError("Session not found")
    
    messages = session.get("messages", [])
    metadata = session.get("metadata", {})
    
    return {
        "session_id": session_id,
        "manager_id": manager_id,
        "scenario": metadata.get("scenario", {}),
        "current_round": metadata.get("current_round", 1),
        "total_rounds": metadata.get("total_rounds", 5),
        "scores": metadata.get("scores", []),
        "completed": metadata.get("completed", False),
        "messages": messages,
        "created_at": session.get("created_at"),
        "updated_at": session.get("updated_at")
    }
