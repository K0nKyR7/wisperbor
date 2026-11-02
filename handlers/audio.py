import os
import tempfile
import logging
from aiogram import Bot, F, Router
from aiogram.enums import ChatAction, ChatType
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from services.transcriber import transcriber
from keyboards import get_transcription_inline_keyboard

logger = logging.getLogger(__name__)

router = Router(name="audio_router")

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 МБ — лимит Telegram Bot API на скачивание


def split_text(text: str, max_chars: int = 4000) -> list[str]:
    """Разбивает длинный текст на части с учетом границ строк и пробелов."""
    if len(text) <= max_chars:
        return [text]

    chunks = []
    while len(text) > max_chars:
        split_idx = text.rfind("\n", 0, max_chars)
        if split_idx == -1:
            split_idx = text.rfind(" ", 0, max_chars)
        if split_idx == -1:
            split_idx = max_chars
        chunks.append(text[:split_idx].strip())
        text = text[split_idx:].strip()

    if text:
        chunks.append(text)
    return chunks


def extract_pure_text(message: Message) -> str:
    """Извлекает чистый распознанный текст без служебных заголовков."""
    raw_text = message.text or message.caption or ""
    parts = raw_text.split("\n\n", 1)
    return parts[1].strip() if len(parts) > 1 else raw_text.strip()


async def process_media_transcription(
    message: Message,
    bot: Bot,
    file_id: str,
    suffix: str,
    media_title: str,
    reply_target: Message | None = None,
):
    target = reply_target or message
    status_msg = await target.reply("⏳ Скачиваю и расшифровываю...")
    await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)

    temp_path = None
    try:
        tg_file = await bot.get_file(file_id)

        if tg_file.file_size and tg_file.file_size > MAX_FILE_SIZE:
            await status_msg.edit_text(
                "❌ Файл превышает лимит в 20 МБ. Telegram Bot API не поддерживает скачивание файлов большего размера."
            )
            return

        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            temp_path = tmp.name

        await bot.download_file(tg_file.file_path, destination=temp_path)

        recognized_text = await transcriber.transcribe(
            file_path=temp_path,
            filename=f"media{suffix}",
        )

        if not recognized_text:
            await status_msg.edit_text("🤷 В сообщении не удалось распознать разборчивую русскую речь.")
            return

        # Владельцем считаем автора медиа
        owner_id = target.from_user.id if target.from_user else 0
        keyboard = get_transcription_inline_keyboard(owner_id=owner_id)

        header = f"📝 **Расшифровка ({media_title}):**\n\n"
        full_text = header + recognized_text
        chunks = split_text(full_text)

        if len(chunks) == 1:
            await status_msg.edit_text(chunks[0], parse_mode="Markdown", reply_markup=keyboard)
        else:
            await status_msg.edit_text(chunks[0], parse_mode="Markdown")
            for i, chunk in enumerate(chunks[1:]):
                is_last = (i == len(chunks) - 2)
                await target.reply(
                    chunk,
                    reply_markup=keyboard if is_last else None,
                )

    except Exception as e:
        logger.exception("Ошибка при обработке аудио/видео:")
        await status_msg.edit_text(f"❌ Произошла ошибка при расшифровке:\n`{str(e)}`", parse_mode="Markdown")
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass


# ==========================================
# 1. ЛИЧНЫЕ СООБЩЕНИЯ (Автоматическая работа)
# ==========================================

@router.message(F.chat.type == ChatType.PRIVATE, F.voice)
async def handle_private_voice(message: Message, bot: Bot):
    await process_media_transcription(
        message=message,
        bot=bot,
        file_id=message.voice.file_id,
        suffix=".ogg",
        media_title="Голосовое сообщение",
    )


@router.message(F.chat.type == ChatType.PRIVATE, F.video_note)
async def handle_private_video_note(message: Message, bot: Bot):
    await process_media_transcription(
        message=message,
        bot=bot,
        file_id=message.video_note.file_id,
        suffix=".mp4",
        media_title="Кружочек",
    )


@router.message(F.chat.type == ChatType.PRIVATE, F.audio)
async def handle_private_audio(message: Message, bot: Bot):
    filename = message.audio.file_name or "audio.mp3"
    _, ext = os.path.splitext(filename)
    if not ext:
        ext = ".mp3"

    await process_media_transcription(
        message=message,
        bot=bot,
        file_id=message.audio.file_id,
        suffix=ext.lower(),
        media_title="Аудиозапись",
    )


@router.message(F.chat.type == ChatType.PRIVATE, F.video)
async def handle_private_video(message: Message, bot: Bot):
    await process_media_transcription(
        message=message,
        bot=bot,
        file_id=message.video.file_id,
        suffix=".mp4",
        media_title="Видео",
    )


# =======================================================
# 2. ГРУППОВЫЕ ЧАТЫ (Работа только по ответу с командой /t)
# =======================================================

@router.message(
    F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}),
    Command("t", "text"),
)
@router.message(
    F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}),
    F.text.lower().contains("@soundtextingbot"),
)
async def handle_group_trigger(message: Message, bot: Bot):
    """
    В группах бот реагирует только когда пользователь делает Reply (ответ)
    на голосовое или кружочек с командой /t или упоминанием бота.
    """
    reply = message.reply_to_message
    if not reply:
        await message.reply(
            "💡 Чтобы расшифровать аудио или кружочек в группе, ответьте на него (**Reply**) командой `/t`.",
            parse_mode="Markdown",
        )
        return

    # Проверяем, какой тип медиа был в сообщении, на которое ответили
    if reply.voice:
        await process_media_transcription(
            message=message,
            bot=bot,
            file_id=reply.voice.file_id,
            suffix=".ogg",
            media_title="Голосовое сообщение",
            reply_target=reply,
        )
    elif reply.video_note:
        await process_media_transcription(
            message=message,
            bot=bot,
            file_id=reply.video_note.file_id,
            suffix=".mp4",
            media_title="Кружочек",
            reply_target=reply,
        )
    elif reply.audio:
        filename = reply.audio.file_name or "audio.mp3"
        _, ext = os.path.splitext(filename)
        await process_media_transcription(
            message=message,
            bot=bot,
            file_id=reply.audio.file_id,
            suffix=ext.lower() if ext else ".mp3",
            media_title="Аудиозапись",
            reply_target=reply,
        )
    elif reply.video:
        await process_media_transcription(
            message=message,
            bot=bot,
            file_id=reply.video.file_id,
            suffix=".mp4",
            media_title="Видео",
            reply_target=reply,
        )
    else:
        await message.reply("⚠️ В сообщении, на которое вы ответили, нет голосового или видеосообщения.")


# ==========================================
# 3. ИНТЕРАКТИВНЫЕ КНОПКИ (Удаление, Саммари и др.)
# ==========================================

@router.callback_query(F.data.startswith("btn_del"))
async def callback_delete(callback: CallbackQuery, bot: Bot):
    """Удаляет сообщение с расшифровкой (с проверкой прав в группах)."""
    owner_id_str = callback.data.split(":")[1] if ":" in callback.data else "0"
    owner_id = int(owner_id_str) if owner_id_str.isdigit() else 0

    if callback.message.chat.type in (ChatType.GROUP, ChatType.SUPERGROUP):
        user_id = callback.from_user.id
        # Автор медиа или админ группы имеют право удалять
        if owner_id != 0 and user_id != owner_id:
            try:
                member = await bot.get_chat_member(callback.message.chat.id, user_id)
                if member.status not in ("creator", "administrator"):
                    await callback.answer("❌ Удалить может только автор голосового или администратор группы.", show_alert=True)
                    return
            except Exception:
                await callback.answer("❌ Недостаточно прав для удаления.", show_alert=True)
                return

    try:
        await callback.message.delete()
    except Exception:
        await callback.answer("Не удалось удалить сообщение.", show_alert=True)


@router.callback_query(F.data == "btn_summarize")
async def callback_summarize(callback: CallbackQuery, bot: Bot):
    """Делает краткую выжимку (тезисы) расшифрованного текста."""
    target_text = extract_pure_text(callback.message)
    if not target_text:
        await callback.answer("Нет текста для анализа.", show_alert=True)
        return

    await callback.answer("Составляю выжимку...")
    await bot.send_chat_action(chat_id=callback.message.chat.id, action=ChatAction.TYPING)
    wait_msg = await callback.message.reply("🧠 Анализирую текст и формирую главные тезисы...")

    try:
        summary = await transcriber.summarize(target_text)
        await wait_msg.edit_text(f"📋 **Краткая выжимка (Саммари):**\n\n{summary}", parse_mode="Markdown")
    except Exception as e:
        logger.exception("Ошибка при генерации выжимки:")
        await wait_msg.edit_text(f"❌ Ошибка при создании выжимки:\n`{str(e)}`", parse_mode="Markdown")


@router.callback_query(F.data == "btn_clean")
async def callback_clean(callback: CallbackQuery, bot: Bot):
    """Очищает расшифровку от слов-паразитов, заиканий и оговорок."""
    target_text = extract_pure_text(callback.message)
    if not target_text:
        await callback.answer("Нет текста для анализа.", show_alert=True)
        return

    await callback.answer("Очищаю от слов-паразитов...")
    await bot.send_chat_action(chat_id=callback.message.chat.id, action=ChatAction.TYPING)
    wait_msg = await callback.message.reply("✨ Очищаю речь от паразитов и оговорок...")

    try:
        cleaned = await transcriber.clean_speech(target_text)
        await wait_msg.edit_text(f"✨ **Очищенный текст:**\n\n{cleaned}", parse_mode="Markdown")
    except Exception as e:
        logger.exception("Ошибка при очистке речи:")
        await wait_msg.edit_text(f"❌ Ошибка при очистке речи:\n`{str(e)}`", parse_mode="Markdown")


@router.callback_query(F.data == "btn_tasks")
async def callback_tasks(callback: CallbackQuery, bot: Bot):
    """Извлекает из речи задачи, дедлайны и договоренности."""
    target_text = extract_pure_text(callback.message)
    if not target_text:
        await callback.answer("Нет текста для анализа.", show_alert=True)
        return

    await callback.answer("Ищу задачи и договоренности...")
    await bot.send_chat_action(chat_id=callback.message.chat.id, action=ChatAction.TYPING)
    wait_msg = await callback.message.reply("📋 Ищу задачи, поручения и договоренности...")

    try:
        tasks = await transcriber.extract_tasks(target_text)
        await wait_msg.edit_text(f"✅ **Задачи и договоренности:**\n\n{tasks}", parse_mode="Markdown")
    except Exception as e:
        logger.exception("Ошибка при поиске задач:")
        await wait_msg.edit_text(f"❌ Ошибка при извлечении задач:\n`{str(e)}`", parse_mode="Markdown")
