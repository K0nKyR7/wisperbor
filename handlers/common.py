from aiogram import Router, F
from aiogram.enums import ChatType
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from config import config
from keyboards import get_main_reply_keyboard, get_start_inline_keyboard

router = Router(name="common_router")


@router.message(CommandStart())
async def handle_start(message: Message):
    is_private = (message.chat.type == ChatType.PRIVATE)
    
    greeting = (
        "👋 **Привет! Я бот Wisperbor** — расшифровываю голосовые сообщения и видео-кружочки в текст.\n\n"
        "✨ **Возможности:**\n"
        "• 👥 **Работа в группах:** добавьте меня в чат с друзьями или коллегами!\n"
        "• 📝 **Выжимка:** краткие тезисы любого длинного войса.\n"
        "• ✨ **Очистка речи:** удаление «э-э», «ну», «типа» и повторов.\n"
        "• ✅ **Список задач:** автоматический поиск договоренностей и To-Do.\n\n"
        "🔒 **100% Приватность:** сообщения нигде не сохраняются."
    )

    if is_private:
        await message.answer(
            greeting,
            parse_mode="Markdown",
            reply_markup=get_main_reply_keyboard(),
        )
        await message.answer(
            "Выберите раздел или просто отправьте аудио/видео:",
            reply_markup=get_start_inline_keyboard(),
        )
    else:
        await message.reply(
            greeting + "\n\n🚀 Просто отправляйте в эту группу голосовые и кружочки — я буду расшифровывать их прямо здесь!",
            parse_mode="Markdown",
        )


@router.message(Command("help"))
@router.message(F.text == "📖 Как пользоваться")
async def handle_help(message: Message):
    help_text = (
        "💡 **Как пользоваться ботом:**\n\n"
        "1. **В личных сообщениях:** перешлите сюда войс/кружочек или запишите новый.\n"
        "2. **В групповых чатах:** добавьте бота в группу. Когда кто-то запишет голосовое или кружочек, бот автоматически ответит на него расшифровкой.\n"
        "3. **Кнопки под текстом:**\n"
        "   • 📝 *Выжимка* — главная суть без воды\n"
        "   • ✨ *Очистить речь* — чистый грамотный текст без паразитов\n"
        "   • ✅ *Задачи* — список поручений и договоренностей\n"
        "   • 🗑 *Удалить* — скрыть сообщение\n\n"
        "🔒 Все сообщения приватны, история не сохраняется.\n"
        "⚠️ Максимальный размер файла для Telegram Bot API — 20 МБ."
    )
    await message.answer(help_text, parse_mode="Markdown")


@router.message(F.text == "✨ Возможности")
async def handle_features(message: Message):
    features_text = (
        "✨ **Все возможности Wisperbor:**\n\n"
        "• ⚡ **Мгновенно:** обработка 1-минутной записи занимает 1–2 секунды.\n"
        "• 👥 **Групповые чаты:** распознавание речи прямо в беседе с коллегами или друзьями.\n"
        "• 🎯 **Whisper V3 Turbo:** высокая точность на русском языке и пунктуация.\n"
        "• 🧠 **Интеллектуальный редактор:** выжимка, поиск задач и удаление слов-паразитов.\n"
        "• 🔒 **Приватность:** файлы удаляются сразу после обработки."
    )
    await message.answer(features_text, parse_mode="Markdown")


@router.message(F.text == "⚙️ Статус и модель")
async def handle_status(message: Message):
    status_text = (
        "⚙️ **Текущие настройки бота:**\n\n"
        f"• **Движок распознавания:** {config.stT_provider.upper()} ({config.groq_model})\n"
        "• **Язык распознавания:** Русский (RU)\n"
        "• **Поддержка групп:** 🟢 Включена\n"
        "• **Статус:** 🟢 Онлайн и готов к работе"
    )
    await message.answer(status_text, parse_mode="Markdown")


@router.callback_query(F.data == "btn_help")
async def callback_help(callback: CallbackQuery):
    help_text = (
        "📖 **Быстрая инструкция:**\n\n"
        "Отправьте боту любое голосовое сообщение или кружочек. Через 1-2 секунды вы получите расшифровку и умные кнопки обработки!"
    )
    await callback.message.answer(help_text, parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data == "btn_tips")
async def callback_tips(callback: CallbackQuery):
    tips_text = (
        "💡 **Советы для наилучшего качества:**\n\n"
        "• Старайтесь говорить внятно и без сильного фонового ветра/шума.\n"
        "• Кружочки обрабатываются так же качественно, как и обычные аудиозаписи.\n"
        "• Используйте кнопку «✨ Очистить речь», если наговорили с паузами и оговорками."
    )
    await callback.message.answer(tips_text, parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data == "btn_groups")
async def callback_groups(callback: CallbackQuery):
    groups_text = (
        "👥 **Как добавить бота в группу:**\n\n"
        "1. Откройте профиль бота [@soundtextingbot](https://t.me/soundtextingbot).\n"
        "2. Нажмите **Добавить в группу / канал** и выберите нужный чат.\n"
        "3. **Важно для работы в группе:**\n"
        "   Чтобы бот слышал голосовые сообщения всех участников, в [@BotFather](https://t.me/BotFather) отправьте команду `/setprivacy`, выберите бота и нажмите **Disable** (или просто назначьте бота администратором группы)."
    )
    await callback.message.answer(groups_text, parse_mode="Markdown")
    await callback.answer()
