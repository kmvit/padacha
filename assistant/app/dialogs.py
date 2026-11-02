"""Запись публичных диалогов в ту же SQLite, которую читает Django admin.

Схемой управляют миграции assistant_dialogs; сервису Django не требуется.
"""

from __future__ import annotations

import os
import sqlite3
from contextlib import closing, contextmanager
from datetime import datetime, timezone
from pathlib import Path


DB_PATH = Path(os.getenv("ASSISTANT_DB_PATH", Path(__file__).resolve().parents[2] / "var/db.sqlite3"))


def _connect() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


@contextmanager
def _transaction():
    with closing(_connect()) as db:
        with db:
            yield db


def _now() -> str:
    # Django хранит DateTimeField в UTC без смещения внутри SQLite.
    return datetime.now(timezone.utc).replace(tzinfo=None).isoformat(" ", timespec="microseconds")


def check_schema() -> None:
    with _transaction() as db:
        db.execute("SELECT id FROM assistant_dialogs_conversation LIMIT 0")
        db.execute("SELECT id FROM assistant_dialogs_message LIMIT 0")


def create_conversation(session_id: str, greeting: str) -> None:
    now = _now()
    with _transaction() as db:
        cursor = db.execute(
            "INSERT INTO assistant_dialogs_conversation (session_id, created_at, updated_at) "
            "VALUES (?, ?, ?)", (session_id, now, now),
        )
        db.execute(
            "INSERT INTO assistant_dialogs_message (conversation_id, role, text, created_at) "
            "VALUES (?, ?, ?, ?)", (cursor.lastrowid, "assistant", greeting, now),
        )


def save_exchange(session_id: str, question: str, answer: str) -> None:
    now = _now()
    with _transaction() as db:
        row = db.execute(
            "SELECT id FROM assistant_dialogs_conversation WHERE session_id = ?", (session_id,)
        ).fetchone()
        if row is None:
            raise RuntimeError(f"Диалог {session_id} не найден в базе")
        conversation_id = row[0]
        db.executemany(
            "INSERT INTO assistant_dialogs_message (conversation_id, role, text, created_at) "
            "VALUES (?, ?, ?, ?)",
            ((conversation_id, "user", question, now),
             (conversation_id, "assistant", answer, now)),
        )
        db.execute(
            "UPDATE assistant_dialogs_conversation SET updated_at = ? WHERE id = ?",
            (now, conversation_id),
        )
