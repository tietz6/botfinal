"""
Dialog Memory V1
Stores and retrieves training session history and state
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from core.state import get_state, set_state, list_keys


def _make_key(manager_id: str, module: str, session_id: str) -> str:
    """Generate storage key for dialog session"""
    return f"dialog:{manager_id}:{module}:{session_id}"


async def start_session(manager_id: str, module: str, session_id: str) -> Dict[str, Any]:
    """
    Create a new dialog session.
    
    Args:
        manager_id: Manager/user identifier
        module: Training module name (master_path, objections, etc)
        session_id: Unique session identifier
    
    Returns:
        Session data dict
    """
    key = _make_key(manager_id, module, session_id)
    
    session_data = {
        "manager_id": manager_id,
        "module": module,
        "session_id": session_id,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "messages": [],
        "stage": "init",
        "score": {},
        "metadata": {}
    }
    
    await set_state(key, session_data)
    return session_data


async def append_message(
    manager_id: str,
    module: str,
    session_id: str,
    role: str,
    content: str,
    stage: Optional[str] = None,
    score: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Append a message to dialog session history.
    
    Args:
        manager_id: Manager identifier
        module: Module name
        session_id: Session identifier
        role: Message role (manager, client, coach, system)
        content: Message content
        stage: Optional stage update
        score: Optional score update
    
    Returns:
        Updated session data
    """
    key = _make_key(manager_id, module, session_id)
    session_data = await get_state(key)
    
    if not session_data:
        # Create session if it doesn't exist
        session_data = await start_session(manager_id, module, session_id)
    
    # Append message
    message = {
        "role": role,
        "content": content,
        "timestamp": datetime.utcnow().isoformat()
    }
    session_data["messages"].append(message)
    
    # Update stage if provided
    if stage:
        session_data["stage"] = stage
    
    # Update score if provided
    if score:
        session_data["score"].update(score)
    
    # Update timestamp
    session_data["updated_at"] = datetime.utcnow().isoformat()
    
    await set_state(key, session_data)
    return session_data


async def get_session(manager_id: str, module: str, session_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve dialog session data.
    
    Args:
        manager_id: Manager identifier
        module: Module name
        session_id: Session identifier
    
    Returns:
        Session data dict or None
    """
    key = _make_key(manager_id, module, session_id)
    return await get_state(key)


async def list_sessions(manager_id: str, module: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List all sessions for a manager.
    
    Args:
        manager_id: Manager identifier
        module: Optional module filter
    
    Returns:
        List of session data dicts
    """
    if module:
        prefix = f"dialog:{manager_id}:{module}:"
    else:
        prefix = f"dialog:{manager_id}:"
    
    keys = await list_keys(prefix)
    sessions = []
    
    for key in keys:
        session_data = await get_state(key)
        if session_data:
            sessions.append(session_data)
    
    return sessions


async def update_metadata(
    manager_id: str,
    module: str,
    session_id: str,
    metadata: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Update session metadata.
    
    Args:
        manager_id: Manager identifier
        module: Module name
        session_id: Session identifier
        metadata: Metadata dict to merge
    
    Returns:
        Updated session data
    """
    key = _make_key(manager_id, module, session_id)
    session_data = await get_state(key)
    
    if not session_data:
        session_data = await start_session(manager_id, module, session_id)
    
    session_data["metadata"].update(metadata)
    session_data["updated_at"] = datetime.utcnow().isoformat()
    
    await set_state(key, session_data)
    return session_data
