"""Markdown → разметка статьи.

Классы в html статей взяты из page.css сайта, и менять их нельзя: на них
держится оформление обеих тем. Поэтому после Markdown идёт короткая правка
результата под местные соглашения (те же, что были в tools/article.py прежнего сайта):

  > цитата          → .callout, врезка; > [Метка] — врезка с ярлыком
  таблица           → числовые колонки выравниваются вправо, как в вёрстке
  заголовки h1      → h2: в статье один h1, и он в шапке страницы

Markdown выбран вместо визуального редактора сознательно: текст остаётся
текстом, его можно скопировать, сравнить и починить руками.
"""
from __future__ import annotations

import html
import re

import markdown as md
from django.utils.safestring import mark_safe

_MD = md.Markdown(
    extensions=["extra", "sane_lists", "smarty"],
    extension_configs={"smarty": {"substitutions": {"left-double-quote": "«", "right-double-quote": "»"}}},
    output_format="html",
)


def _callouts(out: str) -> str:
    """> [Метка] → <div class="callout"><span class="lbl">Метка</span>…"""
    def one(m: re.Match) -> str:
        inner = m.group(1).strip()
        label = re.match(r"<p>\[([^\]]+)\]\s*(?:<br\s*/?>|\n)?\s*", inner)
        if label:
            rest = inner[label.end():]
            inner = f'<span class="lbl">{label.group(1)}</span>\n<p>{rest}' if rest.strip() else \
                f'<span class="lbl">{label.group(1)}</span>'
            inner = inner.replace("<p></p>", "")
        # строки врезки — формулы и шаги расчёта, каждая с новой строки
        inner = re.sub(r"<p>(.*?)</p>", lambda p: "<p>" + re.sub(r"\n(?!$)", "<br>\n", p.group(1).strip()) + "</p>",
                       inner, flags=re.S)
        return f'<div class="callout">\n{inner}\n</div>'

    return re.sub(r"<blockquote>(.*?)</blockquote>", one, out, flags=re.S)


def _numeric_cells(out: str) -> str:
    """Колонки с числами — вправо и моноширинным, как в вёрстке сайта."""
    def cell(m: re.Match) -> str:
        tag, attrs, inner = m.group(1), m.group(2), m.group(3)
        plain_text = re.sub(r"<[^>]+>", "", inner).strip()
        numeric = bool(plain_text) and re.fullmatch(r"[\d\s.,%₽×+\-−–—/()]+", plain_text)
        if numeric and "class=" not in attrs:
            return f'<{tag}{attrs} class="num">{inner}</{tag}>'
        return m.group(0)

    return re.sub(r"<(td|th)([^>]*)>(.*?)</\1>", cell, out, flags=re.S)


def render(text: str) -> str:
    """Текст статьи в html. Возвращается безопасным: источник — админка,
    туда попадает только владелец."""
    _MD.reset()
    out = _MD.convert(text or "")
    out = _callouts(out)
    # колонка с выравниванием ---: в таблице Markdown — тоже числовая
    out = re.sub(r'<(t[hd]) style="text-align: ?right;?">', r'<\1 class="num">', out)
    out = _numeric_cells(out)
    out = re.sub(r"<(/?)h1\b", r"<\1h2", out)
    return mark_safe(out)


def plain(text: str) -> str:
    """Текст без разметки — для микроразметки и описаний."""
    _MD.reset()
    out = _MD.convert(text or "")
    out = re.sub(r"<[^>]+>", " ", out)
    return html.unescape(re.sub(r"\s+", " ", out)).strip()
