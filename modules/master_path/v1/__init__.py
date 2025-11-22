"""
Master Path V1
Full sales cycle training: greeting → story → texts → genre → payment → demo → final
"""
from typing import Dict, Any, List
from modules.dialog_memory.v1 import start_session, append_message, get_session
from modules.deepseek_persona.v1 import persona_chat, evaluate_message

# Sales cycle stages
STAGES = [
    "greeting",    # First contact
    "story",       # Collecting customer story
    "texts",       # Preparing and sending song texts
    "genre",       # Genre and performer selection
    "payment",     # Payment discussion
    "demo",        # Sending 2 demo versions
    "final"        # Final version selection and completion
]

# Stage-specific prompts and criteria
STAGE_INFO = {
    "greeting": {
        "description": "Первое касание с клиентом",
        "criteria": [
            "Тёплое приветствие",
            "Представление себя и проекта",
            "Вопрос: 'Кому хотите подарить песню?'"
        ],
        "coach_hint": "При первом касании важно создать тёплую атмосферу. Представься, кратко расскажи о проекте и задай открытый вопрос про получателя подарка."
    },
    "story": {
        "description": "Сбор истории клиента",
        "criteria": [
            "Вопросы про имена людей",
            "Сколько времени вместе",
            "Как познакомились",
            "Какие моменты важны для песни"
        ],
        "coach_hint": "Собери детали истории: имена, важные даты, как познакомились, что клиент хочет передать в песне. Задавай открытые вопросы."
    },
    "texts": {
        "description": "Подготовка вариантов текста песни",
        "criteria": [
            "Объяснение, что готовятся 2 варианта текста",
            "Уточнение деталей для текста",
            "Сроки подготовки"
        ],
        "coach_hint": "Объясни, что подготовишь два варианта текста на основе истории. Уточни оставшиеся детали и озвучь сроки."
    },
    "genre": {
        "description": "Выбор жанра и исполнителя",
        "criteria": [
            "Предложение жанров",
            "Примеры исполнителей",
            "Учёт предпочтений клиента"
        ],
        "coach_hint": "Предложи несколько жанров (поп, рок, джаз и т.д.) и спроси, какие исполнители нравятся. Это поможет создать идеальное звучание."
    },
    "payment": {
        "description": "Объяснение оплаты",
        "criteria": [
            "Мягкое объяснение предоплаты",
            "Прозрачная логика ('всё создаётся с нуля')",
            "Без извинений и давления"
        ],
        "coach_hint": "Объясни предоплату честно и прозрачно: всё создаётся индивидуально по их истории. Не извиняйся, а покажи ценность персонального подхода."
    },
    "demo": {
        "description": "Отправка демо-версий",
        "criteria": [
            "Отправка 2 демо",
            "Предложение выбрать сердцем",
            "Возможность объединить лучшее"
        ],
        "coach_hint": "Отправь два демо и предложи послушать сердцем. Можно выбрать одно или объединить лучшие элементы обоих."
    },
    "final": {
        "description": "Финальная версия и завершение",
        "criteria": [
            "Утверждение финальной версии",
            "Сроки готовности",
            "Тёплое завершение"
        ],
        "coach_hint": "Зафиксируй выбор клиента, озвучь сроки готовности финальной версии и поблагодари за доверие."
    }
}


def get_next_stage(current_stage: str) -> str:
    """Get next stage in the sales cycle"""
    try:
        current_index = STAGES.index(current_stage)
        if current_index < len(STAGES) - 1:
            return STAGES[current_index + 1]
    except ValueError:
        pass
    return current_stage


async def init_master_path_session(manager_id: str, session_id: str) -> Dict[str, Any]:
    """
    Initialize a new master path training session.
    
    Returns:
        Initial response with coach greeting and first task
    """
    # Create session in dialog memory
    await start_session(manager_id, "master_path", session_id)
    
    # Coach introduction
    coach_intro = """Привет! 👋 
    
Это тренировка полного цикла сделки в проекте "На Счастье". 
Ты пройдёшь все этапы: от первого касания до финальной песни.

Я буду в роли твоего коуча — подскажу, что можно улучшить.
"Клиент" будет отвечать как живой человек.

**Твоя первая задача:** напиши тёплое приветствие клиенту. 
Представься, кратко расскажи о проекте и задай вопрос про получателя подарка."""
    
    # Save coach message
    await append_message(
        manager_id, "master_path", session_id,
        role="coach",
        content=coach_intro,
        stage="greeting"
    )
    
    return {
        "stage": "greeting",
        "coach_message": coach_intro,
        "client_reply": None,
        "status": "active"
    }


async def process_manager_turn(
    manager_id: str,
    session_id: str,
    manager_text: str
) -> Dict[str, Any]:
    """
    Process manager's message and generate client + coach responses.
    
    Args:
        manager_id: Manager identifier
        session_id: Session identifier
        manager_text: Manager's message
    
    Returns:
        Response with client reply, coach tip, and evaluation
    """
    # Get current session
    session = await get_session(manager_id, "master_path", session_id)
    if not session:
        raise ValueError("Session not found")
    
    current_stage = session.get("stage", "greeting")
    stage_info = STAGE_INFO.get(current_stage, {})
    
    # Save manager's message
    await append_message(
        manager_id, "master_path", session_id,
        role="manager",
        content=manager_text
    )
    
    # Evaluate manager's message
    evaluation = await evaluate_message(manager_text, current_stage)
    
    # Build context for client response
    conversation_history = []
    for msg in session.get("messages", [])[-5:]:  # Last 5 messages
        conversation_history.append({
            "role": msg["role"],
            "content": msg["content"]
        })
    
    # Add context about current stage
    stage_context = f"Этап сделки: {stage_info.get('description', current_stage)}. "
    
    conversation_history.append({
        "role": "user",
        "content": f"{stage_context}Менеджер написал: {manager_text}"
    })
    
    # Generate client response
    client_reply = await persona_chat("client", conversation_history)
    
    # Save client response
    await append_message(
        manager_id, "master_path", session_id,
        role="client",
        content=client_reply
    )
    
    # Generate coach tip based on evaluation
    coach_tip = await _generate_coach_tip(
        manager_text,
        current_stage,
        evaluation,
        stage_info
    )
    
    # Determine if we should move to next stage
    should_advance = evaluation["overall"] >= 6.5 and len(manager_text.split()) >= 15
    next_stage = get_next_stage(current_stage) if should_advance else current_stage
    
    # Save coach tip and update stage
    await append_message(
        manager_id, "master_path", session_id,
        role="coach",
        content=coach_tip,
        stage=next_stage,
        score=evaluation["scores"]
    )
    
    # Prepare response
    response = {
        "stage": next_stage,
        "previous_stage": current_stage,
        "client_reply": client_reply,
        "coach_tip": coach_tip,
        "score": evaluation["scores"],
        "overall_score": evaluation["overall"],
        "stage_advanced": should_advance
    }
    
    return response


async def _generate_coach_tip(
    manager_text: str,
    stage: str,
    evaluation: Dict,
    stage_info: Dict
) -> str:
    """Generate coach tip based on evaluation and stage"""
    
    overall = evaluation["overall"]
    scores = evaluation["scores"]
    
    # Build coach context
    criteria = stage_info.get("criteria", [])
    hint = stage_info.get("coach_hint", "")
    
    # Prepare messages for coach
    coach_messages = [
        {
            "role": "user",
            "content": f"""Менеджер на этапе "{stage}" написал: "{manager_text}"

Оценки: тепло={scores['warmth']}, вопросы={scores['questions']}, ясность={scores['clarity']}

Критерии этапа:
{chr(10).join('- ' + c for c in criteria)}

Подсказка: {hint}

Дай краткий совет (2-3 предложения), что улучшить или что хорошо."""
        }
    ]
    
    coach_tip = await persona_chat("coach", coach_messages)
    
    return coach_tip


async def get_session_snapshot(manager_id: str, session_id: str) -> Dict[str, Any]:
    """
    Get current session snapshot with history and state.
    
    Args:
        manager_id: Manager identifier
        session_id: Session identifier
    
    Returns:
        Session snapshot
    """
    session = await get_session(manager_id, "master_path", session_id)
    if not session:
        raise ValueError("Session not found")
    
    # Calculate stats
    messages = session.get("messages", [])
    manager_messages = [m for m in messages if m["role"] == "manager"]
    client_messages = [m for m in messages if m["role"] == "client"]
    
    current_stage = session.get("stage", "greeting")
    stage_index = STAGES.index(current_stage) if current_stage in STAGES else 0
    progress_percent = int((stage_index / len(STAGES)) * 100)
    
    return {
        "session_id": session_id,
        "manager_id": manager_id,
        "stage": current_stage,
        "stage_description": STAGE_INFO.get(current_stage, {}).get("description", ""),
        "progress_percent": progress_percent,
        "messages": messages,
        "stats": {
            "total_messages": len(messages),
            "manager_messages": len(manager_messages),
            "client_messages": len(client_messages),
        },
        "score": session.get("score", {}),
        "created_at": session.get("created_at"),
        "updated_at": session.get("updated_at")
    }
