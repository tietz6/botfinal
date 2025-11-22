"""
ASR Service - Automatic Speech Recognition
"""
import os
import logging
import httpx
from typing import Union

logger = logging.getLogger(__name__)


class ASRService:
    """Automatic Speech Recognition service"""
    
    def __init__(self):
        self.api_key = os.getenv("VOICE_API_KEY", "")
        self.api_base_url = os.getenv("VOICE_API_BASE_URL", "https://example.com/voice-api")
        self.asr_endpoint = f"{self.api_base_url}/asr"
        
        if not self.api_key:
            logger.warning("VOICE_API_KEY not set, ASR service may not work properly")
    
    async def transcribe(self, audio_data: bytes, audio_format: str = "ogg") -> str:
        """
        Transcribe audio to text.
        
        Args:
            audio_data: Audio file bytes
            audio_format: Audio format (ogg, wav, mp3)
        
        Returns:
            Transcribed text
        """
        if not self.api_key:
            logger.error("VOICE_API_KEY not configured")
            return "[Не удалось распознать речь: API ключ не настроен]"
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                # Prepare multipart form data
                files = {
                    "audio": (f"audio.{audio_format}", audio_data, f"audio/{audio_format}")
                }
                headers = {
                    "Authorization": f"Bearer {self.api_key}"
                }
                
                response = await client.post(
                    self.asr_endpoint,
                    files=files,
                    headers=headers
                )
                
                response.raise_for_status()
                data = response.json()
                
                # Extract transcribed text from response
                if "text" in data:
                    return data["text"]
                elif "transcription" in data:
                    return data["transcription"]
                elif "result" in data:
                    return data["result"]
                else:
                    logger.error(f"Unexpected ASR response format: {data}")
                    return "[Не удалось распознать речь: неверный формат ответа]"
                    
        except httpx.HTTPStatusError as e:
            logger.error(f"ASR API HTTP error: {e.response.status_code} - {e.response.text}")
            return f"[Ошибка распознавания речи: {e.response.status_code}]"
        except httpx.TimeoutException:
            logger.error("ASR API timeout")
            return "[Ошибка распознавания речи: превышено время ожидания]"
        except Exception as e:
            logger.error(f"ASR API call failed: {e}")
            return f"[Ошибка распознавания речи: {str(e)}]"
    
    async def transcribe_file(self, file_path: str) -> str:
        """
        Transcribe audio file to text.
        
        Args:
            file_path: Path to audio file
        
        Returns:
            Transcribed text
        """
        try:
            with open(file_path, "rb") as f:
                audio_data = f.read()
            
            # Detect format from extension
            audio_format = file_path.split(".")[-1].lower()
            
            return await self.transcribe(audio_data, audio_format)
        except FileNotFoundError:
            logger.error(f"Audio file not found: {file_path}")
            return "[Ошибка: файл не найден]"
        except Exception as e:
            logger.error(f"Failed to read audio file: {e}")
            return f"[Ошибка чтения файла: {str(e)}]"


# Singleton instance
_asr_service = None


def get_asr_service() -> ASRService:
    """Get or create ASRService singleton"""
    global _asr_service
    if _asr_service is None:
        _asr_service = ASRService()
    return _asr_service
