"""База знаний ассистента — тонкая обёртка над снапшотом data/kb.json.

Снапшот собирается заранее скриптом scripts/export_kb.py: тарифы и вопросы —
из index.html лендинга, знание о продукте — из data/product/*.json. Здесь
файл только читается и перечитывается по команде, без похода в код и без
похода в сеть.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)


def _digits(value: str) -> str:
    """Номер из tel:/wa.me/t.me-ссылки в виде +7XXXXXXXXXX ('' — если не номер)."""
    digits = "".join(ch for ch in value if ch.isdigit())
    if len(digits) == 11 and digits[0] in "78":
        return "+7" + digits[1:]
    return ""


def _pretty(phone: str) -> str:
    """+79943121222 → +7 994 312-12-22."""
    return f"+7 {phone[2:5]} {phone[5:8]}-{phone[8:10]}-{phone[10:12]}"


class KnowledgeBase:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._data: dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        try:
            self._data = json.loads(self._path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            logger.error(
                "Снапшот базы знаний не найден: %s — запустите `python -m scripts.export_kb`",
                self._path,
            )
            self._data = {}
        except json.JSONDecodeError:
            logger.exception("Снапшот базы знаний повреждён: %s", self._path)
            self._data = {}

    # перечитать после export_kb, не перезапуская процесс
    reload = load

    @property
    def generated_at(self) -> str:
        return self._data.get("собрано", "")

    @property
    def contacts(self) -> dict:
        return self._data.get("контакты", {})

    @property
    def contact_line(self) -> str:
        """Одной строкой, для сообщений об ошибках и лимитах.

        Номера читаемым видом — цифровая строка неудобна для устной диктовки
        в чате. Звонок и мессенджеры у «Падачи» на разных номерах: номер
        WhatsApp и Telegram берётся из самих ссылок wa.me / t.me на сайте,
        а не приписывается телефону для звонков.
        """
        c = self.contacts
        phone = _digits(c.get("телефон", ""))
        messenger = _digits(c.get("whatsapp", "")) or _digits(c.get("telegram", ""))
        apps = " и ".join(n for k, n in (("whatsapp", "WhatsApp"), ("telegram", "Telegram")) if c.get(k))

        parts = []
        if phone and messenger == phone and apps:
            parts.append(f"{_pretty(phone)} — звонок, {apps.replace(' и ', ' или ')}")
        else:
            if phone:
                parts.append(f"{_pretty(phone)} — звонок")
            if messenger and apps:
                parts.append(f"{_pretty(messenger)} — {apps}")
        if c.get("почта"):
            parts.append(f"{c['почта']} — почта")
        return "; ".join(parts) or "команде"

    @property
    def tariffs(self) -> list[dict]:
        return self._data.get("тарифы", [])

    @property
    def faq(self) -> list[dict]:
        return self._data.get("частые_вопросы", [])

    @property
    def product_topics(self) -> list[dict]:
        return self._data.get("продукт", [])

    @property
    def policy(self) -> dict:
        return self._data.get("политика", {})

    def as_json(self) -> str:
        """Снапшот целиком — для системного промпта.

        Компактно (без отступов): это read-only контекст для модели, а не
        файл для человека — лишние пробелы просто едят токены.
        """
        return json.dumps(self._data, ensure_ascii=False, separators=(",", ":"))


kb = KnowledgeBase(settings.kb_path)
