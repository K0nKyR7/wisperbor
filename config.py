import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Config:
    bot_token: str
    stT_provider: str
    groq_api_key: str
    groq_model: str
    openai_api_key: str

    @classmethod
    def load(cls) -> "Config":
        bot_token = os.getenv("BOT_TOKEN", "").strip()
        if not bot_token:
            raise ValueError("Не задан BOT_TOKEN в файле .env")

        provider = os.getenv("STT_PROVIDER", "groq").lower().strip()
        groq_api_key = os.getenv("GROQ_API_KEY", "").strip()
        groq_model = os.getenv("GROQ_MODEL", "whisper-large-v3-turbo").strip()
        openai_api_key = os.getenv("OPENAI_API_KEY", "").strip()

        if provider == "groq" and not groq_api_key:
            raise ValueError("Для STT_PROVIDER=groq необходимо указать GROQ_API_KEY в файле .env")

        if provider == "openai" and not openai_api_key:
            raise ValueError("Для STT_PROVIDER=openai необходимо указать OPENAI_API_KEY в файле .env")

        return cls(
            bot_token=bot_token,
            stT_provider=provider,
            groq_api_key=groq_api_key,
            groq_model=groq_model,
            openai_api_key=openai_api_key,
        )


config = Config.load()
