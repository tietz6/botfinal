"""Photo Animation API Routes"""
import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.llm_gateway import get_llm_gateway

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/photo_animation/v1", tags=["photo-animation"])


class AnalyzeRequest(BaseModel):
    """Photo analysis request"""
    photo_description: str
    subject_info: Optional[str] = None
    animation_goal: Optional[str] = "general"


class PromptRequest(BaseModel):
    """Animation prompt generation request"""
    photo_description: str
    style: Optional[str] = "natural"
    actions: Optional[List[str]] = None


@router.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy", "module": "photo_animation"}


@router.post("/analyze")
async def analyze_photo(request: AnalyzeRequest):
    """
    Analyze photo and suggest animation approach.
    
    Provides recommendations on:
    - What emotions to emphasize
    - Best animation style
    - Technical considerations
    
    Args:
        request: Photo description and context
        
    Returns:
        Analysis with recommendations
    """
    try:
        llm = get_llm_gateway()
        
        system_prompt = """Ты — эксперт по оживлению фотографий.
Твоя задача: проанализировать описание фото и дать рекомендации.

Учитывай:
- Эмоциональный контекст (память, праздник, просто креатив)
- Технические возможности
- Желаемый эффект от анимации

Будь деликатным и профессиональным."""
        
        user_prompt = f"""Описание фото: {request.photo_description}

{f'Информация о человеке: {request.subject_info}' if request.subject_info else ''}

Цель анимации: {request.animation_goal}

Проанализируй фото и дай рекомендации:
1. Какие эмоции стоит подчеркнуть
2. Какой стиль анимации подойдёт
3. Какие движения будут естественны
4. Технические советы"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        analysis = await llm.llm_service.chat(messages, temperature=0.7, max_tokens=500)
        
        return {
            "success": True,
            "analysis": analysis,
            "recommended_style": _extract_style_from_analysis(analysis),
            "recommended_actions": ["улыбка", "моргание", "лёгкий поворот головы"]
        }
    except Exception as e:
        logger.error(f"Failed to analyze photo: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/prompt")
async def generate_prompt(request: PromptRequest):
    """
    Generate animation prompt for AI tools.
    
    Creates technical prompt for photo animation platforms
    like D-ID, Pika, Runway, etc.
    
    Args:
        request: Photo description and desired style/actions
        
    Returns:
        Formatted prompt for animation tool
    """
    try:
        llm = get_llm_gateway()
        
        actions_text = ", ".join(request.actions) if request.actions else "улыбка, моргание, естественные движения"
        
        system_prompt = """Ты создаёшь технические промты для AI-систем оживления фотографий.

Промт должен быть:
- Конкретным и техничным
- Описывать желаемые движения
- Учитывать стиль и настроение
- Подходить для D-ID, Pika, Runway"""
        
        user_prompt = f"""Фото: {request.photo_description}
Стиль: {request.style}
Желаемые действия: {actions_text}

Создай промт для системы оживления фото."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        prompt = await llm.llm_service.chat(messages, temperature=0.6, max_tokens=300)
        
        return {
            "success": True,
            "prompt": prompt,
            "style": request.style,
            "actions": request.actions or ["smile", "blink", "head_turn"],
            "platforms": ["d-id", "pika", "runway"]
        }
    except Exception as e:
        logger.error(f"Failed to generate prompt: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/styles")
async def get_animation_styles():
    """
    Get available animation styles.
    
    Returns:
        List of supported styles
    """
    return {
        "success": True,
        "styles": [
            {
                "id": "natural",
                "name": "Естественный",
                "description": "Реалистичные, мягкие движения"
            },
            {
                "id": "expressive",
                "name": "Выразительный",
                "description": "Более заметные эмоции и жесты"
            },
            {
                "id": "subtle",
                "name": "Деликатный",
                "description": "Минимальные, едва заметные движения"
            },
            {
                "id": "talking",
                "name": "Говорящий",
                "description": "Синхронизация с речью"
            }
        ]
    }


def _extract_style_from_analysis(analysis: str) -> str:
    """Extract recommended style from analysis text"""
    analysis_lower = analysis.lower()
    
    if "естественн" in analysis_lower or "реалист" in analysis_lower:
        return "natural"
    elif "выразительн" in analysis_lower or "ярк" in analysis_lower:
        return "expressive"
    elif "деликатн" in analysis_lower or "минимальн" in analysis_lower:
        return "subtle"
    elif "говор" in analysis_lower or "речь" in analysis_lower:
        return "talking"
    
    return "natural"
