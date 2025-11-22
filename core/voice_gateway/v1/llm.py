"""
LLM Service - Real DeepSeek API Integration
"""
import os
import logging
import random
import httpx
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class LLMService:
    """DeepSeek LLM integration service"""
    
    def __init__(self):
        self.api_key = os.getenv("DEEPSEEK_API_KEY", "")
        self.api_base_url = os.getenv("DEEPSEEK_API_BASE_URL", "https://api.deepseek.com/v1")
        self.chat_endpoint = f"{self.api_base_url}/chat/completions"
        
        if not self.api_key:
            logger.warning("DEEPSEEK_API_KEY not set, LLM service may not work properly")
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> str:
        """
        Send chat request to DeepSeek API.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
                     Example: [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]
            temperature: Sampling temperature (0.0 - 1.0)
            max_tokens: Maximum tokens to generate
        
        Returns:
            Generated response text
        """
        if not self.api_key:
            logger.error("DEEPSEEK_API_KEY not configured")
            return self._fallback_response(messages)
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.chat_endpoint,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "deepseek-chat",
                        "messages": messages,
                        "temperature": temperature,
                        "max_tokens": max_tokens
                    }
                )
                
                response.raise_for_status()
                data = response.json()
                
                # Extract response from DeepSeek format
                if "choices" in data and len(data["choices"]) > 0:
                    return data["choices"][0]["message"]["content"]
                else:
                    logger.error(f"Unexpected API response format: {data}")
                    return self._fallback_response(messages)
                    
        except httpx.HTTPStatusError as e:
            logger.error(f"DeepSeek API HTTP error: {e.response.status_code} - {e.response.text}")
            return self._fallback_response(messages)
        except httpx.TimeoutException:
            logger.error("DeepSeek API timeout")
            return self._fallback_response(messages)
        except Exception as e:
            logger.error(f"DeepSeek API call failed: {e}")
            return self._fallback_response(messages)
    
    def _fallback_response(self, messages: List[Dict[str, str]]) -> str:
        """
        Generate fallback response when API is unavailable.
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
            return self._generate_coach_response(last_message)
        
        # Client responses
        if "client" in system_context or "клиент" in system_context:
            return self._generate_client_response(last_message)
        
        # Default friendly response
        return "Отличный вопрос! Давайте подумаем об этом вместе. Что для вас важнее всего в этом вопросе?"
    
    def _generate_coach_response(self, user_msg: str) -> str:
        """Generate coach-style feedback"""
        responses = [
            "Хорошее начало! Попробуй добавить больше тепла и задать уточняющий вопрос.",
            "Отлично! Ты проявил эмпатию. Теперь можно мягко подвести к следующему этапу.",
            "Обрати внимание: важно не давить, а показать ценность через историю клиента.",
            "Хорошо! Не забудь про открытый вопрос в конце — это поддерживает диалог.",
            "Супер! Теперь можно углубиться в детали и показать искренний интерес."
        ]
        
        if len(user_msg) < 30:
            return "Хорошее начало! Попробуй развить мысль подробнее и добавь личный вопрос."
        elif "?" not in user_msg:
            return "Отлично! Добавь вопрос в конце, чтобы поддержать диалог."
        else:
            return random.choice(responses)
    
    def _generate_client_response(self, user_msg: str) -> str:
        """Generate client-style responses"""
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
        
        return random.choice(responses)


# Singleton instance
_llm_service = None


def get_llm_service() -> LLMService:
    """Get or create LLMService singleton"""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
