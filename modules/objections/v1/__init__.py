"""
Objections V1
Training for handling customer objections
"""
import random
from typing import Dict, Any
from modules.dialog_memory.v1 import start_session, append_message, get_session
from modules.deepseek_persona.v1 import persona_chat, evaluate_message

# Objection types
OBJECTION_TYPES = {
    "price": {
        "name": "Дорого",
        "initial_message": "Звучит интересно, но... это довольно дорого. Я не уверен, что готов столько платить.",
        "context": "Клиент считает цену высокой"
    },
    "distrust": {
        "name": "Недоверие",
        "initial_message": "Хм, я раньше не слышал о таком. Как я могу быть уверен, что это не обман?",
        "context": "Клиент не доверяет услуге"
    },
    "think": {
        "name": "Подумать",
        "initial_message": "Интересно, но мне нужно подумать. Можно я вам позже напишу?",
        "context": "Клиент хочет отложить решение"
    },
    "later": {
        "name": "Позже",
        "initial_message": "Сейчас не очень удобно. Может, через месяц-другой...",
        "context": "Клиент откладывает на потом"
    },
    "not_needed": {
        "name": "Не нужно",
        "initial_message": "Я подумал... наверное, это не для меня. Не уверен, что нам нужна песня.",
        "context": "Клиент сомневается в необходимости"
    }
}


async def init_objections_session(
    manager_id: str,
    session_id: str,
    objection_type: str = None
) -> Dict[str, Any]:
    """
    Initialize objections training session.
    
    Args:
        manager_id: Manager identifier
        session_id: Session identifier
        objection_type: Type of objection (random if not specified)
    
    Returns:
        Initial response with objection
    """
    # Select objection type
    if not objection_type or objection_type not in OBJECTION_TYPES:
        objection_type = random.choice(list(OBJECTION_TYPES.keys()))
    
    objection = OBJECTION_TYPES[objection_type]
    
    # Create session
    await start_session(manager_id, "objections", session_id)
    
    # Coach introduction
    coach_intro = f"""🎯 **Тренировка: Отработка возражений**

Тип возражения: **{objection["name"]}**

Твоя задача — отработать возражение мягко и эмпатично.

**Критерии:**
✓ Проявить эмпатию (понять чувства клиента)
✓ Дать развёрнутый ответ (не односложный)
✓ Задать вопрос в конце (поддержать диалог)

Не дави на клиента — помоги ему самому принять решение.

Клиент сейчас напишет возражение, а ты попробуй его отработать."""
    
    # Save coach message
    await append_message(
        manager_id, "objections", session_id,
        role="coach",
        content=coach_intro,
        stage="active"
    )
    
    # Client objection
    await append_message(
        manager_id, "objections", session_id,
        role="client",
        content=objection["initial_message"]
    )
    
    # Store objection type in metadata
    session = await get_session(manager_id, "objections", session_id)
    from modules.dialog_memory.v1 import update_metadata
    await update_metadata(
        manager_id, "objections", session_id,
        {"objection_type": objection_type, "objection_name": objection["name"]}
    )
    
    return {
        "objection_type": objection_type,
        "objection_name": objection["name"],
        "coach_message": coach_intro,
        "client_message": objection["initial_message"],
        "status": "active"
    }


async def process_objection_turn(
    manager_id: str,
    session_id: str,
    manager_text: str
) -> Dict[str, Any]:
    """
    Process manager's response to objection.
    
    Args:
        manager_id: Manager identifier
        session_id: Session identifier
        manager_text: Manager's response
    
    Returns:
        Client reaction and coach feedback
    """
    # Get session
    session = await get_session(manager_id, "objections", session_id)
    if not session:
        raise ValueError("Session not found")
    
    objection_type = session.get("metadata", {}).get("objection_type", "price")
    
    # Save manager message
    await append_message(
        manager_id, "objections", session_id,
        role="manager",
        content=manager_text
    )
    
    # Evaluate response
    evaluation = await _evaluate_objection_response(manager_text)
    
    # Build conversation context
    conversation_history = []
    for msg in session.get("messages", [])[-6:]:
        if msg["role"] != "coach":  # Exclude coach messages from client context
            conversation_history.append({
                "role": msg["role"],
                "content": msg["content"]
            })
    
    # Add context
    objection_context = OBJECTION_TYPES.get(objection_type, {}).get("context", "")
    conversation_history.append({
        "role": "user",
        "content": f"Контекст: {objection_context}. Менеджер ответил: {manager_text}"
    })
    
    # Generate client reaction
    client_reply = await persona_chat("client", conversation_history)
    
    # Save client reply
    await append_message(
        manager_id, "objections", session_id,
        role="client",
        content=client_reply
    )
    
    # Generate coach feedback
    coach_feedback = await _generate_objection_feedback(
        manager_text,
        evaluation,
        objection_type
    )
    
    # Save coach feedback
    await append_message(
        manager_id, "objections", session_id,
        role="coach",
        content=coach_feedback,
        score=evaluation
    )
    
    return {
        "client_reply": client_reply,
        "coach_feedback": coach_feedback,
        "evaluation": evaluation,
        "objection_type": objection_type
    }


async def _evaluate_objection_response(manager_text: str) -> Dict[str, Any]:
    """Evaluate manager's objection handling"""
    
    scores = {
        "empathy": 0,
        "length": 0,
        "question": 0
    }
    
    msg_lower = manager_text.lower()
    
    # Empathy check
    empathy_words = [
        "понимаю", "понятно", "согласен", "да, действительно",
        "вижу", "слышу", "чувствую", "важно"
    ]
    if any(word in msg_lower for word in empathy_words):
        scores["empathy"] = 8
    else:
        scores["empathy"] = 3
    
    # Length check
    word_count = len(manager_text.split())
    if word_count >= 20:
        scores["length"] = 8
    elif word_count >= 10:
        scores["length"] = 6
    else:
        scores["length"] = 3
    
    # Question check
    if "?" in manager_text:
        scores["question"] = 10
    else:
        scores["question"] = 2
    
    overall = sum(scores.values()) / len(scores)
    
    return {
        "scores": scores,
        "overall": round(overall, 1),
        "passed": overall >= 6
    }


async def _generate_objection_feedback(
    manager_text: str,
    evaluation: Dict,
    objection_type: str
) -> str:
    """Generate coach feedback on objection handling"""
    
    scores = evaluation["scores"]
    overall = evaluation["overall"]
    
    # Prepare feedback prompt
    objection_info = OBJECTION_TYPES.get(objection_type, {})
    
    feedback_prompt = f"""Менеджер отрабатывает возражение "{objection_info.get('name', objection_type)}".

Его ответ: "{manager_text}"

Оценки: эмпатия={scores['empathy']}, длина={scores['length']}, вопрос={scores['question']}

Дай краткую обратную связь (2-3 предложения):
- Что получилось хорошо
- Что улучшить для мягкой отработки возражения без давления"""
    
    coach_messages = [{"role": "user", "content": feedback_prompt}]
    feedback = await persona_chat("coach", coach_messages)
    
    return feedback


async def get_objections_snapshot(manager_id: str, session_id: str) -> Dict[str, Any]:
    """Get objections session snapshot"""
    
    session = await get_session(manager_id, "objections", session_id)
    if not session:
        raise ValueError("Session not found")
    
    messages = session.get("messages", [])
    manager_messages = [m for m in messages if m["role"] == "manager"]
    
    return {
        "session_id": session_id,
        "manager_id": manager_id,
        "objection_type": session.get("metadata", {}).get("objection_type"),
        "objection_name": session.get("metadata", {}).get("objection_name"),
        "messages": messages,
        "stats": {
            "total_turns": len(manager_messages),
            "total_messages": len(messages)
        },
        "score": session.get("score", {}),
        "created_at": session.get("created_at"),
        "updated_at": session.get("updated_at")
    }
