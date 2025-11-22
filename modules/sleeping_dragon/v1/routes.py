"""
Sleeping Dragon API Routes
Provides dialogue analysis and feedback
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict

from . import analyze_dialogue

router = APIRouter(prefix="/sleeping_dragon/v1", tags=["sleeping-dragon"])


class AnalyzeRequest(BaseModel):
    """Dialogue analysis request"""
    history: List[Dict[str, str]]
    reply: str


class AnalyzeResponse(BaseModel):
    """Dialogue analysis response"""
    score: float
    scores: Dict[str, float]
    issues: List[str]
    advice: str
    success: bool = True


@router.get("/health")
async def health():
    """Health check"""
    return {
        "status": "healthy",
        "module": "sleeping_dragon",
        "description": "Dialogue analysis and feedback"
    }


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_dialogue_endpoint(request: AnalyzeRequest):
    """
    Analyze manager's dialogue quality.
    
    Args:
        request: Analysis request with conversation history and manager's reply
    
    Returns:
        Analysis with scores (0-10), identified issues, and warm advice
    """
    try:
        result = await analyze_dialogue(
            history=request.history,
            manager_reply=request.reply
        )
        
        return AnalyzeResponse(
            score=result.get("total_score", 0),
            scores=result.get("scores", {}),
            issues=result.get("issues", []),
            advice=result.get("advice", ""),
            success=True
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Dialogue analysis failed: {str(e)}"
        )
