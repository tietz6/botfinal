"""
Upsell V1
Training for upselling and cross-selling
"""
import random
from typing import Dict, Any, Optional
from modules.dialog_memory.v1 import start_session, append_message, get_session
from modules.deepseek_persona.v1 import persona_chat

# Upsell scenarios
UPSELL_SCENARIOS = {
    "texts_warmup": {
        "name": "Подогрев перед текстами",
        "context": "Клиент заказал песню, сейчас этап подготовки текстов",
        "initial_message": "Хорошо, жду ваши варианты текстов. Когда будут готовы?",
        "goal": "Мягко упомянуть, что будет 2 варианта текста, создавая ожидание ценности"
    },
    "both_demos": {
        "name": "Оба демо",
        "context": "Клиент прослушал два демо и выбирает",
        "initial_message": "Оба варианта классные! Сложно выбрать... Наверное, возьму первый.",
        "goal": "Предложить взять оба демо в разных жанрах - больше вариантов для подарков"
    },
    "ladder_2_to_4": {
        "name": "Лестница 2→4 песни",
        "context": "Клиент уже взял 2 песни",
        "initial_message": "Спасибо! Мне очень нравится, как вы работаете. Эти две песни будут отличным подарком.",
        "goal": "Предложить акцию: при заказе 3-й песни — 4-я в подарок. Готовые подарки для разных людей"
    },
    "additional_version": {
        "name": "Дополнительная версия",
        "context": "Клиент доволен финальной песней",
        "initial_message": "Песня получилась потрясающей! Спасибо вам большое!",
        "goal": "Предложить дополнительную версию (акустика, ремикс) со скидкой"
    }
}


async def init_upsell_session(
    manager_id: str,
    session_id: str,
    scenario: Optional[str] = None
) -> Dict[str, Any]:
    """
    Initialize upsell training session.
    
    Args:
        manager_id: Manager identifier
        session_id: Session identifier
        scenario: Upsell scenario type (random if not specified)
    
    Returns:
        Initial response with scenario
    """
    # Select scenario
    if not scenario or scenario not in UPSELL_SCENARIOS:
        scenario = random.choice(list(UPSELL_SCENARIOS.keys()))
    
    scenario_data = UPSELL_SCENARIOS[scenario]
    
    # Create session
    await start_session(manager_id, "upsell", session_id)
    
    # Coach introduction
    coach_intro = f"""💎 **Тренировка: Допродажи**

Сценарий: **{scenario_data["name"]}**

Контекст: {scenario_data["context"]}

Твоя задача: {scenario_data["goal"]}

**Важно:**
✓ Не дави — подсвети выгоду и удобство
✓ Покажи ценность через эмоции и практичность
✓ Дай клиенту самому захотеть больше

Клиент сейчас напишет, а ты попробуй сделать допродажу мягко и естественно."""
    
    # Save coach message
    await append_message(
        manager_id, "upsell", session_id,
        role="coach",
        content=coach_intro,
        stage="active"
    )
    
    # Client message
    await append_message(
        manager_id, "upsell", session_id,
        role="client",
        content=scenario_data["initial_message"]
    )
    
    # Store scenario in metadata
    from modules.dialog_memory.v1 import update_metadata
    await update_metadata(
        manager_id, "upsell", session_id,
        {
            "scenario": scenario,
            "scenario_name": scenario_data["name"],
            "goal": scenario_data["goal"]
        }
    )
    
    return {
        "scenario": scenario,
        "scenario_name": scenario_data["name"],
        "coach_message": coach_intro,
        "client_message": scenario_data["initial_message"],
        "goal": scenario_data["goal"],
        "status": "active"
    }


async def process_upsell_turn(
    manager_id: str,
    session_id: str,
    manager_text: str
) -> Dict[str, Any]:
    """
    Process manager's upsell attempt.
    
    Args:
        manager_id: Manager identifier
        session_id: Session identifier
        manager_text: Manager's message
    
    Returns:
        Client reaction and coach feedback
    """
    # Get session
    session = await get_session(manager_id, "upsell", session_id)
    if not session:
        raise ValueError("Session not found")
    
    scenario = session.get("metadata", {}).get("scenario", "")
    goal = session.get("metadata", {}).get("goal", "")
    
    # Save manager message
    await append_message(
        manager_id, "upsell", session_id,
        role="manager",
        content=manager_text
    )
    
    # Evaluate upsell attempt
    evaluation = await _evaluate_upsell(manager_text, scenario)
    
    # Build conversation context
    conversation_history = []
    for msg in session.get("messages", [])[-6:]:
        if msg["role"] != "coach":
            conversation_history.append({
                "role": msg["role"],
                "content": msg["content"]
            })
    
    # Add scenario context
    scenario_data = UPSELL_SCENARIOS.get(scenario, {})
    context_msg = f"Контекст: {scenario_data.get('context', '')}. Менеджер предлагает: {manager_text}"
    conversation_history.append({
        "role": "user",
        "content": context_msg
    })
    
    # Generate client reaction
    client_reply = await persona_chat("client", conversation_history)
    
    # Save client reply
    await append_message(
        manager_id, "upsell", session_id,
        role="client",
        content=client_reply
    )
    
    # Generate coach feedback
    coach_feedback = await _generate_upsell_feedback(
        manager_text,
        evaluation,
        scenario,
        goal
    )
    
    # Save coach feedback
    await append_message(
        manager_id, "upsell", session_id,
        role="coach",
        content=coach_feedback,
        score=evaluation
    )
    
    return {
        "client_reply": client_reply,
        "coach_feedback": coach_feedback,
        "evaluation": evaluation,
        "scenario": scenario
    }


async def _evaluate_upsell(manager_text: str, scenario: str) -> Dict[str, Any]:
    """Evaluate upsell attempt"""
    
    scores = {
        "value_shown": 0,  # Показана ценность
        "no_pressure": 0,  # Нет давления
        "practical": 0     # Практичность предложения
    }
    
    msg_lower = manager_text.lower()
    
    # Value check
    value_words = [
        "готов", "подарок", "удобно", "выгода", "ценность",
        "особенн", "уникальн", "больше", "вариант"
    ]
    value_count = sum(1 for word in value_words if word in msg_lower)
    scores["value_shown"] = min(10, value_count * 3)
    
    # No pressure check
    pressure_words = ["должны", "обязательно", "только сейчас", "последний шанс"]
    has_pressure = any(word in msg_lower for word in pressure_words)
    scores["no_pressure"] = 3 if has_pressure else 9
    
    # Practical benefits check
    practical_words = ["несколько", "разных", "выбор", "жена", "мама", "друг", "семья"]
    practical_count = sum(1 for word in practical_words if word in msg_lower)
    scores["practical"] = min(10, practical_count * 4)
    
    overall = sum(scores.values()) / len(scores)
    
    return {
        "scores": scores,
        "overall": round(overall, 1),
        "successful": overall >= 6.5
    }


async def _generate_upsell_feedback(
    manager_text: str,
    evaluation: Dict,
    scenario: str,
    goal: str
) -> str:
    """Generate coach feedback on upsell attempt"""
    
    scores = evaluation["scores"]
    overall = evaluation["overall"]
    
    scenario_data = UPSELL_SCENARIOS.get(scenario, {})
    
    feedback_prompt = f"""Менеджер делает допродажу в сценарии "{scenario_data.get('name', '')}".

Цель: {goal}

Его предложение: "{manager_text}"

Оценки: ценность={scores['value_shown']}, нет давления={scores['no_pressure']}, практичность={scores['practical']}

Дай краткую обратную связь (2-3 предложения):
- Что удалось в допродаже
- Как усилить ценность предложения без давления"""
    
    coach_messages = [{"role": "user", "content": feedback_prompt}]
    feedback = await persona_chat("coach", coach_messages)
    
    return feedback


async def get_upsell_snapshot(manager_id: str, session_id: str) -> Dict[str, Any]:
    """Get upsell session snapshot"""
    
    session = await get_session(manager_id, "upsell", session_id)
    if not session:
        raise ValueError("Session not found")
    
    messages = session.get("messages", [])
    manager_messages = [m for m in messages if m["role"] == "manager"]
    
    metadata = session.get("metadata", {})
    
    return {
        "session_id": session_id,
        "manager_id": manager_id,
        "scenario": metadata.get("scenario"),
        "scenario_name": metadata.get("scenario_name"),
        "goal": metadata.get("goal"),
        "messages": messages,
        "stats": {
            "total_turns": len(manager_messages),
            "total_messages": len(messages)
        },
        "score": session.get("score", {}),
        "created_at": session.get("created_at"),
        "updated_at": session.get("updated_at")
    }
