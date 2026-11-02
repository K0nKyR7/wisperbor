import os
import tempfile
import logging
from aiogram import Bot, F, Router
from aiogram.enums import ChatAction
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


async def process_media_transcription(
    message: Message,
    bot: Bot,
    file_id: str,
    suffix: str,
    media_title: str,
):
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

        header = f"📝 **Расшифровка ({media_title}):**\n\n"
        full_text = header + recognized_text
        chunks = split_text(full_text)

        keyboard = get_transcription_inline_keyboard()

        # Выводим сообщение с кнопками
        if len(chunks) == 1:
            await status_msg.edit_text(chunks[0], parse_mode="Markdown", reply_markup=keyboard)
        else:
            await status_msg.edit_text(chunks[0], parse_mode="Markdown")
            for i, chunk in enumerate(chunks[1:]):
                is_last = (i == len(chunks) - 2)
                await message.answer(
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


@router.callback_query(F.data == "btn_delete")
async def callback_delete(callback: CallbackQuery):
    """Удаляет сообщение с расшифровкой."""
    try:
        await callback.message.delete()
    except Exception:
        await callback.answer("Не удалось удалить сообщение.", show_alert=True)


@router.callback_query(F.data == "btn_summarize")
async def callback_summarize(callback: CallbackQuery, bot: Bot):
    """Делает краткую выжимку (саммари) расшифрованного текста."""
    message_text = callback.message.text or callback.message.caption or ""

    # Убираем заголовок "Расшифровка (...):", если он есть
    lines = message_text.split("\n\n", 1)
    target_text = lines[1] if len(lines) > 1 else message_text

    if not target_text.strip():
        await callback.answer("Нет текста для анализа.", show_alert=True)
        return

    await callback.answer("Готовлю краткую выжимку...")
    await bot.send_chat_action(chat_id=callback.message.chat.id, action=ChatAction.TYPING)

    wait_msg = await callback.message.reply("🧠 Анализирую текст и формирую главные тезисы...")

    try:
        summary = await transcriber.summarize(target_text)
        formatted_summary = f"📋 **Краткая выжимка (Саммари):**\n\n{summary}"
        await wait_msg.edit_text(formatted_summary, parse_mode="Markdown")
    except Exception as e:
        logger.exception("Ошибка при генерации выжимки:")
        await wait_msg.edit_text(f"❌ Не удалось сделать выжимку: `{str(e)}`", parse_mode="Markdown")
