import os
import tempfile
import logging
from aiogram import Bot, F, Router
from aiogram.enums import ChatAction, ChatType
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
):
    # В группах всегда отвечаем на конкретное сообщение (reply)
    status_msg = await message.reply("⏳ Скачиваю и расшифровываю...")
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

        owner_id = message.from_user.id if message.from_user else 0
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
                await message.reply(
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


@router.message(F.voice)
async def handle_voice(message: Message, bot: Bot):
    await process_media_transcription(
        message=message,
        bot=bot,
        file_id=message.voice.file_id,
        suffix=".ogg",
        media_title="Голосовое сообщение",
    )


@router.message(F.video_note)
async def handle_video_note(message: Message, bot: Bot):
    await process_media_transcription(
        message=message,
        bot=bot,
        file_id=message.video_note.file_id,
        suffix=".mp4",
        media_title="Кружочек",
    )


@router.message(F.audio)
async def handle_audio(message: Message, bot: Bot):
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


@router.message(F.video)
async def handle_video(message: Message, bot: Bot):
    await process_media_transcription(
        message=message,
        bot=bot,
        file_id=message.video.file_id,
        suffix=".mp4",
        media_title="Видео",
    )


@router.callback_query(F.data.startswith("btn_del"))
async def callback_delete(callback: CallbackQuery, bot: Bot):
    """Удаляет сообщение с расшифровкой (с проверкой прав в группах)."""
    owner_id_str = callback.data.split(":")[1] if ":" in callback.data else "0"
    owner_id = int(owner_id_str) if owner_id_str.isdigit() else 0

    # Если действие в группе: удалять может автор или админ чата
    if callback.message.chat.type in (ChatType.GROUP, ChatType.SUPERGROUP):
        user_id = callback.from_user.id
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


@router.callback_query(F.data == "btn_translate")
async def callback_translate(callback: CallbackQuery, bot: Bot):
    """Переводит расшифровку на английский язык."""
    target_text = extract_pure_text(callback.message)
    if not target_text:
        await callback.answer("Нет текста для анализа.", show_alert=True)
        return

    await callback.answer("Перевожу на английский...")
    await bot.send_chat_action(chat_id=callback.message.chat.id, action=ChatAction.TYPING)
    wait_msg = await callback.message.reply("🌐 Перевожу на английский язык...")

    try:
        translated = await transcriber.translate_text(target_text, target_lang="английский")
        await wait_msg.edit_text(f"🌐 **English Translation:**\n\n{translated}", parse_mode="Markdown")
    except Exception as e:
        logger.exception("Ошибка при переводе:")
        await wait_msg.edit_text(f"❌ Ошибка при переводе:\n`{str(e)}`", parse_mode="Markdown")
