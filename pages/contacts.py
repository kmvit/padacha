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


TELEGRAM_URL = "https://t.me/justscoundel"
MAX_URL = "https://max.ru/u/f9LHodD0cOJorySqccC4WZ749Mu2d_ZdDcDP9aeMXM9nowPq_L3tz8Gq04s"


def update_messengers(body: str) -> str:
    body = body.replace('href="https://t.me/+79289557566"', f'href="{TELEGRAM_URL}"')
    body = body.replace(
        'href="https://max.ru/u/f9LHodD0cOIIAAQbhXr2nnV8L7VZRhxS-b2jl7dlT1-hrMK2KHMn_9lIDfw"',
        f'href="{MAX_URL}"',
    )
    if f'href="{MAX_URL}"' in body:
        return body
    telegram = re.search(rf'( *)<a class="([^"]+)" href="{re.escape(TELEGRAM_URL)}"[^>]*>Telegram</a>\n', body)
    if not telegram:
        return body
    indent, cls = telegram.groups()
    button = f'{indent}<a class="{cls}" href="{MAX_URL}" target="_blank" rel="noreferrer">MAX</a>\n'
    return body[:telegram.end()] + button + body[telegram.end():]


def with_contact_placeholder(body: str) -> str:
    """Подставить общий список вместо прежних контактных кнопок, сохранив демо."""
    def replace_buttons(match):
        buttons = match.group(1)
        if 'href="tel:+79943121222"' not in buttons:
            return match.group()
        remaining = re.sub(
            r'<a\b[^>]* href="(?:tel:|mailto:|https://(?:wa\.me|t\.me|max\.ru)/)[^"]*"[^>]*>[^<]*</a>',
            '', buttons,
        ).strip()
        return '[[контакты]]' + (f'\n<div class="contacts">{remaining}</div>' if remaining else '')

    return re.sub(r'<div class="contacts">(.*?)</div>', replace_buttons, body, flags=re.S)
