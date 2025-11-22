"""Encyclopedia API Routes"""
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from core.encyclopedia_engine import get_encyclopedia_service
from core.auth.models import Role

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/encyclopedia/v1", tags=["encyclopedia"])


class TTSRequest(BaseModel):
    """Request for text-to-speech"""
    voice: Optional[str] = "default"


@router.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy", "module": "encyclopedia"}


@router.get("/pages")
async def get_pages(role: Optional[str] = Query(None, description="User role for filtering")):
    """
    Get list of available encyclopedia pages.
    
    Args:
        role: User role (manager, generator, admin) - filters pages by access
        
    Returns:
        List of available pages
    """
    try:
        service = get_encyclopedia_service()
        
        # Convert role string to Role enum
        user_role = None
        if role:
            try:
                user_role = Role(role)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid role: {role}")
        
        pages = await service.get_pages_list(user_role)
        
        return {
            "success": True,
            "total": len(pages),
            "pages": pages
        }
    except Exception as e:
        logger.error(f"Failed to get pages: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/page/{page_id}")
async def get_page(
    page_id: str,
    role: Optional[str] = Query(None, description="User role for access check")
):
    """
    Get full encyclopedia page by ID.
    
    Args:
        page_id: Page identifier
        role: User role for access check
        
    Returns:
        Full page with all content blocks
    """
    try:
        service = get_encyclopedia_service()
        
        # Convert role string to Role enum
        user_role = None
        if role:
            try:
                user_role = Role(role)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid role: {role}")
        
        page = await service.get_page(page_id, user_role)
        
        if not page:
            raise HTTPException(
                status_code=404,
                detail=f"Page '{page_id}' not found or access denied"
            )
        
        return {
            "success": True,
            "page": page.model_dump()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get page {page_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/page/{page_id}/tts")
async def generate_tts(page_id: str, request: TTSRequest = TTSRequest()):
    """
    Generate text-to-speech audio for encyclopedia page.
    
    Args:
        page_id: Page identifier
        request: TTS options
        
    Returns:
        Text for TTS or audio URL (depending on voice gateway availability)
    """
    try:
        service = get_encyclopedia_service()
        
        # Get text from page
        text = await service.get_page_text_for_tts(page_id)
        
        if not text:
            raise HTTPException(
                status_code=404,
                detail=f"Page '{page_id}' not found"
            )
        
        # For now, return the text
        # In future, integrate with core/voice_gateway/v1/tts
        return {
            "success": True,
            "page_id": page_id,
            "text_for_voice": text,
            "audio": None,
            "message": "TTS integration pending - text extracted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate TTS for page {page_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
