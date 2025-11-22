"""
Voice API V1 Routes
Provides voice processing endpoints for ASR, TTS, and chat
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Response
from pydantic import BaseModel
from typing import List, Dict, Optional

from core.voice_gateway.v1.pipeline import get_pipeline
from core.voice_gateway.v1.asr import get_asr_service
from core.voice_gateway.v1.tts import get_tts_service
from core.voice_gateway.v1.llm import get_llm_service

router = APIRouter(prefix="/voice/v1", tags=["voice"])


class TextChatRequest(BaseModel):
    """Text chat request"""
    messages: List[Dict[str, str]]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 500


class TextChatResponse(BaseModel):
    """Text chat response"""
    response: str
    success: bool = True


class TTSRequest(BaseModel):
    """Text-to-speech request"""
    text: str
    voice: Optional[str] = "default"
    speed: Optional[float] = 1.0


class ASRResponse(BaseModel):
    """ASR response"""
    text: str
    success: bool = True


@router.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "voice-gateway",
        "version": "1.0"
    }


@router.post("/asr", response_model=ASRResponse)
async def transcribe_audio(audio: UploadFile = File(...)):
    """
    Transcribe audio to text (ASR).
    
    Args:
        audio: Audio file (OGG, WAV, MP3)
    
    Returns:
        Transcribed text
    """
    try:
        # Read audio data
        audio_data = await audio.read()
        
        # Get ASR service
        asr = get_asr_service()
        
        # Transcribe
        text = await asr.transcribe(audio_data)
        
        if text.startswith("["):
            # Error message from ASR
            raise HTTPException(status_code=500, detail=text)
        
        return ASRResponse(text=text, success=True)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ASR failed: {str(e)}")


@router.post("/tts")
async def synthesize_speech(request: TTSRequest):
    """
    Synthesize text to speech (TTS).
    
    Args:
        request: TTS request with text, voice, and speed
    
    Returns:
        Audio file (OGG format)
    """
    try:
        # Get TTS service
        tts = get_tts_service()
        
        # Synthesize
        audio_data = await tts.synthesize(
            text=request.text,
            voice=request.voice,
            speed=request.speed
        )
        
        if audio_data is None:
            raise HTTPException(status_code=500, detail="TTS synthesis failed")
        
        # Return audio as response
        return Response(
            content=audio_data,
            media_type="audio/ogg",
            headers={
                "Content-Disposition": "attachment; filename=speech.ogg"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS failed: {str(e)}")


@router.post("/chat/text", response_model=TextChatResponse)
async def text_chat(request: TextChatRequest):
    """
    Text-based chat with LLM.
    
    Args:
        request: Chat request with messages
    
    Returns:
        LLM response
    """
    try:
        # Get LLM service
        llm = get_llm_service()
        
        # Generate response
        response = await llm.chat(
            messages=request.messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        return TextChatResponse(response=response, success=True)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


@router.post("/chat/voice")
async def voice_chat(
    audio: UploadFile = File(...),
    system_prompt: Optional[str] = ""
):
    """
    Voice-to-voice chat (ASR -> LLM -> TTS).
    
    Args:
        audio: Input audio file
        system_prompt: Optional system prompt for LLM
    
    Returns:
        Response audio file (OGG format)
    """
    try:
        # Read audio data
        audio_data = await audio.read()
        
        # Get pipeline
        pipeline = get_pipeline()
        
        # Process voice-to-voice
        response_audio = await pipeline.voice_to_voice(
            audio_data=audio_data,
            system_prompt=system_prompt
        )
        
        if response_audio is None:
            raise HTTPException(status_code=500, detail="Voice processing failed")
        
        # Return audio as response
        return Response(
            content=response_audio,
            media_type="audio/ogg",
            headers={
                "Content-Disposition": "attachment; filename=response.ogg"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Voice chat failed: {str(e)}")
