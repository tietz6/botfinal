"""Dialog Memory API Routes"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any

from . import (
    start_session,
    append_message,
    get_session,
    list_sessions,
    update_metadata
)

router = APIRouter(prefix="/dialog_memory/v1", tags=["dialog-memory"])


class StartSessionRequest(BaseModel):
    manager_id: str
    module: str
    session_id: str


class AppendMessageRequest(BaseModel):
    manager_id: str
    module: str
    session_id: str
    role: str
    content: str
    stage: Optional[str] = None
    score: Optional[Dict[str, Any]] = None


class UpdateMetadataRequest(BaseModel):
    manager_id: str
    module: str
    session_id: str
    metadata: Dict[str, Any]


@router.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy", "module": "dialog_memory"}


@router.post("/start")
async def api_start_session(request: StartSessionRequest):
    """Start a new dialog session"""
    try:
        session = await start_session(
            request.manager_id,
            request.module,
            request.session_id
        )
        return {"success": True, "session": session}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/append")
async def api_append_message(request: AppendMessageRequest):
    """Append message to session"""
    try:
        session = await append_message(
            request.manager_id,
            request.module,
            request.session_id,
            request.role,
            request.content,
            request.stage,
            request.score
        )
        return {"success": True, "session": session}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/get/{manager_id}/{module}/{session_id}")
async def api_get_session(manager_id: str, module: str, session_id: str):
    """Get session data"""
    try:
        session = await get_session(manager_id, module, session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        return {"success": True, "session": session}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list/{manager_id}")
async def api_list_sessions(manager_id: str, module: Optional[str] = None):
    """List all sessions for manager"""
    try:
        sessions = await list_sessions(manager_id, module)
        return {"success": True, "sessions": sessions, "count": len(sessions)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/metadata")
async def api_update_metadata(request: UpdateMetadataRequest):
    """Update session metadata"""
    try:
        session = await update_metadata(
            request.manager_id,
            request.module,
            request.session_id,
            request.metadata
        )
        return {"success": True, "session": session}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
