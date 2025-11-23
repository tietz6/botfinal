"""
Simple Telegram Bot for SALESBOT Training System
Integrates with FastAPI backend to provide training through Telegram
"""
import os
import logging
import asyncio
import httpx
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8080")

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration constants
MAX_ENCYCLOPEDIA_PAGES = 8  # Maximum number of encyclopedia pages to display
MAX_CONTENT_LENGTH = 3000   # Maximum content length before truncation
MAX_LYRICS_LENGTH = 2000    # Maximum lyrics length before truncation
MAX_SCENES_DISPLAY = 5      # Maximum number of video scenes to display
MAX_FEEDBACK_LENGTH = 500   # Maximum feedback length before truncation
MAX_STRENGTHS_DISPLAY = 3   # Maximum number of strengths to display
MAX_IMPROVEMENTS_DISPLAY = 3  # Maximum number of improvements to display

# Default content generation parameters
DEFAULT_SONG_STYLE = "romantic"
DEFAULT_SONG_MOOD = "love"
DEFAULT_VIDEO_PLATFORM = "sora"
DEFAULT_VIDEO_STYLE = "cinematic"
DEFAULT_PHOTO_ANIMATION_STYLE = "natural"

# Dialog role identifiers
MANAGER_ROLE_KEYWORDS = ['менеджер', 'manager']
CLIENT_ROLE_KEYWORDS = ['клиент', 'client']

# User session storage (in-memory for simplicity)
user_sessions: Dict[int, Dict[str, Any]] = {}


def get_user_session(user_id: int) -> Dict[str, Any]:
    """Get or create user session"""
    if user_id not in user_sessions:
        user_sessions[user_id] = {
            "active_module": None,
            "session_id": None,
            "state": "idle"
        }
    return user_sessions[user_id]


async def call_backend(endpoint: str, method: str = "GET", data: Dict = None, files: Dict = None) -> Optional[Dict]:
    """
    Call backend API.
    
    Args:
        endpoint: API endpoint (e.g., '/master_path/start/session123')
        method: HTTP method
        data: Request data for POST
        files: Files for multipart upload
    
    Returns:
        Response data or None on error
    """
    url = f"{BACKEND_URL}{endpoint}"
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            if method == "POST":
                if files:
                    response = await client.post(url, files=files, data=data or {})
                else:
                    response = await client.post(url, json=data or {})
            else:
                response = await client.get(url)
            
            response.raise_for_status()
            
            # Check if response is JSON or binary
            content_type = response.headers.get("content-type", "")
            if "application/json" in content_type:
                return response.json()
            else:
                # Return binary content for audio
                return {"audio": response.content, "content_type": content_type}
    except httpx.HTTPError as e:
        logger.error(f"Backend call failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error calling backend: {e}")
        return None


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    user_id = user.id
    
    # Check if user has a role assigned
    role_response = await call_backend(f"/api/public/v1/get_role/{user_id}")
    
    if not role_response or not role_response.get("role"):
        # User needs to select a role first
        await show_role_selection(update)
        return
    
    # User has a role, show main menu
    welcome_text = f"""👋 Привет, {user.first_name}!

Добро пожаловать в **SALESBOT** — систему тренировок для проекта "На Счастье"!

💬 Пиши текстом или 🎤 отправляй голосовые сообщения!

**Выбери раздел:**"""
    
    role = role_response.get("role")
    keyboard = []
    
    # Training modules for all roles
    keyboard.append([InlineKeyboardButton("🎓 Школа продаж", callback_data="section_training")])
    
    # Encyclopedia for all roles
    keyboard.append([InlineKeyboardButton("📚 База знаний", callback_data="section_encyclopedia")])
    
    # Content creation for generators and admins
    if role in ["generator", "admin"]:
        keyboard.append([InlineKeyboardButton("🎨 Создание контента", callback_data="section_content")])
    
    # Change role option
    keyboard.append([InlineKeyboardButton("👤 Изменить роль", callback_data="change_role")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="Markdown")


async def show_role_selection(update: Update):
    """Show role selection menu"""
    text = """👋 Добро пожаловать в SALESBOT!

Для начала работы выбери свою роль:"""
    
    keyboard = [
        [InlineKeyboardButton("👨‍💼 Менеджер по продажам", callback_data="role_manager")],
        [InlineKeyboardButton("🎨 Генератор контента", callback_data="role_generator")],
        [InlineKeyboardButton("👑 Руководство", callback_data="role_admin")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    elif update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    # Role selection
    if data.startswith("role_"):
        role = data.replace("role_", "")
        await set_user_role_handler(query, user_id, role)
    elif data == "change_role":
        await show_role_selection(query)
    
    # Section navigation
    elif data == "section_training":
        await show_training_menu(query, user_id)
    elif data == "section_encyclopedia":
        await show_encyclopedia_menu(query, user_id)
    elif data == "section_content":
        await show_content_menu(query, user_id)
    
    # Legacy support
    elif data == "level_beginner":
        await show_beginner_menu(query, user_id)
    elif data == "level_advanced":
        await show_advanced_menu(query, user_id)
    
    # Module actions
    elif data.startswith("module_"):
        module = data.replace("module_", "")
        await start_training_module(query, user_id, module)
    elif data.startswith("encyclopedia_"):
        page_id = data.replace("encyclopedia_", "")
        await show_encyclopedia_page(query, user_id, page_id)
    
    # Navigation
    elif data == "main_menu":
        await show_main_menu(query, user_id)
    elif data == "back_training":
        await show_training_menu(query, user_id)
    elif data == "back_content":
        await show_content_menu(query, user_id)


async def set_user_role_handler(query, user_id: int, role: str):
    """Set user role"""
    result = await call_backend(
        "/api/public/v1/set_role",
        method="POST",
        data={"user_id": str(user_id), "role": role}
    )
    
    if not result or not result.get("success"):
        await query.edit_message_text(
            "❌ Ошибка при установке роли. Попробуй ещё раз.",
            parse_mode="Markdown"
        )
        return
    
    role_names = {
        "manager": "Менеджер по продажам",
        "generator": "Генератор контента",
        "admin": "Руководство"
    }
    
    text = f"""✅ Роль установлена: **{role_names.get(role, role)}**

Теперь выбери раздел для работы:"""
    
    keyboard = []
    keyboard.append([InlineKeyboardButton("🎓 Школа продаж", callback_data="section_training")])
    keyboard.append([InlineKeyboardButton("📚 База знаний", callback_data="section_encyclopedia")])
    
    if role in ["generator", "admin"]:
        keyboard.append([InlineKeyboardButton("🎨 Создание контента", callback_data="section_content")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")


async def show_training_menu(query, user_id: int):
    """Show training modules menu"""
    text = """🎓 **Школа продаж**

Выбери тренировку:"""
    
    keyboard = [
        [InlineKeyboardButton("📖 Script Lab (практика скриптов)", callback_data="module_training_scripts")],
        [InlineKeyboardButton("🎯 Путь Мастера", callback_data="module_master_path")],
        [InlineKeyboardButton("🛡️ Возражения", callback_data="module_objections")],
        [InlineKeyboardButton("💎 Допродажи", callback_data="module_upsell")],
        [InlineKeyboardButton("🎪 Арена (свободная практика)", callback_data="module_arena")],
        [InlineKeyboardButton("📝 Экзамен", callback_data="module_exam")],
        [InlineKeyboardButton("« Назад", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")


async def show_encyclopedia_menu(query, user_id: int):
    """Show encyclopedia menu"""
    # Get user role
    role_response = await call_backend(f"/api/public/v1/get_role/{user_id}")
    role = role_response.get("role", "manager") if role_response else "manager"
    
    # Get available pages
    pages_response = await call_backend(f"/encyclopedia/v1/pages?role={role}")
    
    if not pages_response or not pages_response.get("success"):
        await query.edit_message_text(
            "❌ Ошибка при загрузке базы знаний.",
            parse_mode="Markdown"
        )
        return
    
    text = """📚 **База знаний**

Выбери раздел:"""
    
    keyboard = []
    pages = pages_response.get("pages", [])
    
    for page in pages[:MAX_ENCYCLOPEDIA_PAGES]:
        page_id = page.get("id", "")
        title = page.get("title", "")
        keyboard.append([InlineKeyboardButton(f"📄 {title}", callback_data=f"encyclopedia_{page_id}")])
    
    keyboard.append([InlineKeyboardButton("« Назад", callback_data="main_menu")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")


async def show_content_menu(query, user_id: int):
    """Show content creation menu"""
    text = """🎨 **Создание контента**

Выбери инструмент:"""
    
    keyboard = [
        [InlineKeyboardButton("🎵 Генератор песен", callback_data="module_song_generator")],
        [InlineKeyboardButton("🎬 Генератор видео-промптов", callback_data="module_video_prompt_generator")],
        [InlineKeyboardButton("📸 Анимация фото", callback_data="module_photo_animation")],
        [InlineKeyboardButton("📊 Анализ кейсов", callback_data="module_cases_analyzer")],
        [InlineKeyboardButton("« Назад", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")


async def show_encyclopedia_page(query, user_id: int, page_id: str):
    """Show encyclopedia page content"""
    # Get user role for access check
    role_response = await call_backend(f"/api/public/v1/get_role/{user_id}")
    role = role_response.get("role", "manager") if role_response else "manager"
    
    # Get page content
    page_response = await call_backend(f"/encyclopedia/v1/page/{page_id}?role={role}")
    
    if not page_response or not page_response.get("success"):
        await query.edit_message_text(
            "❌ Ошибка при загрузке страницы.",
            parse_mode="Markdown"
        )
        return
    
    page = page_response.get("page", {})
    title = page.get("title", "")
    content = page.get("content", "")
    
    # Format content (limit to Telegram message size)
    text = f"""📄 **{title}**

{content[:MAX_CONTENT_LENGTH]}"""
    
    if len(content) > MAX_CONTENT_LENGTH:
        text += "\n\n_...текст обрезан, полная версия доступна в API_"
    
    keyboard = [[InlineKeyboardButton("« Назад к базе знаний", callback_data="section_encyclopedia")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")


async def show_beginner_menu(query, user_id: int):
    """Show beginner training menu (legacy support)"""
    await show_training_menu(query, user_id)


async def show_advanced_menu(query, user_id: int):
    """Show advanced training menu (legacy support)"""
    await show_training_menu(query, user_id)


async def show_main_menu(query, user_id: int):
    """Show main menu"""
    # Get user role
    role_response = await call_backend(f"/api/public/v1/get_role/{user_id}")
    role = role_response.get("role") if role_response else None
    
    if not role:
        await show_role_selection(query)
        return
    
    text = """**SALESBOT** — Главное меню

Выбери раздел:"""
    
    keyboard = []
    keyboard.append([InlineKeyboardButton("🎓 Школа продаж", callback_data="section_training")])
    keyboard.append([InlineKeyboardButton("📚 База знаний", callback_data="section_encyclopedia")])
    
    if role in ["generator", "admin"]:
        keyboard.append([InlineKeyboardButton("🎨 Создание контента", callback_data="section_content")])
    
    keyboard.append([InlineKeyboardButton("👤 Изменить роль", callback_data="change_role")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")


async def start_training_module(query, user_id: int, module: str):
    """Start a training module"""
    session = get_user_session(user_id)
    session_id = f"tg_{user_id}_{module}"
    
    # Handle different module types
    if module == "song_generator":
        await start_song_generator(query, user_id)
        return
    elif module == "video_prompt_generator":
        await start_video_generator(query, user_id)
        return
    elif module == "photo_animation":
        await start_photo_animation(query, user_id)
        return
    elif module == "cases_analyzer":
        await start_cases_analyzer(query, user_id)
        return
    
    # Standard training module start
    # Call backend to start module
    result = await call_backend(f"/{module}/start/{session_id}", method="POST")
    
    if not result or not result.get("success"):
        await query.edit_message_text(
            "❌ Ошибка при запуске модуля. Попробуй позже или обратись к администратору.",
            parse_mode="Markdown"
        )
        return
    
    # Update session
    session["active_module"] = module
    session["session_id"] = session_id
    session["state"] = "training"
    
    # Get coach message
    coach_message = result.get("coach_message") or result.get("coach_intro") or result.get("exam_intro", "")
    client_message = result.get("client_message", "")
    
    # Format response
    response_text = f"{coach_message}"
    if client_message:
        response_text += f"\n\n**Клиент:**\n{client_message}"
    
    response_text += f"\n\n💬 _Напиши свой ответ в чат или отправь голосовое сообщение 🎤_"
    
    keyboard = [[InlineKeyboardButton("❌ Завершить тренировку", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(response_text, reply_markup=reply_markup, parse_mode="Markdown")


async def start_song_generator(query, user_id: int):
    """Start song generator"""
    text = """🎵 **Генератор песен**

Опиши историю для песни. Включи:
- Кому предназначена песня
- Какие чувства хочешь передать
- Важные моменты или воспоминания
- Желаемый стиль (романтика, рок, поп и т.д.)

Пример: "Хочу песню для жены на юбилей свадьбы. 10 лет вместе, познакомились в университете, вместе путешествуем. Стиль - лирическая баллада."

💬 Напиши историю:"""
    
    # Set session state for song generation
    session = get_user_session(user_id)
    session["active_module"] = "song_generator"
    session["state"] = "awaiting_song_story"
    
    keyboard = [[InlineKeyboardButton("« Назад", callback_data="section_content")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")


async def start_video_generator(query, user_id: int):
    """Start video prompt generator"""
    text = """🎬 **Генератор видео-промптов**

Для создания видео-клипа нужен текст песни.

💬 Отправь текст песни, и я создам покадровый план для видео-платформ (Sora, VEO, Pika, Runway):"""
    
    session = get_user_session(user_id)
    session["active_module"] = "video_prompt_generator"
    session["state"] = "awaiting_video_song"
    
    keyboard = [[InlineKeyboardButton("« Назад", callback_data="section_content")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")


async def start_photo_animation(query, user_id: int):
    """Start photo animation"""
    text = """📸 **Анимация фото**

Этот модуль помогает создать промпты для анимации фотографий.

💬 Опиши фото и что хочешь анимировать:

Пример: "Фото пары на пляже на закате. Хочу оживить волны, движение волос на ветру, мягкое свечение солнца."

Или просто опиши что на фото:"""
    
    session = get_user_session(user_id)
    session["active_module"] = "photo_animation"
    session["state"] = "awaiting_photo_desc"
    
    keyboard = [[InlineKeyboardButton("« Назад", callback_data="section_content")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")


async def start_cases_analyzer(query, user_id: int):
    """Start cases analyzer"""
    text = """📊 **Анализ кейсов**

Отправь диалог с клиентом для анализа. Формат:

```
Менеджер: Добрый день!
Клиент: Здравствуйте
Менеджер: Расскажите, что вас интересует?
...
```

Я проанализирую диалог и дам детальную обратную связь.

💬 Отправь диалог:"""
    
    session = get_user_session(user_id)
    session["active_module"] = "cases_analyzer"
    session["state"] = "awaiting_case_dialog"
    
    keyboard = [[InlineKeyboardButton("« Назад", callback_data="section_content")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user messages during training"""
    user_id = update.effective_user.id
    session = get_user_session(user_id)
    
    state = session.get("state", "idle")
    module = session.get("active_module")
    
    # Check if waiting for content generation input
    if state == "awaiting_song_story":
        await handle_song_story(update, user_id)
        return
    elif state == "awaiting_video_song":
        await handle_video_song(update, user_id)
        return
    elif state == "awaiting_photo_desc":
        await handle_photo_description(update, user_id)
        return
    elif state == "awaiting_case_dialog":
        await handle_case_dialog(update, user_id)
        return
    
    # Check if in training mode
    if state != "training" or not module:
        await update.message.reply_text(
            "Используй /start для начала работы или выбери модуль тренировки."
        )
        return
    
    user_text = update.message.text
    session_id = session["session_id"]
    
    # Show typing indicator
    await update.message.chat.send_action("typing")
    
    # Call backend to process turn
    result = await call_backend(
        f"/{module}/turn/{session_id}",
        method="POST",
        data={"text": user_text}
    )
    
    if not result or not result.get("success"):
        await update.message.reply_text(
            "❌ Ошибка при обработке сообщения. Попробуй ещё раз или начни сначала с /start"
        )
        return
    
    # Format response
    client_reply = result.get("client_reply", "")
    coach_tip = result.get("coach_tip") or result.get("coach_feedback") or result.get("coach_analysis") or result.get("coach_note", "")
    
    response_text = ""
    
    if client_reply:
        response_text += f"**Клиент:**\n{client_reply}\n\n"
    
    if coach_tip:
        response_text += f"**Коуч:**\n{coach_tip}\n\n"
    
    # Check if exam is completed
    if module == "exam" and result.get("is_final_round"):
        response_text += "\n✅ Экзамен завершён! Используй команду /result для получения итогов."
    
    response_text += "💬 _Продолжай диалог или нажми кнопку для выхода_"
    
    keyboard = [[InlineKeyboardButton("❌ Завершить", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(response_text, reply_markup=reply_markup, parse_mode="Markdown")


async def handle_song_story(update: Update, user_id: int):
    """Handle song story input"""
    story = update.message.text
    
    await update.message.chat.send_action("typing")
    
    # Call song generator API
    result = await call_backend(
        "/song_generator/v1/generate",
        method="POST",
        data={
            "story": story,
            "style": DEFAULT_SONG_STYLE,
            "mood": DEFAULT_SONG_MOOD
        }
    )
    
    if not result or not result.get("success"):
        await update.message.reply_text("❌ Ошибка при генерации песни. Попробуй ещё раз.")
        return
    
    song = result.get("song", {})
    title = song.get("title", "Без названия")
    lyrics = song.get("lyrics", "")
    
    response = f"""🎵 **{title}**

{lyrics[:MAX_LYRICS_LENGTH]}"""
    
    if len(lyrics) > MAX_LYRICS_LENGTH:
        response += "\n\n_...текст обрезан для отображения_"
    
    # Reset session
    session = get_user_session(user_id)
    session["state"] = "idle"
    session["active_module"] = None
    
    keyboard = [
        [InlineKeyboardButton("🔄 Создать ещё", callback_data="module_song_generator")],
        [InlineKeyboardButton("« В меню", callback_data="section_content")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(response, reply_markup=reply_markup, parse_mode="Markdown")


async def handle_video_song(update: Update, user_id: int):
    """Handle video song input"""
    song_text = update.message.text
    
    await update.message.chat.send_action("typing")
    
    result = await call_backend(
        "/video_prompt_generator/v1/from_song",
        method="POST",
        data={
            "song_text": song_text,
            "platform": DEFAULT_VIDEO_PLATFORM,
            "visual_style": DEFAULT_VIDEO_STYLE
        }
    )
    
    if not result or not result.get("success"):
        await update.message.reply_text("❌ Ошибка при генерации промптов. Попробуй ещё раз.")
        return
    
    timeline = result.get("timeline", [])
    
    response = "🎬 **Видео-таймлайн:**\n\n"
    for i, scene in enumerate(timeline[:MAX_SCENES_DISPLAY], 1):
        prompt = scene.get("prompt", "")
        response += f"**Сцена {i}:**\n{prompt}\n\n"
    
    session = get_user_session(user_id)
    session["state"] = "idle"
    session["active_module"] = None
    
    keyboard = [
        [InlineKeyboardButton("🔄 Создать ещё", callback_data="module_video_prompt_generator")],
        [InlineKeyboardButton("« В меню", callback_data="section_content")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(response, reply_markup=reply_markup, parse_mode="Markdown")


async def handle_photo_description(update: Update, user_id: int):
    """Handle photo description input"""
    description = update.message.text
    
    await update.message.chat.send_action("typing")
    
    result = await call_backend(
        "/photo_animation/v1/prompt",
        method="POST",
        data={
            "description": description,
            "style": DEFAULT_PHOTO_ANIMATION_STYLE
        }
    )
    
    if not result or not result.get("success"):
        await update.message.reply_text("❌ Ошибка при генерации промпта. Попробуй ещё раз.")
        return
    
    prompt = result.get("prompt", "")
    recommendations = result.get("recommendations", [])
    
    response = f"""📸 **Промпт для анимации:**

{prompt}

**Рекомендации:**
"""
    for rec in recommendations[:3]:
        response += f"• {rec}\n"
    
    session = get_user_session(user_id)
    session["state"] = "idle"
    session["active_module"] = None
    
    keyboard = [
        [InlineKeyboardButton("🔄 Создать ещё", callback_data="module_photo_animation")],
        [InlineKeyboardButton("« В меню", callback_data="section_content")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(response, reply_markup=reply_markup, parse_mode="Markdown")


async def handle_case_dialog(update: Update, user_id: int):
    """Handle case dialog input"""
    dialog_text = update.message.text
    
    await update.message.chat.send_action("typing")
    
    # Parse dialog into history format
    lines = dialog_text.strip().split('\n')
    history = []
    
    for line in lines:
        if ':' not in line:
            continue  # Skip lines without role separator
        
        parts = line.split(':', 1)
        if len(parts) != 2:
            continue  # Skip malformed lines
        
        role, text = parts
        role = role.strip().lower()
        text = text.strip()
        
        # Map role to API format
        if any(keyword in role for keyword in MANAGER_ROLE_KEYWORDS):
            history.append({"role": "user", "content": text})
        elif any(keyword in role for keyword in CLIENT_ROLE_KEYWORDS):
            history.append({"role": "assistant", "content": text})
    
    result = await call_backend(
        "/cases_analyzer/v1/analyze",
        method="POST",
        data={"history": history}
    )
    
    if not result or not result.get("success"):
        await update.message.reply_text("❌ Ошибка при анализе диалога. Попробуй ещё раз.")
        return
    
    score = result.get("overall_score", 0)
    feedback = result.get("feedback", "")
    strengths = result.get("strengths", [])
    improvements = result.get("improvements", [])
    
    response = f"""📊 **Анализ диалога**

Общая оценка: {score}/10

**Сильные стороны:**
"""
    for s in strengths[:MAX_STRENGTHS_DISPLAY]:
        response += f"✅ {s}\n"
    
    response += "\n**Что улучшить:**\n"
    for imp in improvements[:MAX_IMPROVEMENTS_DISPLAY]:
        response += f"💡 {imp}\n"
    
    if feedback:
        response += f"\n**Общая обратная связь:**\n{feedback[:MAX_FEEDBACK_LENGTH]}"
    
    session = get_user_session(user_id)
    session["state"] = "idle"
    session["active_module"] = None
    
    keyboard = [
        [InlineKeyboardButton("🔄 Анализ ещё", callback_data="module_cases_analyzer")],
        [InlineKeyboardButton("« В меню", callback_data="section_content")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(response, reply_markup=reply_markup, parse_mode="Markdown")


async def result_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /result command for exam results"""
    user_id = update.effective_user.id
    session = get_user_session(user_id)
    
    if session["active_module"] != "exam":
        await update.message.reply_text("Эта команда работает только после экзамена.")
        return
    
    session_id = session["session_id"]
    
    # Call backend to get result
    result = await call_backend(f"/exam/result/{session_id}")
    
    if not result or not result.get("success"):
        await update.message.reply_text("❌ Ошибка при получении результата.")
        return
    
    if result.get("status") == "in_progress":
        await update.message.reply_text("Экзамен ещё не завершён. Продолжай отвечать на вопросы.")
        return
    
    # Format result
    final_score = result.get("final_score", 0)
    grade = result.get("grade", "")
    verdict = result.get("verdict", "")
    scenario_name = result.get("scenario_name", "")
    
    result_text = f"""📊 **РЕЗУЛЬТАТ ЭКЗАМЕНА**

Сценарий: {scenario_name}

**Итоговый балл:** {final_score}/100
**Оценка:** {grade}

{verdict}

Используй /start для новой тренировки."""
    
    await update.message.reply_text(result_text, parse_mode="Markdown")


async def master_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Quick start for master_path"""
    user_id = update.effective_user.id
    session = get_user_session(user_id)
    session_id = f"tg_{user_id}_master_path"
    
    result = await call_backend(f"/master_path/start/{session_id}", method="POST")
    
    if not result or not result.get("success"):
        await update.message.reply_text("❌ Ошибка при запуске модуля.")
        return
    
    session["active_module"] = "master_path"
    session["session_id"] = session_id
    session["state"] = "training"
    
    coach_message = result.get("coach_message", "")
    response_text = f"{coach_message}\n\n💬 _Напиши свой ответ в чат или отправь голосовое сообщение 🎤_"
    
    keyboard = [[InlineKeyboardButton("❌ Завершить", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(response_text, reply_markup=reply_markup, parse_mode="Markdown")


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle voice messages"""
    user_id = update.effective_user.id
    session = get_user_session(user_id)
    
    # Check if in training mode
    if session["state"] != "training" or not session["active_module"]:
        await update.message.reply_text(
            "🎤 Голосовые сообщения поддерживаются только в режиме тренировки.\n"
            "Используй /start для начала работы."
        )
        return
    
    try:
        # Show recording indicator
        await update.message.chat.send_action("record_voice")
        
        # Get voice file
        voice = update.message.voice
        voice_file = await context.bot.get_file(voice.file_id)
        
        # Download voice to temporary file
        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp_file:
            tmp_path = tmp_file.name
            await voice_file.download_to_drive(tmp_path)
        
        # Read audio data
        with open(tmp_path, "rb") as f:
            audio_data = f.read()
        
        # Clean up temp file
        os.unlink(tmp_path)
        
        # Show typing indicator
        await update.message.chat.send_action("typing")
        
        # Process through voice gateway
        # First, transcribe to text
        asr_response = await call_backend(
            "/voice/v1/asr",
            method="POST",
            files={"audio": ("voice.ogg", audio_data, "audio/ogg")}
        )
        
        if not asr_response or not asr_response.get("success"):
            await update.message.reply_text(
                "❌ Не удалось распознать голос. Попробуй ещё раз или напиши текстом."
            )
            return
        
        user_text = asr_response.get("text", "")
        
        # Show what was recognized
        await update.message.reply_text(f"🎤 Я услышал: _{user_text}_", parse_mode="Markdown")
        
        # Process through module backend
        module = session["active_module"]
        session_id = session["session_id"]
        
        result = await call_backend(
            f"/{module}/turn/{session_id}",
            method="POST",
            data={"text": user_text}
        )
        
        if not result or not result.get("success"):
            await update.message.reply_text(
                "❌ Ошибка при обработке сообщения. Попробуй ещё раз."
            )
            return
        
        # Get text response
        client_reply = result.get("client_reply", "")
        coach_tip = result.get("coach_tip") or result.get("coach_feedback") or result.get("coach_analysis") or result.get("coach_note", "")
        
        response_text = ""
        if client_reply:
            response_text += f"**Клиент:**\n{client_reply}\n\n"
        if coach_tip:
            response_text += f"**Коуч:**\n{coach_tip}\n\n"
        
        # Send text response first
        keyboard = [[InlineKeyboardButton("❌ Завершить", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(response_text, reply_markup=reply_markup, parse_mode="Markdown")
        
        # Try to send voice response if client replied
        if client_reply:
            await update.message.chat.send_action("record_voice")
            
            # Synthesize client reply to voice
            tts_response = await call_backend(
                "/voice/v1/tts",
                method="POST",
                data={"text": client_reply}
            )
            
            if tts_response and "audio" in tts_response:
                # Send voice message
                await update.message.reply_voice(
                    voice=tts_response["audio"],
                    caption="🎤 Голосовой ответ клиента"
                )
        
    except Exception as e:
        logger.error(f"Voice handling error: {e}")
        await update.message.reply_text(
            "❌ Ошибка при обработке голосового сообщения. Попробуй написать текстом."
        )


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    logger.error(f"Error: {context.error}")
    
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "Произошла ошибка. Попробуй команду /start для перезапуска."
        )


def main():
    """Start the bot"""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set in environment!")
        return
    
    logger.info("Starting SALESBOT Telegram Bot...")
    logger.info(f"Backend URL: {BACKEND_URL}")
    
    # Create application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Register handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("master", master_command))
    application.add_handler(CommandHandler("result", result_command))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))
    application.add_error_handler(error_handler)
    
    # Start bot
    logger.info("Bot started. Press Ctrl+C to stop.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
