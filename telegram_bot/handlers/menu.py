"""
Telegram Bot Menu Handler - Role-based menu system
"""
import logging
from typing import Dict, List, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


class MenuHandler:
    """Handles Telegram bot menu based on user roles"""
    
    def __init__(self):
        self.menus = self._initialize_menus()
    
    def _initialize_menus(self) -> Dict[str, List[Dict]]:
        """Initialize menu structure for each role"""
        return {
            "manager": [
                {
                    "id": "encyclopedia",
                    "text": "📘 Энциклопедия",
                    "callback": "menu_encyclopedia",
                    "description": "База знаний компании"
                },
                {
                    "id": "script_lab",
                    "text": "🧪 Script Lab",
                    "callback": "menu_script_lab",
                    "description": "Анализ скриптов продаж"
                },
                {
                    "id": "song_generator",
                    "text": "🎤 Генератор песен",
                    "callback": "menu_songs",
                    "description": "Создание персонализированных песен"
                },
                {
                    "id": "video_prompts",
                    "text": "🎬 Видео-промты",
                    "callback": "menu_video",
                    "description": "Генерация промтов для видео"
                },
                {
                    "id": "photo_animation",
                    "text": "📸 Фото / Мультфильмы",
                    "callback": "menu_photo",
                    "description": "Оживление фото и анимация"
                },
                {
                    "id": "training",
                    "text": "📚 Школа продаж",
                    "callback": "menu_training",
                    "description": "Обучающие материалы"
                },
                {
                    "id": "role",
                    "text": "👤 Роль: Менеджер",
                    "callback": "menu_role",
                    "description": "Текущая роль"
                }
            ],
            "generator": [
                {
                    "id": "encyclopedia",
                    "text": "📘 Энциклопедия",
                    "callback": "menu_encyclopedia",
                    "description": "База знаний (базовый доступ)"
                },
                {
                    "id": "script_lab",
                    "text": "🧪 Script Lab",
                    "callback": "menu_script_lab",
                    "description": "Анализ скриптов (базовый)"
                },
                {
                    "id": "song_generator",
                    "text": "🎤 Генератор текстов",
                    "callback": "menu_songs",
                    "description": "Создание текстов песен"
                },
                {
                    "id": "video_prompts",
                    "text": "🎬 Генератор видео-промтов",
                    "callback": "menu_video",
                    "description": "Промты для Sora/Veo3"
                },
                {
                    "id": "photo_animation",
                    "text": "📸 Продуктовые модули",
                    "callback": "menu_photo",
                    "description": "Креативные модули"
                },
                {
                    "id": "role",
                    "text": "👤 Роль: Генератор",
                    "callback": "menu_role",
                    "description": "Текущая роль"
                }
            ],
            "admin": [
                {
                    "id": "encyclopedia",
                    "text": "📘 Энциклопедия",
                    "callback": "menu_encyclopedia",
                    "description": "Полный доступ к базе знаний"
                },
                {
                    "id": "script_lab",
                    "text": "🧪 Script Lab",
                    "callback": "menu_script_lab",
                    "description": "Анализ и обучение скриптам"
                },
                {
                    "id": "song_generator",
                    "text": "🎤 Генератор песен",
                    "callback": "menu_songs",
                    "description": "Создание песен"
                },
                {
                    "id": "video_prompts",
                    "text": "🎬 Видео-промты",
                    "callback": "menu_video",
                    "description": "Генерация видео-промтов"
                },
                {
                    "id": "photo_animation",
                    "text": "📸 Фото / Мультфильмы",
                    "callback": "menu_photo",
                    "description": "Все продуктовые модули"
                },
                {
                    "id": "training",
                    "text": "📚 Школа продаж",
                    "callback": "menu_training",
                    "description": "Обучение команды"
                },
                {
                    "id": "analytics",
                    "text": "📊 Аналитика",
                    "callback": "menu_analytics",
                    "description": "Статистика и отчеты"
                },
                {
                    "id": "users",
                    "text": "👥 Управление",
                    "callback": "menu_users",
                    "description": "Управление командой"
                },
                {
                    "id": "role",
                    "text": "👤 Роль: Руководство",
                    "callback": "menu_role",
                    "description": "Полный доступ"
                }
            ]
        }
    
    def get_main_menu(self, role: str = "manager") -> InlineKeyboardMarkup:
        """
        Get main menu keyboard for a specific role.
        
        Args:
            role: User role (manager, generator, admin)
            
        Returns:
            InlineKeyboardMarkup with menu buttons
        """
        menu_items = self.menus.get(role, self.menus["manager"])
        
        # Create keyboard with 2 buttons per row
        keyboard = []
        row = []
        
        for item in menu_items:
            button = InlineKeyboardButton(
                text=item["text"],
                callback_data=item["callback"]
            )
            row.append(button)
            
            # 2 buttons per row
            if len(row) == 2:
                keyboard.append(row)
                row = []
        
        # Add remaining buttons
        if row:
            keyboard.append(row)
        
        return InlineKeyboardMarkup(keyboard)
    
    def get_encyclopedia_menu(self) -> InlineKeyboardMarkup:
        """Get encyclopedia submenu"""
        keyboard = [
            [
                InlineKeyboardButton("📖 Введение", callback_data="enc_intro"),
                InlineKeyboardButton("🏢 О компании", callback_data="enc_company")
            ],
            [
                InlineKeyboardButton("🌍 Рынки", callback_data="enc_markets"),
                InlineKeyboardButton("🧠 Психология", callback_data="enc_psychology")
            ],
            [
                InlineKeyboardButton("📦 Продукты", callback_data="enc_products"),
                InlineKeyboardButton("📝 Скрипты продаж", callback_data="enc_scripts")
            ],
            [
                InlineKeyboardButton("💬 Возражения", callback_data="enc_objections"),
                InlineKeyboardButton("💰 Допродажи", callback_data="enc_upsells")
            ],
            [
                InlineKeyboardButton("🔙 Назад", callback_data="menu_main")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def get_script_lab_menu(self) -> InlineKeyboardMarkup:
        """Get script lab submenu"""
        keyboard = [
            [
                InlineKeyboardButton("✍️ Анализировать скрипт", callback_data="script_analyze")
            ],
            [
                InlineKeyboardButton("📋 Примеры скриптов", callback_data="script_examples")
            ],
            [
                InlineKeyboardButton("📊 Критерии оценки", callback_data="script_criteria")
            ],
            [
                InlineKeyboardButton("🔙 Назад", callback_data="menu_main")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def get_song_generator_menu(self) -> InlineKeyboardMarkup:
        """Get song generator submenu"""
        keyboard = [
            [
                InlineKeyboardButton("🎵 Создать песню", callback_data="song_create")
            ],
            [
                InlineKeyboardButton("🎼 Жанры", callback_data="song_styles"),
                InlineKeyboardButton("💭 Настроения", callback_data="song_moods")
            ],
            [
                InlineKeyboardButton("📜 Мои песни", callback_data="song_list")
            ],
            [
                InlineKeyboardButton("🔙 Назад", callback_data="menu_main")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def get_video_prompts_menu(self) -> InlineKeyboardMarkup:
        """Get video prompts submenu"""
        keyboard = [
            [
                InlineKeyboardButton("🎬 Генерировать промты", callback_data="video_generate")
            ],
            [
                InlineKeyboardButton("🎯 Из песни", callback_data="video_from_song"),
                InlineKeyboardButton("✏️ Свой текст", callback_data="video_custom")
            ],
            [
                InlineKeyboardButton("🎨 Платформы", callback_data="video_platforms")
            ],
            [
                InlineKeyboardButton("🔙 Назад", callback_data="menu_main")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def get_photo_menu(self) -> InlineKeyboardMarkup:
        """Get photo/animation submenu"""
        keyboard = [
            [
                InlineKeyboardButton("📸 Оживить фото", callback_data="photo_animate")
            ],
            [
                InlineKeyboardButton("🎨 Мультфильм", callback_data="photo_cartoon")
            ],
            [
                InlineKeyboardButton("🎬 Монтаж видео", callback_data="photo_video")
            ],
            [
                InlineKeyboardButton("🔙 Назад", callback_data="menu_main")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def get_training_menu(self) -> InlineKeyboardMarkup:
        """Get training submenu"""
        keyboard = [
            [
                InlineKeyboardButton("📖 Основы продаж", callback_data="train_basics")
            ],
            [
                InlineKeyboardButton("🎯 10 шагов продажи", callback_data="train_steps")
            ],
            [
                InlineKeyboardButton("💬 Работа с возражениями", callback_data="train_objections")
            ],
            [
                InlineKeyboardButton("💰 Допродажи", callback_data="train_upsells")
            ],
            [
                InlineKeyboardButton("🧠 Психология клиента", callback_data="train_psychology")
            ],
            [
                InlineKeyboardButton("🔙 Назад", callback_data="menu_main")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def get_role_menu(self, current_role: str = "manager") -> InlineKeyboardMarkup:
        """Get role selection menu"""
        keyboard = [
            [
                InlineKeyboardButton(
                    "✅ Менеджер" if current_role == "manager" else "Менеджер",
                    callback_data="role_manager"
                )
            ],
            [
                InlineKeyboardButton(
                    "✅ Генератор" if current_role == "generator" else "Генератор",
                    callback_data="role_generator"
                )
            ],
            [
                InlineKeyboardButton(
                    "✅ Руководство" if current_role == "admin" else "Руководство",
                    callback_data="role_admin"
                )
            ],
            [
                InlineKeyboardButton("🔙 Назад", callback_data="menu_main")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    async def handle_menu_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle /menu command.
        
        Shows the main menu based on user's role.
        """
        # Get user role from context (default to manager)
        user_data = context.user_data or {}
        role = user_data.get("role", "manager")
        
        menu_keyboard = self.get_main_menu(role)
        
        welcome_text = self._get_welcome_text(role)
        
        if update.message:
            await update.message.reply_text(
                text=welcome_text,
                reply_markup=menu_keyboard
            )
        else:
            await update.callback_query.message.edit_text(
                text=welcome_text,
                reply_markup=menu_keyboard
            )
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle callback queries from menu buttons.
        """
        query = update.callback_query
        await query.answer()
        
        callback_data = query.data
        user_data = context.user_data or {}
        current_role = user_data.get("role", "manager")
        
        # Route to appropriate submenu
        if callback_data == "menu_main":
            keyboard = self.get_main_menu(current_role)
            text = self._get_welcome_text(current_role)
        
        elif callback_data == "menu_encyclopedia":
            keyboard = self.get_encyclopedia_menu()
            text = "📘 Энциклопедия компании\n\nВыберите раздел:"
        
        elif callback_data == "menu_script_lab":
            keyboard = self.get_script_lab_menu()
            text = "🧪 Script Lab\n\nАнализ и улучшение скриптов продаж:"
        
        elif callback_data == "menu_songs":
            keyboard = self.get_song_generator_menu()
            text = "🎤 Генератор песен\n\nСоздание персонализированных песен:"
        
        elif callback_data == "menu_video":
            keyboard = self.get_video_prompts_menu()
            text = "🎬 Генератор видео-промтов\n\nСоздание промтов для Sora/Veo3:"
        
        elif callback_data == "menu_photo":
            keyboard = self.get_photo_menu()
            text = "📸 Фото и мультфильмы\n\nКреативные модули:"
        
        elif callback_data == "menu_training":
            keyboard = self.get_training_menu()
            text = "📚 Школа продаж\n\nОбучающие материалы:"
        
        elif callback_data == "menu_role":
            keyboard = self.get_role_menu(current_role)
            text = "👤 Выбор роли\n\nВыберите свою роль в системе:"
        
        elif callback_data.startswith("role_"):
            new_role = callback_data.replace("role_", "")
            context.user_data["role"] = new_role
            keyboard = self.get_main_menu(new_role)
            text = f"✅ Роль изменена на: {self._get_role_name(new_role)}\n\n{self._get_welcome_text(new_role)}"
        
        else:
            # Default fallback
            keyboard = self.get_main_menu(current_role)
            text = "Функция в разработке. Выберите пункт меню:"
        
        await query.edit_message_text(
            text=text,
            reply_markup=keyboard
        )
    
    def _get_welcome_text(self, role: str) -> str:
        """Get welcome text for role"""
        welcome_texts = {
            "manager": (
                "👋 Добро пожаловать, Менеджер!\n\n"
                "У вас есть доступ ко всем инструментам продаж:\n"
                "• Энциклопедия компании\n"
                "• Анализ скриптов\n"
                "• Обучающие материалы\n"
                "• Генераторы контента\n\n"
                "Выберите нужный раздел:"
            ),
            "generator": (
                "👋 Добро пожаловать, Генератор!\n\n"
                "У вас есть доступ к креативным инструментам:\n"
                "• Генерация текстов песен\n"
                "• Создание видео-промтов\n"
                "• Продуктовые модули\n"
                "• Базовая энциклопедия\n\n"
                "Выберите нужный раздел:"
            ),
            "admin": (
                "👋 Добро пожаловать, Руководство!\n\n"
                "У вас полный доступ ко всем модулям:\n"
                "• Все инструменты команды\n"
                "• Аналитика и отчеты\n"
                "• Управление пользователями\n\n"
                "Выберите нужный раздел:"
            )
        }
        return welcome_texts.get(role, welcome_texts["manager"])
    
    def _get_role_name(self, role: str) -> str:
        """Get readable role name"""
        role_names = {
            "manager": "Менеджер",
            "generator": "Генератор",
            "admin": "Руководство"
        }
        return role_names.get(role, role)


# Global instance
_menu_handler = None


def get_menu_handler() -> MenuHandler:
    """Get menu handler instance"""
    global _menu_handler
    if _menu_handler is None:
        _menu_handler = MenuHandler()
    return _menu_handler
