import os
import sqlite3
import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "transcriptions.db")


def init_db_sync():
    """Создает таблицу для логирования расшифровок, если её ещё нет."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS messages_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                username TEXT,
                full_name TEXT,
                media_type TEXT NOT NULL,
                duration INTEGER,
                file_size INTEGER,
                recognized_text TEXT NOT NULL,
                summary TEXT
            )
            """
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_id ON messages_log (user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON messages_log (created_at)")
        conn.commit()


async def init_db():
    await asyncio.to_thread(init_db_sync)


def log_transcription_sync(
    user_id: int,
    username: Optional[str],
    full_name: Optional[str],
    media_type: str,
    duration: Optional[int],
    file_size: Optional[int],
    recognized_text: str,
) -> int:
    """Записывает расшифровку и данные пользователя в базу SQLite."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            """
            INSERT INTO messages_log 
            (created_at, user_id, username, full_name, media_type, duration, file_size, recognized_text)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (now, user_id, username, full_name, media_type, duration, file_size, recognized_text),
        )
        conn.commit()
        return cursor.lastrowid


async def log_transcription(
    user_id: int,
    username: Optional[str],
    full_name: Optional[str],
    media_type: str,
    duration: Optional[int],
    file_size: Optional[int],
    recognized_text: str,
) -> int:
    return await asyncio.to_thread(
        log_transcription_sync,
        user_id,
        username,
        full_name,
        media_type,
        duration,
        file_size,
        recognized_text,
    )


def update_summary_sync(record_id: int, summary: str):
    """Обновляет выжимку (саммари) для конкретной записи."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE messages_log SET summary = ? WHERE id = ?",
            (summary, record_id),
        )
        conn.commit()


async def update_summary(record_id: int, summary: str):
    await asyncio.to_thread(update_summary_sync, record_id, summary)


def get_stats_sync() -> Tuple[int, int]:
    """Возвращает общее количество расшифровок и уникальных пользователей."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*), COUNT(DISTINCT user_id) FROM messages_log")
        row = cursor.fetchone()
        return row[0] if row else 0, row[1] if row else 0


async def get_stats() -> Tuple[int, int]:
    return await asyncio.to_thread(get_stats_sync)


def get_recent_logs_sync(limit: int = 10) -> List[Dict[str, Any]]:
    """Возвращает последние записи из базы данных."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, created_at, user_id, username, full_name, media_type, recognized_text, summary
            FROM messages_log 
            ORDER BY id DESC 
            LIMIT ?
            """,
            (limit,),
        )
        return [dict(row) for row in cursor.fetchall()]


async def get_recent_logs(limit: int = 10) -> List[Dict[str, Any]]:
    return await asyncio.to_thread(get_recent_logs_sync, limit)
