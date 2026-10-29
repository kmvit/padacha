"""Заливает статьи из content/blog/<адрес>.md в базу.

Формат файла — content/blog/README.md (шапка между ---, текст Markdown,
блоки «=== faq» и «=== related»). Так удобно готовить партию статей
заранее: написать файлы, закоммитить, на сервере выполнить

    manage.py import_articles                 # новые статьи, уже залитые не трогает
    manage.py import_articles slug1 slug2     # только эти
    manage.py import_articles --force slug1   # перезаписать правки из админки

Время выхода (published: 2026-11-05 09:00, по Москве) переезжает в поле
«Выход»: статья сама появится на сайте, когда оно наступит.
"""
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from blog.models import Article

SRC = settings.CONTENT_DIR / "blog"
MSK = ZoneInfo("Europe/Moscow")
REQUIRED = ("slug", "title", "description", "crumb", "lede", "published")


def parse(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---\n(.*)", text, flags=re.S)
    if not m:
        raise CommandError(f"{path.name}: нет шапки между ---")
    meta: dict = {}
    for line in m.group(1).splitlines():
        if line.strip():
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip()
    missing = [k for k in REQUIRED if not meta.get(k)]
    if missing:
        raise CommandError(f"{path.name}: не заполнено {', '.join(missing)}")

    parts = re.split(r"^=== (faq|related)\s*$", m.group(2), flags=re.M)
    meta["body"] = parts[0].strip()
    sections = dict(zip(parts[1::2], parts[2::2]))

    meta["faq"] = []
    for block in re.split(r"^### ", sections.get("faq", ""), flags=re.M)[1:]:
        q, _, a = block.partition("\n")
        meta["faq"].append((q.strip(), a.strip()))

    meta["related"] = []
    for line in sections.get("related", "").splitlines():
        line = line.strip()
        if line.startswith("- "):
            href, name, note = (p.strip() for p in (line[2:].split("|") + ["", ""])[:3])
            meta["related"].append((href, name, note))

    when = re.fullmatch(r"(\d{4}-\d{2}-\d{2})(?:[ T](\d{2}:\d{2}))?", meta["published"])
    if not when:
        raise CommandError(f"{path.name}: published — ГГГГ-ММ-ДД или ГГГГ-ММ-ДД ЧЧ:ММ")
    meta["published_at"] = datetime.fromisoformat(f"{when.group(1)}T{when.group(2) or '00:00'}").replace(tzinfo=MSK)
    meta["show_time"] = bool(when.group(2))
    return meta


class Command(BaseCommand):
    help = "Заливает статьи из content/blog/*.md в базу"

    def add_arguments(self, parser):
        parser.add_argument("slugs", nargs="*", help="только эти статьи")
        parser.add_argument("--force", action="store_true", help="перезаписать статьи, что уже есть в базе")

    def handle(self, *args, slugs=(), force=False, **options):
        files = [p for p in sorted(SRC.glob("*.md")) if p.name != "README.md"]
        now = timezone.now()
        done = 0
        for path in files:
            a = parse(path)
            if slugs and a["slug"] not in slugs:
                continue
            if Article.objects.filter(slug=a["slug"]).exists() and not force:
                self.stdout.write(f"уже в базе: {a['slug']}")
                continue
            with transaction.atomic():
                article, _ = Article.objects.update_or_create(slug=a["slug"], defaults={
                    "title": a["title"],
                    "description": a["description"],
                    "h1": a.get("h1", ""),
                    "crumb": a["crumb"],
                    "meta": a.get("meta", ""),
                    "card": a.get("card", ""),
                    "lede": a["lede"],
                    "body": a["body"],
                    "faq_title": a.get("faq_title", ""),
                    "call_title": a.get("call_title", ""),
                    "call_text": a.get("call_text", ""),
                    "published_at": a["published_at"],
                    "show_time": a["show_time"],
                    "modified": a.get("updated") or None,
                    "is_published": True,
                    # уже вышедшие поисковик знает — в IndexNow их не шлём
                    "indexnow_at": now if a["published_at"] <= now else None,
                })
                article.questions.all().delete()
                article.related.all().delete()
                for i, (q, ans) in enumerate(a["faq"]):
                    article.questions.create(order=i, question=q, answer=ans)
                for i, (href, name, note) in enumerate(a["related"]):
                    article.related.create(order=i, href=href, title=name, note=note)
            when = timezone.localtime(a["published_at"]).strftime("%d.%m.%Y %H:%M")
            state = "на сайте" if a["published_at"] <= now else f"выйдет {when}"
            self.stdout.write(f"залита: {a['slug']} ({state})")
            done += 1
        self.stdout.write(f"готово: {done}")
