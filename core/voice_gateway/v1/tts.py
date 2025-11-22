"""
TTS Service - Text to Speech
"""
import os
import logging
import httpx
from typing import Optional

logger = logging.getLogger(__name__)


class TTSService:
    """Text to Speech service"""
    
    def __init__(self):
        self.api_key = os.getenv("VOICE_API_KEY", "")
        self.api_base_url = os.getenv("VOICE_API_BASE_URL", "https://example.com/voice-api")
        self.tts_endpoint = f"{self.api_base_url}/tts"
        
        if not self.api_key:
            logger.warning("VOICE_API_KEY not set, TTS service may not work properly")
    
    async def synthesize(
        self,
        text: str,
        voice: str = "default",
        speed: float = 1.0
    ) -> Optional[bytes]:
        """
        Synthesize text to speech audio.
        
        Args:
            text: Text to synthesize
            voice: Voice name/ID
            speed: Speech speed (0.5 - 2.0)
        
        Returns:
            Audio bytes (OGG format) or None on error
        """
        if not self.api_key:
            logger.error("VOICE_API_KEY not configured")
            return None
        
        if not text or not text.strip():
            logger.warning("Empty text provided for synthesis")
            return None
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "text": text,
                    "voice": voice,
                    "speed": speed,
                    "format": "ogg"  # Request OGG format for Telegram compatibility
                }
                
                response = await client.post(
                    self.tts_endpoint,
                    headers=headers,
                    json=payload
                )
                
                response.raise_for_status()
                
                # Check if response is audio binary
                content_type = response.headers.get("content-type", "")
                
                if "audio" in content_type or "application/octet-stream" in content_type:
                    # Direct audio response
                    return response.content
                else:
                    # JSON response with audio URL or base64
                    data = response.json()
                    
                    if "audio" in data and isinstance(data["audio"], bytes):
                        return data["audio"]
                    elif "audio_url" in data:
                        # Download audio from URL
                        audio_response = await client.get(data["audio_url"])
                        audio_response.raise_for_status()
                        return audio_response.content
                    elif "audio_base64" in data:
                        import base64
                        return base64.b64decode(data["audio_base64"])
                    else:
                        logger.error(f"Unexpected TTS response format: {data}")
                        return None
                    
        except httpx.HTTPStatusError as e:
            logger.error(f"TTS API HTTP error: {e.response.status_code} - {e.response.text}")
            return None
        except httpx.TimeoutException:
            logger.error("TTS API timeout")
            return None
        except Exception as e:
            logger.error(f"TTS API call failed: {e}")
            return None
    
    async def synthesize_to_file(
        self,
        text: str,
        output_path: str,
        voice: str = "default",
        speed: float = 1.0
    ) -> bool:
        """
        Synthesize text to speech and save to file.
        
        Args:
            text: Text to synthesize
            output_path: Path to save audio file
            voice: Voice name/ID
            speed: Speech speed (0.5 - 2.0)
        
        Returns:
            True if successful, False otherwise
        """
        audio_data = await self.synthesize(text, voice, speed)
        
        if audio_data:
            try:
                with open(output_path, "wb") as f:
                    f.write(audio_data)
                return True
            except Exception as e:
                logger.error(f"Failed to save audio file: {e}")
                return False
        
        return False


# Singleton instance
_tts_service = None


def get_tts_service() -> TTSService:
    """Get or create TTSService singleton"""
    global _tts_service
    if _tts_service is None:
        _tts_service = TTSService()
    return _tts_service
