"""Song Generator API Routes"""
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.llm_gateway import get_llm_gateway

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/song_generator/v1", tags=["song-generator"])


class GenerateRequest(BaseModel):
    """Song generation request"""
    story: str
    style: Optional[str] = "romantic"
    language: Optional[str] = "ru"
    length: Optional[str] = "full"
    from_person: Optional[str] = "автор"
    to_person: Optional[str] = "получатель"
    mood: Optional[str] = "love"


@router.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy", "module": "song_generator"}


@router.post("/generate")
async def generate_song(request: GenerateRequest):
    """
    Generate song text based on client's story.
    
    Uses LLM to create personalized song lyrics that capture
    the emotional essence of the client's story.
    
    Args:
        request: Song generation parameters including:
            - story: Client's story and context
            - style: Music style (romantic, upbeat, rock, etc.)
            - language: Language code (ru, en, etc.)
            - length: Song length (short, full, extended)
            - from_person: Who is giving the gift
            - to_person: Who is receiving
            - mood: Emotional mood (love, support, celebration, etc.)
            
    Returns:
        Generated song with structure and metadata
    """
    try:
        llm = get_llm_gateway()
        
        # Generate song using LLM gateway
        result = await llm.generate_song_text({
            "story": request.story,
            "style": request.style,
            "language": request.language,
            "length": request.length,
            "from_person": request.from_person,
            "to_person": request.to_person,
            "mood": request.mood
        })
        
        return {
            "success": True,
            "text": result["text"],
            "structure": result["structure"],
            "prompt_for_cover": result["prompt_for_cover"],
            "notes_for_voice": result["notes_for_voice"],
            "metadata": {
                "style": request.style,
                "language": request.language,
                "mood": request.mood,
                "from": request.from_person,
                "to": request.to_person
            }
        }
    except Exception as e:
        logger.error(f"Failed to generate song: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/styles")
async def get_available_styles():
    """
    Get list of available music styles.
    
    Returns:
        List of supported styles with descriptions
    """
    return {
        "success": True,
        "styles": [
            {
                "id": "romantic",
                "name": "Романтическая баллада",
                "description": "Нежная, лирическая композиция для любовных историй"
            },
            {
                "id": "upbeat",
                "name": "Весёлый поп",
                "description": "Энергичная, позитивная песня для друзей и праздников"
            },
            {
                "id": "rock",
                "name": "Рок",
                "description": "Мощная, драйвовая композиция для ярких характеров"
            },
            {
                "id": "acoustic",
                "name": "Акустика",
                "description": "Интимная, камерная песня с гитарой"
            },
            {
                "id": "rap",
                "name": "Рэп",
                "description": "Ритмичный, современный стиль с речитативом"
            },
            {
                "id": "jazz",
                "name": "Джаз",
                "description": "Изысканная, утончённая композиция"
            }
        ]
    }


@router.get("/moods")
async def get_available_moods():
    """
    Get list of available emotional moods.
    
    Returns:
        List of supported moods with descriptions
    """
    return {
        "success": True,
        "moods": [
            {
                "id": "love",
                "name": "Любовь",
                "description": "Нежные чувства, романтика"
            },
            {
                "id": "support",
                "name": "Поддержка",
                "description": "Слова ободрения и веры"
            },
            {
                "id": "celebration",
                "name": "Празднование",
                "description": "Радость, веселье, торжество"
            },
            {
                "id": "gratitude",
                "name": "Благодарность",
                "description": "Спасибо за всё, что ты сделал"
            },
            {
                "id": "nostalgia",
                "name": "Ностальгия",
                "description": "Воспоминания о прошлом"
            },
            {
                "id": "hope",
                "name": "Надежда",
                "description": "Вера в будущее"
            }
        ]
    }
