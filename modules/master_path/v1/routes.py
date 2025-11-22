"""Master Path API Routes"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from . import (
    init_master_path_session,
    process_manager_turn,
    get_session_snapshot
)

router = APIRouter(prefix="/master_path", tags=["master-path"])


class TurnRequest(BaseModel):
    text: str


@router.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy", "module": "master_path"}


@router.post("/start/{session_id}")
async def start_session(session_id: str, manager_id: str = "default"):
    """
    Start a new master path training session.
    
    Args:
        session_id: Unique session identifier
        manager_id: Manager identifier (default: "default")
    
    Returns:
        Initial coach message and task
    """
    try:
        result = await init_master_path_session(manager_id, session_id)
        return {"success": True, **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/turn/{session_id}")
async def manager_turn(session_id: str, request: TurnRequest, manager_id: str = "default"):
    """
    Process manager's turn in the conversation.
    
    Args:
        session_id: Session identifier
        request: Manager's message
        manager_id: Manager identifier (default: "default")
    
    Returns:
        Client reply, coach tip, and evaluation
    """
    try:
        result = await process_manager_turn(manager_id, session_id, request.text)
        return {"success": True, **result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/snapshot/{session_id}")
async def session_snapshot(session_id: str, manager_id: str = "default"):
    """
    Get current session state and history.
    
    Args:
        session_id: Session identifier
        manager_id: Manager identifier (default: "default")
    
    Returns:
        Full session snapshot
    """
    try:
        snapshot = await get_session_snapshot(manager_id, session_id)
        return {"success": True, **snapshot}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
