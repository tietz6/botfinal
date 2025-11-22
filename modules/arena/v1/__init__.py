"""
Arena V1
Free-form dialog practice with different client types
"""
import random
from typing import Dict, Any, Optional
from modules.dialog_memory.v1 import start_session, append_message, get_session
from modules.deepseek_persona.v1 import persona_chat

# Client personality types
CLIENT_TYPES = {
    "calm": {
        "name": "Спокойный",
        "description": "Вдумчивый клиент, задаёт много вопросов, принимает решения медленно"
    },
    "doubtful": {
        "name": "Сомневающийся",
        "description": "Клиент с множеством сомнений, нужно много эмпатии и терпения"
    },
    "price_focused": {
        "name": "Ценовой",
        "description": "Клиент очень чувствителен к цене, ищет скидки и выгоду"
    },
    "enthusiastic": {
        "name": "Восторженный",
        "description": "Клиент в восторге от идеи, но может потерять интерес если затянуть"
    },
    "busy": {
        "name": "Занятой",
        "description": "Клиент торопится, хочет быстрых ответов и конкретики"
    }
}


async def init_arena_session(
    manager_id: str,
    session_id: str,
    client_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Initialize arena training session.
    
    Args:
        manager_id: Manager identifier
        session_id: Session identifier
        client_type: Client personality type (random if not specified)
    
    Returns:
        Initial response
    """
    # Select client type
    if not client_type or client_type not in CLIENT_TYPES:
        client_type = random.choice(list(CLIENT_TYPES.keys()))
    
    client_info = CLIENT_TYPES[client_type]
    
    # Create session
    await start_session(manager_id, "arena", session_id)
    
    # Coach introduction
    coach_intro = f"""🎪 **Арена свободных диалогов**

Тип клиента: **{client_info["name"]}**
{client_info["description"]}

Это свободная практика. Веди диалог естественно, адаптируйся под клиента.

Я буду давать короткий анализ после каждого твоего сообщения.

Начинай диалог с приветствия!"""
    
    # Save coach message
    await append_message(
        manager_id, "arena", session_id,
        role="coach",
        content=coach_intro,
        stage="active"
    )
    
    # Store client type in metadata
    from modules.dialog_memory.v1 import update_metadata
    await update_metadata(
        manager_id, "arena", session_id,
        {
            "client_type": client_type,
            "client_name": client_info["name"],
            "client_description": client_info["description"]
        }
    )
    
    return {
        "client_type": client_type,
        "client_name": client_info["name"],
        "coach_message": coach_intro,
        "status": "active"
    }


async def process_arena_turn(
    manager_id: str,
    session_id: str,
    manager_text: str
) -> Dict[str, Any]:
    """
    Process manager's turn in arena.
    
    Args:
        manager_id: Manager identifier
        session_id: Session identifier
        manager_text: Manager's message
    
    Returns:
        Client response and coach analysis
    """
    # Get session
    session = await get_session(manager_id, "arena", session_id)
    if not session:
        raise ValueError("Session not found")
    
    client_type = session.get("metadata", {}).get("client_type", "calm")
    client_description = session.get("metadata", {}).get("client_description", "")
    
    # Save manager message
    await append_message(
        manager_id, "arena", session_id,
        role="manager",
        content=manager_text
    )
    
    # Build conversation context with client personality
    conversation_history = []
    for msg in session.get("messages", [])[-8:]:
        if msg["role"] != "coach":
            conversation_history.append({
                "role": msg["role"],
                "content": msg["content"]
            })
    
    # Add personality context
    personality_context = f"Ты - {client_description}. Менеджер написал: {manager_text}"
    conversation_history.append({
        "role": "user",
        "content": personality_context
    })
    
    # Generate client response
    client_reply = await persona_chat("client", conversation_history)
    
    # Save client reply
    await append_message(
        manager_id, "arena", session_id,
        role="client",
        content=client_reply
    )
    
    # Generate coach analysis
    coach_analysis = await _generate_arena_analysis(
        manager_text,
        client_type,
        len(session.get("messages", []))
    )
    
    # Save coach analysis
    await append_message(
        manager_id, "arena", session_id,
        role="coach",
        content=coach_analysis
    )
    
    return {
        "client_reply": client_reply,
        "coach_analysis": coach_analysis,
        "client_type": client_type
    }


async def _generate_arena_analysis(
    manager_text: str,
    client_type: str,
    message_count: int
) -> str:
    """Generate brief coach analysis for arena"""
    
    client_info = CLIENT_TYPES.get(client_type, {})
    
    analysis_prompt = f"""Менеджер общается с клиентом типа "{client_info.get('name', '')}" ({client_info.get('description', '')}).

Сообщение менеджера: "{manager_text}"

Это {message_count // 2 + 1}-й ход диалога.

Дай очень краткий анализ (1-2 предложения): что хорошо или что стоит учесть с таким типом клиента."""
    
    coach_messages = [{"role": "user", "content": analysis_prompt}]
    analysis = await persona_chat("coach", coach_messages)
    
    return analysis


async def get_arena_snapshot(manager_id: str, session_id: str) -> Dict[str, Any]:
    """Get arena session snapshot"""
    
    session = await get_session(manager_id, "arena", session_id)
    if not session:
        raise ValueError("Session not found")
    
    messages = session.get("messages", [])
    manager_messages = [m for m in messages if m["role"] == "manager"]
    client_messages = [m for m in messages if m["role"] == "client"]
    
    metadata = session.get("metadata", {})
    
    return {
        "session_id": session_id,
        "manager_id": manager_id,
        "client_type": metadata.get("client_type"),
        "client_name": metadata.get("client_name"),
        "messages": messages,
        "stats": {
            "total_turns": len(manager_messages),
            "manager_messages": len(manager_messages),
            "client_messages": len(client_messages)
        },
        "created_at": session.get("created_at"),
        "updated_at": session.get("updated_at")
    }
