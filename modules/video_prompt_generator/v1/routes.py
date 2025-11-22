"""Video Prompt Generator API Routes"""
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.llm_gateway import get_llm_gateway

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/video_prompt_generator/v1", tags=["video-prompts"])


class FromSongRequest(BaseModel):
    """Generate video prompts from song"""
    song_text: str
    audio_duration_sec: int = 120
    platform: Optional[str] = "sora"
    chunk_duration_sec: Optional[int] = 5


@router.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy", "module": "video_prompt_generator"}


@router.post("/from_song")
async def generate_from_song(request: FromSongRequest):
    """
    Generate video prompt timeline from song text.
    
    Creates a sequence of visual prompts synchronized with song,
    suitable for AI video generation platforms like Sora, VEO, Pika, Runway.
    
    Args:
        request: Parameters including:
            - song_text: Full lyrics
            - audio_duration_sec: Total duration
            - platform: Target platform
            - chunk_duration_sec: Duration per scene
            
    Returns:
        Timeline with prompts for each scene
    """
    try:
        llm = get_llm_gateway()
        
        result = await llm.generate_video_prompts({
            "song_text": request.song_text,
            "audio_duration_sec": request.audio_duration_sec,
            "platform": request.platform,
            "chunk_duration_sec": request.chunk_duration_sec
        })
        
        return {
            "success": True,
            "total_chunks": result["total_chunks"],
            "timeline": result["timeline"],
            "global_style": result["global_style"],
            "platform": request.platform,
            "total_duration_sec": request.audio_duration_sec
        }
    except Exception as e:
        logger.error(f"Failed to generate video prompts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/platforms")
async def get_platforms():
    """
    Get list of supported video generation platforms.
    
    Returns:
        List of platforms with their characteristics
    """
    return {
        "success": True,
        "platforms": [
            {
                "id": "sora",
                "name": "OpenAI Sora",
                "description": "High-quality cinematic video generation",
                "recommended_chunk_sec": 5
            },
            {
                "id": "veo",
                "name": "Google VEO",
                "description": "Fast, realistic video generation",
                "recommended_chunk_sec": 5
            },
            {
                "id": "pika",
                "name": "Pika Labs",
                "description": "Creative, artistic video generation",
                "recommended_chunk_sec": 3
            },
            {
                "id": "runway",
                "name": "Runway Gen-2",
                "description": "Professional video editing and generation",
                "recommended_chunk_sec": 4
            }
        ]
    }


@router.get("/styles")
async def get_video_styles():
    """
    Get list of available visual styles.
    
    Returns:
        List of style presets
    """
    return {
        "success": True,
        "styles": [
            {
                "id": "cinematic",
                "name": "Кинематографичный",
                "description": "Как в фильмах: драматическое освещение, глубина кадра"
            },
            {
                "id": "anime",
                "name": "Аниме",
                "description": "Японская анимация, выразительные персонажи"
            },
            {
                "id": "disney",
                "name": "Disney/Pixar",
                "description": "Мультяшный, уютный, семейный стиль"
            },
            {
                "id": "minimalist",
                "name": "Минимализм",
                "description": "Простые формы, концептуальная графика"
            },
            {
                "id": "watercolor",
                "name": "Акварель",
                "description": "Мягкие, лирические визуалы"
            },
            {
                "id": "realistic",
                "name": "Реалистичный",
                "description": "Фотореалистичное изображение"
            }
        ]
    }
