"""Агент «Падачи» через MODO API.

Без инструментов: вся база знаний уже лежит в системном промпте целиком
(см. app/prompt.py) — снапшот умещается в несколько тысяч токенов, и
дозагрузка по частям добавила бы только новый способ ошибиться, а не
сэкономила бы что-то ощутимое. Из-за этого агент проще, чем у соседнего
ассистента ХАК ИТС: один запрос — один ответ, без цикла вызовов инструментов.
"""

from __future__ import annotations

import asyncio
import logging
import re

import httpx

from app.config import settings
from app.prompt import GREETING, load_prompt

logger = logging.getLogger(__name__)

__all__ = ["Agent", "GREETING"]

#: Сколько раз повторить запрос при обрыве связи. Обрыв на пути к облаку —
#: обычное дело, а для посетителя это потерянная реплика посреди разговора.
#: Повторяем только сетевые ошибки: отказ по существу (неверная модель,
#: кончилась квота) вторая попытка не починит.
NETWORK_RETRIES = 2
RETRY_PAUSE_SECONDS = 1.0

#: Сколько сообщений диалога держим сверх системного промпта.
MAX_HISTORY = 24

#: Разметку модель просили не использовать, но подстраховаться дешевле, чем
#: показать посетителю «**склад**» или «[demo](https://…)» в сыром виде.
#: Дешёвая модель инструкцию про списки через дефис соблюдает не всегда —
#: маркер в начале строки срезаем отдельно, оставляя перенос строки.
_MD_LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^)]+)\)")
_MD_MARKS_RE = re.compile(r"[*_`#]{1,3}")
_MD_LIST_MARK_RE = re.compile(r"^\s*[-•*]\s+", re.MULTILINE)

def clean_markup(text: str) -> str:
    text = _MD_LINK_RE.sub(lambda m: f"{m.group(1)} — {m.group(2)}", text)
    text = _MD_LIST_MARK_RE.sub("", text)
    text = _MD_MARKS_RE.sub("", text)
    return text.strip()


def _is_user_message(message) -> bool:
    return isinstance(message, dict) and message.get("role") == "user" and "content" in message


class Agent:
    """Один экземпляр = один диалог (хранит свою историю)."""

    def __init__(self) -> None:
        settings.require_credentials()
        self._messages: list[dict[str, str]] = [{"role": "system", "content": load_prompt()}]

    def _trim_history(self) -> None:
        if len(self._messages) <= MAX_HISTORY + 1:
            return
        tail = self._messages[-MAX_HISTORY:]
        while tail and not _is_user_message(tail[0]):
            tail.pop(0)
        self._messages = [self._messages[0], *tail]

    async def _run_with_retry(self) -> str:
        for attempt in range(NETWORK_RETRIES + 1):
            try:
                async with httpx.AsyncClient(timeout=httpx.Timeout(45, connect=5), trust_env=False) as client:
                    response = await client.post(
                        f"{settings.modo_base_url}/chat/completions",
                        headers={"Authorization": f"Bearer {settings.modo_api_key}"},
                        json={
                            "model": settings.llm_model,
                            "messages": self._messages,
                            "temperature": 0.2,
                            "max_tokens": 800,
                            "stream": False,
                        },
                    )
                    response.raise_for_status()
                    content = response.json()["choices"][0]["message"]["content"]
                    if not isinstance(content, str):
                        raise ValueError("Модель вернула ответ без текста")
                    return content
            except httpx.TransportError as exc:
                if attempt == NETWORK_RETRIES:
                    raise
                logger.warning(
                    "Обрыв связи с моделью (%s), повтор %d из %d",
                    type(exc).__name__, attempt + 1, NETWORK_RETRIES,
                )
                await asyncio.sleep(RETRY_PAUSE_SECONDS * (attempt + 1))
        raise RuntimeError("Недоступная ветка повторов")

    async def ask(self, user_text: str) -> str:
        """Прогоняет реплику через модель и возвращает готовый ответ.

        Пустая строка — модель ничего не сказала; вызывающий код решает,
        что показать посетителю (см. server.py).
        """
        self._messages.append({"role": "user", "content": user_text})
        self._trim_history()

        try:
            answer = await self._run_with_retry()
        except Exception:
            self._messages.pop()
            raise
        self._messages.append({"role": "assistant", "content": answer})
        return clean_markup(answer)
