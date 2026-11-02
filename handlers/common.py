from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from config import config
from keyboards import get_main_reply_keyboard, get_start_inline_keyboard

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
    # Отправляем inline-кнопки
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
        "• ✂️ **Без ограничений на длину:** длинные тексты автоматически разбиваются на части."
    )
    await message.answer(features_text, parse_mode="Markdown")


@router.message(F.text == "⚙️ Статус и модель")
async def handle_status(message: Message):
    status_text = (
        "⚙️ **Текущие настройки бота:**\n\n"
        f"• **Движок распознавания:** {config.stT_provider.upper()}\n"
        f"• **Модель речи:** `{config.groq_model if config.stT_provider == 'groq' else 'whisper-1'}`\n"
        "• **Язык распознавания:** Русский (RU)\n"
        "• **Статус:** 🟢 Онлайн и готов к работе"
    )
    await message.answer(status_text, parse_mode="Markdown")


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
