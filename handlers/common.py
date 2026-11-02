import os
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, FSInputFile
from config import config
from keyboards import get_main_reply_keyboard, get_start_inline_keyboard
from services.database import get_stats, get_recent_logs, DB_PATH

router = Router(name="common_router")


@router.message(CommandStart())
async def handle_start(message: Message):
    greeting = (
        "👋 **Привет! Я бот Wisperbor** — расшифровываю голосовые сообщения и видео-кружочки в текст.\n\n"
        "🎙 **Что я умею принимать:**\n"
        "• Голосовые сообщения (Voice)\n"
        "• Видеосообщения («кружочки» / Video Note)\n"
        "• Аудиофайлы и диктофонные записи\n"
        "• Видеофайлы (до 20 МБ)\n\n"
        "🚀 Просто перешлите мне сообщение или запишите новое прямо в этот чат!"
    )
    await message.answer(
        greeting,
        parse_mode="Markdown",
        reply_markup=get_main_reply_keyboard(),
    )
    await message.answer(
        "Выберите раздел или отправьте аудио/видео:",
        reply_markup=get_start_inline_keyboard(),
    )


@router.message(Command("help"))
@router.message(F.text == "📖 Как пользоваться")
async def handle_help(message: Message):
    help_text = (
        "💡 **Как пользоваться ботом:**\n\n"
        "1. Перешлите сюда голосовое сообщение или видео-кружочек из любого чата.\n"
        "2. Либо запишите аудио/видео прямо в диалоге с ботом.\n"
        "3. Бот за 1-2 секунды превратит речь в чистый русский текст.\n"
        "4. Под расшифровкой вы можете нажать **«📝 Сделать выжимку»**, чтобы получить ключевые тезисы.\n\n"
        "⚠️ Максимальный размер файла для Telegram Bot API — 20 МБ."
    )
    await message.answer(help_text, parse_mode="Markdown")


@router.message(F.text == "✨ Возможности")
async def handle_features(message: Message):
    features_text = (
        "✨ **Возможности Wisperbor:**\n\n"
        "• ⚡ **Сверхбыстрая скорость:** обработка 1-минутной записи занимает всего 1–2 секунды.\n"
        "• 🎯 **Точность Whisper V3:** корректная расстановка знаков препинания и заглавных букв.\n"
        "• 📝 **Умное саммари:** кнопка для автоматического выделения сути длинных сообщений.\n"
        "• 💾 **История:** сохранение всех расшифровок в локальную базу данных.\n"
        "• ✂️ **Без ограничений на длину:** длинные тексты автоматически разбиваются на части."
    )
    await message.answer(features_text, parse_mode="Markdown")


@router.message(F.text == "⚙️ Статус и модель")
async def handle_status(message: Message):
    total_msgs, total_users = await get_stats()
    status_text = (
        "⚙️ **Текущие настройки бота:**\n\n"
        f"• **Движок распознавания:** {config.stT_provider.upper()}\n"
        f"• **Модель речи:** `{config.groq_model if config.stT_provider == 'groq' else 'whisper-1'}`\n"
        "• **Язык распознавания:** Русский (RU)\n"
        "• **Статус:** 🟢 Онлайн и готов к работе\n\n"
        "📊 **Статистика базы данных:**\n"
        f"• Обработано записей: **{total_msgs}**\n"
        f"• Пользователей в базе: **{total_users}**\n\n"
        "Дополнительные команды:\n"
        "• `/history` — посмотреть последние сообщения\n"
        "• `/export` — скачать файл базы данных (.db)"
    )
    await message.answer(status_text, parse_mode="Markdown")


@router.message(Command("history"))
@router.message(Command("logs"))
async def handle_history(message: Message):
    """Показывает последние расшифрованные сообщения из базы данных."""
    logs = await get_recent_logs(limit=5)
    if not logs:
        await message.answer("📭 В базе данных пока нет сохранённых сообщений.")
        return

    text_parts = ["📜 **Последние сообщения в базе данных:**\n"]
    for row in logs:
        user_info = row.get("username") or row.get("full_name") or f"ID {row['user_id']}"
        date = row["created_at"]
        m_type = row["media_type"]
        preview = row["recognized_text"]
        if len(preview) > 150:
            preview = preview[:150] + "..."

        text_parts.append(
            f"👤 **{user_info}** ({date})\n"
            f"📁 {m_type}\n"
            f"💬 _{preview}_\n"
            "───────────────"
        )

    await message.answer("\n".join(text_parts), parse_mode="Markdown")


@router.message(Command("export"))
async def handle_export(message: Message):
    """Выгружает файл базы данных SQLite прямо в чат."""
    if not os.path.exists(DB_PATH):
        await message.answer("Файл базы данных пока не создан.")
        return

    file = FSInputFile(DB_PATH, filename="transcriptions.db")
    await message.answer_document(file, caption="📁 Локальная база данных всех расшифровок (SQLite).")


@router.callback_query(F.data == "btn_help")
async def callback_help(callback: CallbackQuery):
    help_text = (
        "📖 **Быстрая инструкция:**\n\n"
        "Отправьте боту любое голосовое сообщение или кружочек. Через 1-2 секунды вы получите расшифровку!"
    )
    await callback.message.answer(help_text, parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data == "btn_tips")
async def callback_tips(callback: CallbackQuery):
    tips_text = (
        "💡 **Советы для наилучшего качества:**\n\n"
        "• Старайтесь говорить внятно и без сильного фонового ветра/шума.\n"
        "• Кружочки обрабатываются так же качественно, как и обычные аудиозаписи.\n"
        "• Если собеседник наговорил 5 минут, используйте кнопку «Сделать выжимку» под результатом."
    )
    await callback.message.answer(tips_text, parse_mode="Markdown")
    await callback.answer()
