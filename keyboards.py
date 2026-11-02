from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)


def get_main_reply_keyboard() -> ReplyKeyboardMarkup:
    """Главная нижняя панель с кнопками быстрого доступа (только для личных сообщений)."""
    buttons = [
        [
            KeyboardButton(text="📖 Как пользоваться"),
            KeyboardButton(text="✨ Возможности"),
        ],
        [
            KeyboardButton(text="⚙️ Статус и модель"),
        ],
    ]
    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        input_field_placeholder="Отправьте голосовое или кружочек...",
    )


def get_start_inline_keyboard() -> InlineKeyboardMarkup:
    """Inline-кнопки в стартовом приветствии."""
    buttons = [
        [
            InlineKeyboardButton(text="📖 Инструкция", callback_data="btn_help"),
            InlineKeyboardButton(text="💡 Советы по качеству", callback_data="btn_tips"),
        ],
        [
            InlineKeyboardButton(text="👥 Использование в группах", callback_data="btn_groups"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_transcription_inline_keyboard(owner_id: int = 0) -> InlineKeyboardMarkup:
    """Inline-кнопки под результатом расшифровки аудио/видео."""
    buttons = [
        [
            InlineKeyboardButton(text="📝 Выжимка", callback_data="btn_summarize"),
            InlineKeyboardButton(text="✨ Очистить речь", callback_data="btn_clean"),
        ],
        [
            InlineKeyboardButton(text="✅ Задачи / To-Do", callback_data="btn_tasks"),
            InlineKeyboardButton(text="🌐 На английский", callback_data="btn_translate"),
        ],
        [
            InlineKeyboardButton(text="🗑 Удалить", callback_data=f"btn_del:{owner_id}"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
