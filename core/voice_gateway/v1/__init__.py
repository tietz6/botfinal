"""Voice Gateway V1 - LLM communication pipeline"""
import os
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class VoicePipeline:
    """
    Unified LLM gateway for all modules.
    Provides fallback behavior if external LLM API is not available.
    """
    
    def __init__(self):
        self.api_key = os.getenv("LLM_API_KEY", "")
        self.api_url = os.getenv("LLM_API_URL", "")
        self.has_external_api = bool(self.api_key and self.api_url)
        
        if not self.has_external_api:
            logger.warning("LLM API not configured, using fallback mode")
    
    async def llm_chat(self, messages: List[Dict[str, str]]) -> str:
        """
        Main method for LLM communication.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
                     Example: [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]
        
        Returns:
            Generated response text
        """
        if self.has_external_api:
            return await self._call_external_api(messages)
        else:
            return await self._fallback_response(messages)
    
    async def _call_external_api(self, messages: List[Dict[str, str]]) -> str:
        """Call external LLM API (DeepSeek or similar)"""
        try:
            import httpx
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.api_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "messages": messages,
                        "temperature": 0.7,
                        "max_tokens": 500
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                # Handle different API response formats
                if "choices" in data:
                    return data["choices"][0]["message"]["content"]
                elif "response" in data:
                    return data["response"]
                else:
                    return data.get("content", "")
                    
        except Exception as e:
            logger.error(f"External API call failed: {e}")
            return await self._fallback_response(messages)
    
    async def _fallback_response(self, messages: List[Dict[str, str]]) -> str:
        """
        Fallback response generator when external API is unavailable.
        Provides reasonable responses based on message context.
        """
        if not messages:
            return "Привет! Я готов помочь."
        
        last_message = messages[-1].get("content", "").lower()
        
        # Detect context from system/user messages
        system_context = ""
        for msg in messages:
            if msg.get("role") == "system":
                system_context = msg.get("content", "").lower()
                break
        
        # Coach responses
        if "coach" in system_context or "коуч" in system_context:
            return self._generate_coach_response(last_message, system_context)
        
        # Client responses
        if "client" in system_context or "клиент" in system_context:
            return self._generate_client_response(last_message, system_context)
        
        # Default friendly response
        return "Отличный вопрос! Давайте подумаем об этом вместе. Что для вас важнее всего в этом вопросе?"
    
    def _generate_coach_response(self, user_msg: str, context: str) -> str:
        """Generate coach-style feedback"""
        responses = [
            "Хорошее начало! Попробуй добавить больше тепла и задать уточняющий вопрос.",
            "Отлично! Ты проявил эмпатию. Теперь можно мягко подвести к следующему этапу.",
            "Обрати внимание: важно не давить, а показать ценность через историю клиента.",
            "Хорошо! Не забудь про открытый вопрос в конце — это поддерживает диалог.",
            "Супер! Теперь можно углубиться в детали и показать искренний интерес."
        ]
        
        # Simple heuristic based on message length and keywords
        if len(user_msg) < 30:
            return "Хорошее начало! Попробуй развить мысль подробнее и добавь личный вопрос."
        elif "?" not in user_msg:
            return "Отлично! Добавь вопрос в конце, чтобы поддержать диалог."
        else:
            import random
            return random.choice(responses)
    
    def _generate_client_response(self, user_msg: str, context: str) -> str:
        """Generate client-style responses"""
        # Detect sentiment
        positive_words = ["спасибо", "отлично", "интересно", "хорошо", "да", "понял"]
        doubt_words = ["не знаю", "дорого", "подумать", "позже", "сомневаюсь"]
        
        has_positive = any(word in user_msg for word in positive_words)
        has_doubt = any(word in user_msg for word in doubt_words)
        
        if has_doubt:
            responses = [
                "Хм, звучит интересно, но я пока не уверен... Расскажите подробнее?",
                "Мне нравится идея, но нужно подумать. А сколько времени это занимает?",
                "Интересно, но я раньше не встречал такое. А как это работает?",
            ]
        elif has_positive or "?" in user_msg:
            responses = [
                "Да, мне интересно! Расскажите, как это происходит?",
                "Звучит здорово! А какие есть варианты?",
                "О, это то, что я искал! Что нужно для начала?",
                "Отлично! Мне нравится такой подход. Что дальше?",
            ]
        else:
            responses = [
                "Хм, интересно... Расскажите подробнее.",
                "Я слушаю вас. Что вы предлагаете?",
                "Понятно. А как это мне поможет?",
            ]
        
        import random
        return random.choice(responses)


# Singleton instance
_pipeline = None


def get_pipeline() -> VoicePipeline:
    """Get or create VoicePipeline singleton"""
    global _pipeline
    if _pipeline is None:
        _pipeline = VoicePipeline()
    return _pipeline
