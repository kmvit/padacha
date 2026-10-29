"""Почта в блоке контактов #call — рядом с кнопкой Telegram.

Кнопки контактов лежат в теле каждой страницы (оно в базе), поэтому почту
вставляют и импорт страниц, и миграция 0002 для уже заведённых.
"""
import re

EMAIL = "info@padacha.ru"


def with_email(body: str) -> str:
    if f"mailto:{EMAIL}" in body:
        return body
    telegram = re.search(r'( *)<a class="([^"]+)" href="https://t\.me/[^"]*"[^>]*>Telegram</a>\n', body)
    if not telegram:
        return body
    indent, cls = telegram.group(1), telegram.group(2)
    button = f'{indent}<a class="{cls}" href="mailto:{EMAIL}">{EMAIL}</a>\n'
    return body[:telegram.end()] + button + body[telegram.end():]
