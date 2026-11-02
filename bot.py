import os
import asyncio
import logging
import sys
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import (
    BotCommand,
    BotCommandScopeAllGroupChats,
    BotCommandScopeAllPrivateChats,
    BotCommandScopeDefault,
)

from config import config
from handlers import common, audio

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)


async def handle_ping(request: web.Request) -> web.Response:
    """Эндпоинт для пинга от cron-job.org и проверки здоровья Render."""
    return web.Response(text="Wisperbor bot is alive and running!", content_type="text/plain")


async def start_web_server():
    """Запускает легковесный HTTP-сервер для Render и пингов cron-job.org."""
    port_str = os.getenv("PORT")
    if not port_str:
        return None

    try:
        port = int(port_str)
        app = web.Application()
        app.router.add_get("/", handle_ping)
        app.router.add_get("/health", handle_ping)

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", port)
        await site.start()
        logging.info(f"Веб-сервер для пинга запущен на порту {port}")
        return runner
    except Exception as e:
        logging.warning(f"Не удалось запустить веб-сервер пинга: {e}")
        return None


async def setup_commands(bot: Bot):
    """Регистрирует подсказки команд в меню Telegram при вводе '/'."""
    try:
        # Меню команд для групповых чатов
        await bot.set_my_commands(
            commands=[
                BotCommand(command="t", description="Расшифровать (в ответ на войс/кружочек)"),
                BotCommand(command="help", description="Инструкция по боту"),
            ],
            scope=BotCommandScopeAllGroupChats(),
        )

        # Меню команд для личных сообщений
        await bot.set_my_commands(
            commands=[
                BotCommand(command="start", description="Запустить бота"),
                BotCommand(command="help", description="Инструкция и возможности"),
            ],
            scope=BotCommandScopeAllPrivateChats(),
        )

        # Дефолтные команды для всех контекстов
        await bot.set_my_commands(
            commands=[
                BotCommand(command="t", description="Расшифровать (в ответ на войс)"),
                BotCommand(command="start", description="Старт"),
                BotCommand(command="help", description="Помощь"),
            ],
            scope=BotCommandScopeDefault(),
        )
        logging.info("Подсказки команд Telegram успешно зарегистрированы!")
    except Exception as e:
        logging.warning(f"Не удалось зарегистрировать подсказки команд: {e}")


async def main():
    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    # Регистрация роутеров
    dp.include_router(common.router)
    dp.include_router(audio.router)

    # Регистрация команд при вводе '/'
    await setup_commands(bot)

    # Запуск фонового веб-сервера для Render
    web_runner = await start_web_server()

    logging.info(f"Бот запускается! Провайдер STT: {config.stT_provider.upper()}")
    await bot.delete_webhook(drop_pending_updates=True)

    try:
        await dp.start_polling(bot)
    finally:
        if web_runner:
            await web_runner.cleanup()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот остановлен пользователем.")
