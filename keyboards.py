from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)


def get_main_reply_keyboard() -> ReplyKeyboardMarkup:
    """Главная нижняя панель с кнопками быстрого доступа."""
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
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_transcription_inline_keyboard(record_id: int = 0) -> InlineKeyboardMarkup:
    """Inline-кнопки под результатом расшифровки аудио/видео."""
    buttons = [
        [
            InlineKeyboardButton(text="📝 Сделать выжимку (Саммари)", callback_data=f"btn_sum:{record_id}"),
            InlineKeyboardButton(text="🗑 Удалить", callback_data="btn_delete"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
