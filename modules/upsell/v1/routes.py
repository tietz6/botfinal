"""Upsell API Routes"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from . import (
    init_upsell_session,
    process_upsell_turn,
    get_upsell_snapshot
)

router = APIRouter(prefix="/upsell", tags=["upsell"])


class StartRequest(BaseModel):
    scenario: Optional[str] = None


class TurnRequest(BaseModel):
    text: str


@router.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy", "module": "upsell"}


@router.post("/start/{session_id}")
async def start_session(
    session_id: str,
    request: StartRequest = StartRequest(),
    manager_id: str = "default"
):
    """
    Start upsell training session.
    
    Args:
        session_id: Session identifier
        request: Optional scenario type
        manager_id: Manager identifier
    
    Returns:
        Initial scenario and instructions
    """
    try:
        result = await init_upsell_session(
            manager_id,
            session_id,
            request.scenario
        )
        return {"success": True, **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/turn/{session_id}")
async def manager_turn(
    session_id: str,
    request: TurnRequest,
    manager_id: str = "default"
):
    """
    Process manager's upsell attempt.
    
    Args:
        session_id: Session identifier
        request: Manager's message
        manager_id: Manager identifier
    
    Returns:
        Client reaction and coach feedback
    """
    try:
        result = await process_upsell_turn(manager_id, session_id, request.text)
        return {"success": True, **result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/snapshot/{session_id}")
async def session_snapshot(session_id: str, manager_id: str = "default"):
    """
    Get upsell session snapshot.
    
    Args:
        session_id: Session identifier
        manager_id: Manager identifier
    
    Returns:
        Session snapshot
    """
    try:
        snapshot = await get_upsell_snapshot(manager_id, session_id)
        return {"success": True, **snapshot}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
