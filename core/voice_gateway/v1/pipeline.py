"""
Voice Pipeline - Complete voice-to-voice processing
"""
import logging
from typing import List, Dict, Optional
from .llm import get_llm_service
from .asr import get_asr_service
from .tts import get_tts_service

logger = logging.getLogger(__name__)


class VoicePipeline:
    """
    Complete voice processing pipeline: ASR -> LLM -> TTS
    """
    
    def __init__(self):
        self.llm = get_llm_service()
        self.asr = get_asr_service()
        self.tts = get_tts_service()
    
    async def voice_to_voice(
        self,
        audio_data: bytes,
        system_prompt: str = "",
        conversation_history: List[Dict[str, str]] = None
    ) -> Optional[bytes]:
        """
        Complete voice-to-voice pipeline.
        
        Args:
            audio_data: Input audio bytes
            system_prompt: System prompt for LLM
            conversation_history: Previous conversation messages
        
        Returns:
            Output audio bytes or None on error
        """
        # Step 1: Transcribe audio to text (ASR)
        text = await self.asr.transcribe(audio_data)
        
        if text.startswith("["):
            # Error message from ASR
            logger.error(f"ASR failed: {text}")
            return None
        
        logger.info(f"Transcribed text: {text}")
        
        # Step 2: Generate response using LLM
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        if conversation_history:
            messages.extend(conversation_history)
        
        messages.append({"role": "user", "content": text})
        
        response_text = await self.llm.chat(messages)
        logger.info(f"LLM response: {response_text}")
        
        # Step 3: Synthesize response to audio (TTS)
        audio_response = await self.tts.synthesize(response_text)
        
        if audio_response is None:
            logger.error("TTS failed")
            return None
        
        return audio_response
    
    async def voice_to_text(self, audio_data: bytes) -> str:
        """
        Transcribe audio to text.
        
        Args:
            audio_data: Input audio bytes
        
        Returns:
            Transcribed text
        """
        return await self.asr.transcribe(audio_data)
    
    async def text_to_voice(self, text: str) -> Optional[bytes]:
        """
        Synthesize text to audio.
        
        Args:
            text: Input text
        
        Returns:
            Output audio bytes or None on error
        """
        return await self.tts.synthesize(text)
    
    async def text_to_text(
        self,
        text: str,
        system_prompt: str = "",
        conversation_history: List[Dict[str, str]] = None
    ) -> str:
        """
        Process text through LLM.
        
        Args:
            text: Input text
            system_prompt: System prompt for LLM
            conversation_history: Previous conversation messages
        
        Returns:
            LLM response text
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        if conversation_history:
            messages.extend(conversation_history)
        
        messages.append({"role": "user", "content": text})
        
        return await self.llm.chat(messages)
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> str:
        """
        Direct LLM chat interface.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
        
        Returns:
            LLM response text
        """
        return await self.llm.chat(messages, temperature, max_tokens)


# Singleton instance
_pipeline = None


def get_pipeline() -> VoicePipeline:
    """Get or create VoicePipeline singleton"""
    global _pipeline
    if _pipeline is None:
        _pipeline = VoicePipeline()
    return _pipeline
