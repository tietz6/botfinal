"""Exam API Routes"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from . import (
    init_exam_session,
    process_exam_turn,
    get_exam_result,
    get_exam_snapshot
)

router = APIRouter(prefix="/exam", tags=["exam"])


class StartRequest(BaseModel):
    scenario_type: Optional[str] = None


class TurnRequest(BaseModel):
    text: str


@router.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy", "module": "exam"}


@router.post("/start/{session_id}")
async def start_exam(
    session_id: str,
    request: StartRequest = StartRequest(),
    manager_id: str = "default"
):
    """
    Start exam session.
    
    Args:
        session_id: Session identifier
        request: Optional scenario type
        manager_id: Manager identifier
    
    Returns:
        Exam instructions
    """
    try:
        result = await init_exam_session(
            manager_id,
            session_id,
            request.scenario_type
        )
        return {"success": True, **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/turn/{session_id}")
async def exam_turn(
    session_id: str,
    request: TurnRequest,
    manager_id: str = "default"
):
    """
    Process exam turn.
    
    Args:
        session_id: Session identifier
        request: Manager's response
        manager_id: Manager identifier
    
    Returns:
        Client response and round evaluation
    """
    try:
        result = await process_exam_turn(manager_id, session_id, request.text)
        return {"success": True, **result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/result/{session_id}")
async def exam_result(session_id: str, manager_id: str = "default"):
    """
    Get final exam result.
    
    Args:
        session_id: Session identifier
        manager_id: Manager identifier
    
    Returns:
        Final score and verdict
    """
    try:
        result = await get_exam_result(manager_id, session_id)
        return {"success": True, **result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/snapshot/{session_id}")
async def exam_snapshot(session_id: str, manager_id: str = "default"):
    """
    Get exam session snapshot.
    
    Args:
        session_id: Session identifier
        manager_id: Manager identifier
    
    Returns:
        Session snapshot
    """
    try:
        snapshot = await get_exam_snapshot(manager_id, session_id)
        return {"success": True, **snapshot}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
