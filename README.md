# Telegram Бот для расшифровки голосовых и видеосообщений в текст

Асинхронный Telegram-бот на Python (**Aiogram 3**) с распознаванием русской речи через **Whisper** (облачный API Groq / OpenAI).

## 🚀 Возможности
- 🎙 **Голосовые сообщения** (`.ogg` / Opus)
- 🔵 **Видеосообщения** («кружочки» `.mp4`)
- 🎵 **Аудиофайлы и диктофонные записи** (`.mp3`, `.m4a`, `.wav` и др.)
- 🎬 **Видеофайлы** (до 20 МБ)
- ⚡ **Мгновенная скорость**: Groq Whisper обрабатывает минутное сообщение за 1-2 секунды.
- 🇷🇺 **Высокая точность**: Whisper Large V3 оптимизирован под русскую речь и пунктуацию.
- 📜 **Авторазбиение длинных сообщений**: если текст длиннее лимита Telegram (4096 символов), он аккуратно разбивается на части.

---

## 🛠 Быстрый старт

### 1. Получение API-ключей

1. **Токен Telegram-бота**:
   - Откройте бота [@BotFather](https://t.me/BotFather) в Telegram.
   - Отправьте команду `/newbot` и следуйте инструкциям.
   - Скопируйте полученный HTTP API токен.

2. **Ключ Groq API (Бесплатно)**:
   - Перейдите в [Groq Console](https://console.groq.com/keys).
   - Зарегистрируйтесь (через Google или GitHub).
   - Нажмите **Create API Key**, придумайте имя и скопируйте ключ (начинается с `gsk_...`).
   *(У Groq есть щедрый бесплатный лимит на модель `whisper-large-v3-turbo`)*.

---

### 2. Установка и настройка

1. Перейдите в папку проекта:
   ```bash
   cd C:\Users\Админ\.gemini\antigravity\scratch\tg-voice-transcriber-bot
   ```

2. Создайте и активируйте виртуальное окружение:
   ```bash
   python -m venv venv
   # В Windows (PowerShell):
   .\venv\Scripts\Activate.ps1
   # В Linux / macOS:
   source venv/bin/activate
   ```

3. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```

4. Скопируйте файл `.env.example` в `.env`:
   ```bash
   copy .env.example .env
   ```

5. Откройте файл `.env` и вставьте ваши ключи:
   ```env
   BOT_TOKEN=1234567890:AAHxxxxxx_ваш_токен_botfather
   STT_PROVIDER=groq
   GROQ_API_KEY=gsk_ваш_ключ_groq
   GROQ_MODEL=whisper-large-v3-turbo
   ```

---

### 3. Запуск бота

```bash
python bot.py
```

После запуска отправьте боту команду `/start`, а затем запишите или перешлите любое голосовое сообщение или видео-кружочек!
