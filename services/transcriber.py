import os
import aiofiles
from groq import AsyncGroq
from openai import AsyncOpenAI
from config import config


class TranscriberService:
    def __init__(self):
        self.provider = config.stT_provider
        if self.provider == "groq":
            self.groq_client = AsyncGroq(api_key=config.groq_api_key)
        elif self.provider == "openai":
            self.openai_client = AsyncOpenAI(api_key=config.openai_api_key)
        else:
            raise ValueError(f"Неизвестный STT провайдер: {self.provider}")

    async def transcribe(self, file_path: str, filename: str) -> str:
        """
        Отправляет аудио/видео файл в Whisper API (Groq или OpenAI)
        и возвращает распознанный текст на русском языке.
        """
        async with aiofiles.open(file_path, "rb") as f:
            file_bytes = await f.read()

        file_payload = (filename, file_bytes)

        if self.provider == "groq":
            transcription = await self.groq_client.audio.transcriptions.create(
                file=file_payload,
                model=config.groq_model,
                language="ru",
                temperature=0.0,
            )
            return transcription.text.strip()

        elif self.provider == "openai":
            transcription = await self.openai_client.audio.transcriptions.create(
                file=file_payload,
                model="whisper-1",
                language="ru",
                temperature=0.0,
            )
            return transcription.text.strip()

        return ""

    async def summarize(self, text: str) -> str:
        """
        Создает структурированную краткую выжимку переданного текста на русском языке.
        """
        system_prompt = (
            "Ты умный аналитик. Твоя задача — сделать краткую, четкую и структурированную выжимку "
            "(главные тезисы, ключевые мысли, договоренности или задачи) из расшифровки голосового сообщения на русском языке. "
            "Используй маркированный список. Будь краток и пиши по существу без вводных фраз."
        )

        if self.provider == "groq":
            groq_llm_models = ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.8-27b"]
            last_err = None
            for model_name in groq_llm_models:
                try:
                    response = await self.groq_client.chat.completions.create(
                        model=model_name,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": f"Текст для выжимки:\n\n{text}"},
                        ],
                        temperature=0.3,
                    )
                    return response.choices[0].message.content.strip()
                except Exception as err:
                    last_err = err
                    continue
            if last_err:
                raise last_err

        elif self.provider == "openai":
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Текст для выжимки:\n\n{text}"},
                ],
                temperature=0.3,
            )
            return response.choices[0].message.content.strip()

        return ""


transcriber = TranscriberService()
