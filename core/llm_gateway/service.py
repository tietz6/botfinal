"""
LLM Gateway Service - Unified wrapper around existing LLMService.
Provides convenient methods for different use cases.
"""
import logging
import math
from typing import Dict, Any, List
from core.voice_gateway.v1.llm import get_llm_service

logger = logging.getLogger(__name__)


class LLMGateway:
    """
    Unified LLM gateway that wraps the existing LLMService.
    Provides high-level methods for different scenarios.
    """
    
    def __init__(self):
        self.llm_service = get_llm_service()
    
    async def generate_client_reply(self, context: Dict[str, Any]) -> str:
        """
        Generate client reply based on context.
        
        Args:
            context: Dictionary containing:
                - dialog_history: List of previous messages
                - client_profile: Client characteristics
                - manager_message: Last manager message
                
        Returns:
            Generated client reply
        """
        dialog_history = context.get("dialog_history", [])
        client_profile = context.get("client_profile", {})
        manager_message = context.get("manager_message", "")
        
        # Build system prompt for client role
        client_traits = client_profile.get("traits", "заинтересованный, но осторожный")
        client_mood = client_profile.get("mood", "neutral")
        client_context = client_profile.get("context", "")
        
        system_prompt = f"""Ты — потенциальный клиент проекта "На Счастье".
Твои характеристики: {client_traits}
Настроение: {client_mood}
{client_context}

Отвечай естественно, как обычный человек. Не спеши соглашаться на покупку.
Задавай вопросы, если что-то непонятно. Будь реалистичным."""
        
        # Build messages for LLM
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add dialog history
        for msg in dialog_history[-6:]:  # Last 6 messages for context
            role = "assistant" if msg.get("from") == "client" else "user"
            messages.append({"role": role, "content": msg.get("text", "")})
        
        # Add current manager message
        if manager_message:
            messages.append({"role": "user", "content": manager_message})
        
        # Generate response
        response = await self.llm_service.chat(messages, temperature=0.8, max_tokens=300)
        return response
    
    async def generate_coach_feedback(self, context: Dict[str, Any]) -> str:
        """
        Generate coach feedback for manager's performance.
        
        Args:
            context: Dictionary containing:
                - dialog_history: List of previous messages
                - manager_message: Last manager message
                - evaluation_criteria: What to evaluate
                - stage: Current stage of conversation
                
        Returns:
            Coach feedback
        """
        dialog_history = context.get("dialog_history", [])
        manager_message = context.get("manager_message", "")
        criteria = context.get("evaluation_criteria", "теплота, структура, вопросы")
        stage = context.get("stage", "unknown")
        
        system_prompt = f"""Ты — опытный коуч по продажам проекта "На Счастье".
Ты анализируешь работу менеджера и даёшь конструктивную обратную связь.

Критерии оценки: {criteria}
Текущий этап: {stage}

Твоя задача:
1. Отметить, что менеджер сделал хорошо
2. Указать на точки роста (без критики, конструктивно)
3. Дать конкретный совет на следующий шаг

Стиль: дружелюбный, поддерживающий, конкретный."""
        
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add recent dialog context
        if dialog_history:
            context_text = "История диалога:\n"
            for msg in dialog_history[-4:]:
                from_who = msg.get("from", "")
                text = msg.get("text", "")
                context_text += f"{from_who}: {text}\n"
            messages.append({"role": "user", "content": context_text})
        
        # Add manager's current message
        if manager_message:
            messages.append({
                "role": "user",
                "content": f"Последнее сообщение менеджера: {manager_message}\n\nДай обратную связь."
            })
        
        response = await self.llm_service.chat(messages, temperature=0.7, max_tokens=400)
        return response
    
    async def generate_song_text(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate song text based on client story.
        
        Args:
            context: Dictionary containing:
                - story: Client's story
                - style: Music style (romantic, upbeat, etc.)
                - language: Language (ru, en, etc.)
                - length: Song length (short, full, etc.)
                - from_person: Who is giving the gift
                - to_person: Who is receiving
                - mood: Emotional mood (love, support, celebration, etc.)
                
        Returns:
            Dictionary with song structure
        """
        story = context.get("story", "")
        style = context.get("style", "romantic")
        language = context.get("language", "ru")
        length = context.get("length", "full")
        from_person = context.get("from_person", "автор")
        to_person = context.get("to_person", "получатель")
        mood = context.get("mood", "love")
        
        system_prompt = f"""Ты — профессиональный автор песен для проекта "На Счастье".
Ты создаёшь искренние, трогательные тексты песен по историям клиентов.

Стиль: {style}
Язык: {language}
Настроение: {mood}
Длина: {length}

Требования:
- Текст должен быть личным и эмоциональным
- Включай детали из истории клиента
- Избегай клише и банальностей
- Структура: вступление, куплет 1, припев, куплет 2, припев, bridge, финальный припев
- Не используй сложные метафоры, пиши просто и от души"""
        
        user_prompt = f"""История:
От кого: {from_person}
Кому: {to_person}

{story}

Создай текст песни по этой истории. Верни структурированный текст с разделением на части."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = await self.llm_service.chat(messages, temperature=0.8, max_tokens=800)
        
        # Parse response into structure
        # For now, return as single text, but in future can parse into sections
        return {
            "text": response,
            "structure": self._parse_song_structure(response),
            "prompt_for_cover": await self._generate_cover_prompt(story, style),
            "notes_for_voice": f"Исполнять {style}, с чувством {mood}, подчёркивая эмоциональные моменты."
        }
    
    def _parse_song_structure(self, text: str) -> Dict[str, str]:
        """Parse song text into structure (simple version)"""
        # Simple parsing - split by common section markers
        structure = {
            "intro": "",
            "verse1": "",
            "chorus": "",
            "verse2": "",
            "bridge": "",
            "outro": ""
        }
        
        # Try to identify sections
        lines = text.split("\n")
        current_section = "verse1"
        
        for line in lines:
            line_lower = line.lower().strip()
            if "припев" in line_lower or "chorus" in line_lower:
                current_section = "chorus"
            elif "куплет 2" in line_lower or "verse 2" in line_lower:
                current_section = "verse2"
            elif "bridge" in line_lower or "бридж" in line_lower:
                current_section = "bridge"
            elif "вступление" in line_lower or "intro" in line_lower:
                current_section = "intro"
            elif line.strip():
                structure[current_section] += line + "\n"
        
        return structure
    
    async def _generate_cover_prompt(self, story: str, style: str) -> str:
        """Generate image prompt for song cover"""
        system_prompt = """Ты создаёшь описания для обложек песен.
Опиши визуальную сцену, которая передаёт атмосферу истории.
Стиль: кинематографичный, эмоциональный, тёплый.
Ответ должен быть кратким, 2-3 предложения."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"История: {story}\nСтиль: {style}\nОпиши обложку для песни."}
        ]
        
        response = await self.llm_service.chat(messages, temperature=0.7, max_tokens=150)
        return response
    
    async def generate_video_prompts(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate video prompts timeline from song text.
        
        Args:
            context: Dictionary containing:
                - song_text: Full song text
                - audio_duration_sec: Duration in seconds
                - platform: Target platform (sora, veo, etc.)
                - chunk_duration_sec: Duration per scene
                
        Returns:
            Timeline with prompts for each scene
        """
        song_text = context.get("song_text", "")
        duration = context.get("audio_duration_sec", 120)
        platform = context.get("platform", "sora")
        chunk_duration = context.get("chunk_duration_sec", 5)
        
        # Use ceiling to ensure full duration is covered
        total_chunks = math.ceil(duration / chunk_duration)
        
        system_prompt = f"""Ты — режиссёр видеоклипов для проекта "На Счастье".
Создай timeline промтов для генерации видео по тексту песни.

Платформа: {platform}
Длительность: {duration} секунд
Сцен: {total_chunks}
Длительность сцены: {chunk_duration} секунд

Требования:
- Каждая сцена должна визуально передавать смысл слов
- Создай плавные переходы между сценами
- Используй кинематографичное освещение
- Эмоции персонажей должны быть выразительными
- Стиль: тёплый, человечный, не слишком глянцевый"""
        
        user_prompt = f"""Текст песни:
{song_text}

Создай {total_chunks} промтов для видео, по {chunk_duration} секунд каждый.
Для каждого промта укажи:
1. Описание сцены
2. Эмоцию, которую нужно передать"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = await self.llm_service.chat(messages, temperature=0.7, max_tokens=1000)
        
        # Parse response into timeline
        timeline = self._parse_video_timeline(response, total_chunks, chunk_duration)
        
        return {
            "total_chunks": total_chunks,
            "timeline": timeline,
            "global_style": "Кинематографичный стиль, тёплое освещение, мягкие тени, естественные цвета"
        }
    
    def _parse_video_timeline(self, text: str, total_chunks: int, chunk_duration: int) -> List[Dict[str, Any]]:
        """Parse LLM response into video timeline"""
        timeline = []
        lines = text.split("\n")
        
        current_prompt = ""
        current_emotion = "neutral"
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Simple parsing - look for numbered items or scene descriptions
            if line and not line.startswith("#"):
                if ":" in line:
                    parts = line.split(":", 1)
                    if "эмоция" in parts[0].lower() or "emotion" in parts[0].lower():
                        current_emotion = parts[1].strip()
                    else:
                        current_prompt = parts[1].strip() if len(parts) > 1 else line
                else:
                    current_prompt = line
                
                # If we have enough info, add to timeline
                if current_prompt and len(timeline) < total_chunks:
                    start_sec = len(timeline) * chunk_duration
                    end_sec = start_sec + chunk_duration
                    
                    timeline.append({
                        "start_sec": start_sec,
                        "end_sec": end_sec,
                        "prompt": current_prompt,
                        "emotion": current_emotion
                    })
                    current_prompt = ""
        
        # Fill remaining slots if needed
        while len(timeline) < total_chunks:
            start_sec = len(timeline) * chunk_duration
            end_sec = start_sec + chunk_duration
            timeline.append({
                "start_sec": start_sec,
                "end_sec": end_sec,
                "prompt": "Продолжение истории, мягкий переход",
                "emotion": "neutral"
            })
        
        return timeline[:total_chunks]


# Singleton instance
_llm_gateway = None


def get_llm_gateway() -> LLMGateway:
    """Get or create LLMGateway singleton"""
    global _llm_gateway
    if _llm_gateway is None:
        _llm_gateway = LLMGateway()
    return _llm_gateway
