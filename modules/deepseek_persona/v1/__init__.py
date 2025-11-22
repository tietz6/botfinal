"""
DeepSeek Persona V1
Brand voice for "На Счастье" project - warm, empathetic, human communication
"""
from typing import List, Dict
from core.voice_gateway.v1 import get_pipeline

# Brand style guidelines
BRAND_STYLE = {
    "warmth": "Тёплое первое касание, без давления",
    "empathy": "Много эмпатии и человеческих формулировок",
    "no_pressure": "Никакой агрессии и сухих фраз",
    "transparency": "Прозрачность и честность в объяснениях"
}

# Persona system prompts
COACH_SYSTEM_PROMPT = """Ты — опытный коуч-наставник в проекте "На Счастье".
Твоя задача — помогать менеджерам учиться тёплому, эмпатичному общению с клиентами.

Стиль общения:
- Тёплый, мягкий, но честный
- Даёшь конструктивную обратную связь
- Поддерживаешь и подсказываешь, как улучшить
- Не критикуешь, а показываешь лучший путь
- Краткие, но ёмкие советы (2-3 предложения)

Критерии оценки менеджера:
- Тепло и эмпатия в сообщении
- Наличие открытых вопросов
- Понятность и структура
- Отсутствие давления на клиента
"""

CLIENT_SYSTEM_PROMPT = """Ты — живой клиент в диалоге с менеджером проекта "На Счастье".
"На Счастье" создаёт уникальные песни по реальным историям людей.

Твой характер:
- Естественный, с эмоциями (радость, сомнения, интерес)
- Реагируешь на тон и подход менеджера
- Можешь сомневаться, если менеджер давит
- Открываешься, если менеджер тёплый и искренний
- Задаёшь естественные вопросы клиента

Помни:
- Ты не знаешь деталей услуги заранее
- Реагируешь человечески на каждое сообщение
- Можешь быть любопытным, но осторожным с деньгами
- Отвечай 2-3 предложениями, как в живой переписке
"""


async def persona_chat(role: str, messages: List[Dict[str, str]]) -> str:
    """
    Generate response in brand voice for specified role.
    
    Args:
        role: "coach" or "client"
        messages: Conversation history
    
    Returns:
        Generated response text
    """
    pipeline = get_pipeline()
    
    # Prepare messages with system prompt
    if role == "coach":
        system_prompt = COACH_SYSTEM_PROMPT
    elif role == "client":
        system_prompt = CLIENT_SYSTEM_PROMPT
    else:
        system_prompt = "Ты — полезный ассистент в проекте 'На Счастье'."
    
    # Build full message list
    full_messages = [{"role": "system", "content": system_prompt}]
    full_messages.extend(messages)
    
    # Get response from LLM
    response = await pipeline.llm_chat(full_messages)
    
    # Apply stylization
    styled_response = stylize(response, role)
    
    return styled_response


def stylize(text: str, role: str) -> str:
    """
    Apply brand style to text.
    
    Args:
        text: Original text
        role: "coach" or "client"
    
    Returns:
        Stylized text
    """
    # Remove overly formal phrases
    replacements = {
        "Извините": "Простите",
        "Вы должны": "Было бы здорово, если бы вы",
        "обязательно": "важно",
        "необходимо": "было бы отлично",
        "требуется": "нужно",
    }
    
    styled = text
    for old, new in replacements.items():
        styled = styled.replace(old, new)
    
    # Ensure warm tone
    if role == "coach" and styled and not any(emoji in styled for emoji in ["😊", "🌟", "✨", "💫"]):
        # Don't force emojis, let natural response flow
        pass
    
    return styled.strip()


async def generate_greeting(context: str = "") -> str:
    """
    Generate initial greeting for client.
    
    Args:
        context: Optional context for greeting
    
    Returns:
        Greeting message
    """
    messages = [{
        "role": "user",
        "content": f"Напиши приветствие клиенту от имени менеджера проекта 'На Счастье'. {context}"
    }]
    
    return await persona_chat("client", messages)


async def evaluate_message(
    manager_message: str,
    stage: str,
    context: str = ""
) -> Dict[str, any]:
    """
    Evaluate manager's message quality.
    
    Args:
        manager_message: Manager's message text
        stage: Current conversation stage
        context: Additional context
    
    Returns:
        Evaluation dict with scores and feedback
    """
    # Simple heuristic evaluation
    scores = {
        "warmth": 0,
        "questions": 0,
        "clarity": 0,
        "length": 0
    }
    
    msg_lower = manager_message.lower()
    
    # Warmth check
    warm_words = ["добр", "рад", "приятно", "здравствуйте", "привет", "😊", "🥰"]
    if any(word in msg_lower for word in warm_words):
        scores["warmth"] = 8
    else:
        scores["warmth"] = 4
    
    # Questions check
    question_count = manager_message.count("?")
    scores["questions"] = min(10, question_count * 3)
    
    # Clarity and length
    word_count = len(manager_message.split())
    if 10 <= word_count <= 50:
        scores["clarity"] = 8
        scores["length"] = 8
    elif word_count < 10:
        scores["clarity"] = 4
        scores["length"] = 4
    else:
        scores["clarity"] = 6
        scores["length"] = 6
    
    # Overall score
    overall = sum(scores.values()) / len(scores)
    
    return {
        "scores": scores,
        "overall": round(overall, 1),
        "needs_improvement": overall < 6
    }
