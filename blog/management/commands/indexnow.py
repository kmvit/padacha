"""Сообщает поисковикам о вышедших статьях по протоколу IndexNow.

Статьи выходят сами, когда наступает их время, и поисковику надо об этом
сказать. Команду запускает таймер раз в 15 минут (deploy/padacha-indexnow.*):
она находит вышедшие, но ещё не отправленные статьи и шлёт их адреса вместе
со списком /blog/. Ключ — файл <32 hex>.txt в public/.

    manage.py indexnow                      # вышедшие статьи, если есть
    manage.py indexnow /sravnenie/ /sklad/  # эти адреса — после правки страниц
"""
import json
import ssl
import urllib.error
import urllib.request

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from blog.models import Article

HOST = "padacha.ru"
ENDPOINTS = ["https://yandex.com/indexnow", "https://api.indexnow.org/indexnow"]


def key() -> str:
    found = [p for p in settings.SITE_ROOT.glob("*.txt") if len(p.stem) == 32 and p.read_text().strip() == p.stem]
    if not found:
        raise CommandError("нет файла-ключа <32 hex>.txt в корне сайта")
    return found[0].stem


class Command(BaseCommand):
    help = "Отправляет вышедшие статьи (или указанные адреса) в IndexNow"

    def add_arguments(self, parser):
        parser.add_argument("paths", nargs="*")

    def handle(self, *args, paths=(), **options):
        fresh = []
        if not paths:
            fresh = list(Article.objects.live().filter(indexnow_at__isnull=True))
            if not fresh:
                return
            paths = [a.get_absolute_url() for a in fresh] + ["/blog/"]
        k = key()
        body = json.dumps({
            "host": HOST, "key": k, "keyLocation": f"https://{HOST}/{k}.txt",
            "urlList": [f"https://{HOST}{p}" for p in paths],
        }).encode()
        ok = 0
        for url in ENDPOINTS:
            req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json; charset=utf-8"})
            try:
                with urllib.request.urlopen(req, timeout=20, context=ssl.create_default_context()) as r:
                    self.stdout.write(f"{url}: {r.status}")
                    ok += r.status in (200, 202)
            except urllib.error.HTTPError as e:
                self.stdout.write(f"{url}: {e.code} {e.read().decode(errors='replace')[:200]}")
            except urllib.error.URLError as e:
                self.stdout.write(f"{url}: нет связи — {e.reason}")
        self.stdout.write(f"адресов: {len(paths)}, приняли: {ok} из {len(ENDPOINTS)}")
        if ok and fresh:  # не приняли — повторим в следующий запуск
            Article.objects.filter(pk__in=[a.pk for a in fresh]).update(indexnow_at=timezone.now())
