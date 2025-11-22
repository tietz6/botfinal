"""DeepSeek Persona API Routes"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional

from . import persona_chat, stylize, generate_greeting, evaluate_message

router = APIRouter(prefix="/deepseek_persona/v1", tags=["persona"])


class PersonaChatRequest(BaseModel):
    role: str  # "coach" or "client"
    messages: List[Dict[str, str]]


class StylizeRequest(BaseModel):
    text: str
    role: str


class GreetingRequest(BaseModel):
    context: Optional[str] = ""


class EvaluateRequest(BaseModel):
    manager_message: str
    stage: str
    context: Optional[str] = ""


@router.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy", "module": "deepseek_persona"}


@router.post("/chat")
async def api_persona_chat(request: PersonaChatRequest):
    """Generate response in brand voice"""
    try:
        if request.role not in ["coach", "client"]:
            raise HTTPException(
                status_code=400,
                detail="Role must be 'coach' or 'client'"
            )
        
        response = await persona_chat(request.role, request.messages)
        return {"success": True, "response": response, "role": request.role}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stylize")
async def api_stylize(request: StylizeRequest):
    """Apply brand style to text"""
    try:
        styled_text = stylize(request.text, request.role)
        return {"success": True, "original": request.text, "styled": styled_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/greeting")
async def api_generate_greeting(request: GreetingRequest):
    """Generate greeting message"""
    try:
        greeting = await generate_greeting(request.context)
        return {"success": True, "greeting": greeting}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/evaluate")
async def api_evaluate_message(request: EvaluateRequest):
    """Evaluate manager's message quality"""
    try:
        evaluation = await evaluate_message(
            request.manager_message,
            request.stage,
            request.context
        )
        return {"success": True, "evaluation": evaluation}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
