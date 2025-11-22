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
    
    welcome_text = f"""👋 Привет, {user.first_name}!

Добро пожаловать в **SALESBOT** — систему тренировок для менеджеров проекта "На Счастье"!

Здесь ты научишься:
✨ Тёплому общению с клиентами
💬 Отработке возражений
💎 Допродажам без давления
🎯 Полному циклу сделки

💬 Пиши текстом или 🎤 отправляй голосовые сообщения!

**Выбери свой уровень:**"""
    
    keyboard = [
        [InlineKeyboardButton("🌱 Я новичок", callback_data="level_beginner")],
        [InlineKeyboardButton("📈 У меня есть база", callback_data="level_advanced")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="Markdown")


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    if data == "level_beginner":
        await show_beginner_menu(query, user_id)
    elif data == "level_advanced":
        await show_advanced_menu(query, user_id)
    elif data.startswith("module_"):
        module = data.replace("module_", "")
        await start_training_module(query, user_id, module)
    elif data == "main_menu":
        await show_main_menu(query, user_id)


async def show_beginner_menu(query, user_id: int):
    """Show beginner training menu"""
    text = """🌱 **Путь новичка**

Рекомендую начать с этих модулей:"""
    
    keyboard = [
        [InlineKeyboardButton("🎯 Путь Мастера", callback_data="module_master_path")],
        [InlineKeyboardButton("🛡️ Возражения", callback_data="module_objections")],
        [InlineKeyboardButton("🎪 Арена (свободная практика)", callback_data="module_arena")],
        [InlineKeyboardButton("« Назад", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")


async def show_advanced_menu(query, user_id: int):
    """Show advanced training menu"""
    text = """📈 **Продвинутый уровень**

Выбери нужный модуль:"""
    
    keyboard = [
        [InlineKeyboardButton("🎯 Путь Мастера", callback_data="module_master_path")],
        [InlineKeyboardButton("🛡️ Возражения", callback_data="module_objections")],
        [InlineKeyboardButton("💎 Допродажи", callback_data="module_upsell")],
        [InlineKeyboardButton("🎪 Арена", callback_data="module_arena")],
        [InlineKeyboardButton("📝 Экзамен", callback_data="module_exam")],
        [InlineKeyboardButton("« Назад", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")


async def show_main_menu(query, user_id: int):
    """Show main menu"""
    text = """**SALESBOT** — Главное меню

Выбери свой уровень:"""
    
    keyboard = [
        [InlineKeyboardButton("🌱 Я новичок", callback_data="level_beginner")],
        [InlineKeyboardButton("📈 У меня есть база", callback_data="level_advanced")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")


async def start_training_module(query, user_id: int, module: str):
    """Start a training module"""
    session = get_user_session(user_id)
    session_id = f"tg_{user_id}_{module}"
    
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


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user messages during training"""
    user_id = update.effective_user.id
    session = get_user_session(user_id)
    
    # Check if in training mode
    if session["state"] != "training" or not session["active_module"]:
        await update.message.reply_text(
            "Используй /start для начала работы или выбери модуль тренировки."
        )
        return
    
    user_text = update.message.text
    module = session["active_module"]
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
