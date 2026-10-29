"""Переносит страницы из статического сайта (legacy/: index.html прежнего
padacha-landing) в базу: поисковые поля, микроразметку и тело между шапкой и подвалом.
Шапку, подвал, Метрику и общие скрипты рисует шаблон, их не переносим.

    manage.py import_pages            # только новые адреса
    manage.py import_pages --force    # перезаписать и те, что уже в базе

Запускается один раз при переезде. Дальше страницы правятся в админке.
"""
import html
import re
from datetime import date
from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand

from pages.models import ARTICLES, LEAD_FORM, Page

ROOT = settings.LEGACY_DIR
#: адрес → файл. Статьи блога сюда не входят: они в content/blog/*.md
FILES = {
    "/": "index.html",
    "/qr-menu/": "qr-menu/index.html",
    "/ekran-kuhni/": "ekran-kuhni/index.html",
    "/sklad/": "sklad/index.html",
    "/personal/": "personal/index.html",
    "/oplata/": "oplata/index.html",
    "/dlya-kofejni/": "dlya-kofejni/index.html",
    "/dlya-kafe/": "dlya-kafe/index.html",
    "/sravnenie/": "sravnenie/index.html",
    "/blog/": "blog/index.html",
    "/404/": "404.html",
}
LD = re.compile(r'<script type="application/ld\+json">\n?(.*?)\n?</script>\n?', re.S)

# Согласие на обработку персональных данных (152-ФЗ) — на него ведёт галочка
# в форме заявки. В статическом сайте его не было, поэтому создаётся черновик:
# вписать реквизиты оператора и опубликовать в админке до запуска формы.
CONSENT_BODY = """<main>
  <div class="page-hero">
    <div class="wrap">
      <div class="crumbs"><a href="/">Падача</a> → Согласие на обработку данных</div>
      <h1>Согласие на обработку<br>персональных данных</h1>
    </div>
  </div>
  <section>
    <div class="narrow prose">
      <p>Отправляя заявку на сайте padacha.ru, я даю согласие [ОПЕРАТОР: ФИО ИП или название организации], ИНН [ИНН], ОГРНИП/ОГРН [номер], адрес: [адрес] (далее — Оператор) на обработку моих персональных данных на условиях ниже.</p>
      <h2>Какие данные</h2>
      <p>Имя, телефон или имя в мессенджере, формат заведения и текст комментария, а также технические данные: IP-адрес, сведения о браузере, адрес страницы и метки рекламной кампании.</p>
      <h2>Зачем</h2>
      <p>Чтобы связаться со мной по заявке, рассказать о сервисе «Падача» и подключить заведение.</p>
      <h2>Что Оператор делает с данными</h2>
      <p>Сбор, запись, систематизация, хранение, уточнение, использование, удаление и уничтожение — с использованием средств автоматизации и без них. Данные хранятся на серверах в России и третьим лицам не передаются.</p>
      <h2>Сколько действует</h2>
      <p>До достижения цели обработки или до отзыва согласия. Отозвать согласие можно письмом на [e-mail для отзыва]; данные будут удалены в течение 30 дней.</p>
    </div>
  </section>
</main>
"""


def meta(head: str, attr: str, name: str) -> str:
    m = re.search(rf'<meta {attr}="{re.escape(name)}" content="([^"]*)"', head)
    return html.unescape(m.group(1)) if m else ""


def sitemap_rows() -> dict:
    xml = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    rows = {}
    for block in re.findall(r"<url>(.*?)</url>", xml, re.S):
        loc = re.search(r"<loc>https://padacha\.ru(.*?)</loc>", block).group(1)
        get = lambda tag: (re.search(rf"<{tag}>(.*?)</{tag}>", block) or [None, None])[1]  # noqa: E731
        rows[loc] = (get("lastmod"), get("changefreq"), get("priority"))
    return rows


def with_form(body: str) -> str:
    """Форма заявки — под кнопками связи в блоке #call."""
    if LEAD_FORM in body:
        return body
    return re.sub(r'(<div class="call" id="call">.*?<div class="contacts">.*?</div>\n)',
                  lambda m: m.group(1) + LEAD_FORM + "\n", body, count=1, flags=re.S)


def parse(path: str, file: str) -> dict:
    src = (ROOT / file).read_text(encoding="utf-8")
    head = src[src.index("<head>"):src.index("</head>")]
    after_title = head[head.index("</title>") + len("</title>\n"):]
    body = src[src.index("</header>") + len("</header>"):src.index("<footer>")].strip("\n") + "\n"
    home = path == "/"

    if home:
        # у главной своя вёрстка: head после <title> — целиком, микроразметка — в конце body
        jsonld = LD.search(src[src.index("</footer>"):]).group(1)
        extra_head = after_title
    else:
        found = LD.search(after_title)
        jsonld = found.group(1) if found else ""
        extra_head = ""

    if path == "/blog/":
        body = re.sub(r'(<div class="posts">\n).*?(\n      </div>\n    </div>\n  </section>)',
                      lambda m: m.group(1) + ARTICLES + m.group(2), body, count=1, flags=re.S)

    title = html.unescape(re.search(r"<title>(.*?)</title>", head, re.S).group(1))
    description = meta(head, "name", "description")
    og_title, og_description = meta(head, "property", "og:title"), meta(head, "property", "og:description")
    return {
        "title": title,
        "description": description,
        "og_title": "" if og_title == title else og_title,
        "og_description": "" if og_description == description else og_description,
        "theme_color": meta(head, "name", "theme-color") or "#FF7A18",
        "noindex": "noindex" in meta(head, "name", "robots"),
        "layout": Page.Layout.HOME if home else Page.Layout.INNER,
        "head": extra_head,
        "jsonld": jsonld,
        "body": with_form(body),
    }


class Command(BaseCommand):
    help = "Переносит страницы статического сайта в базу"

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="перезаписать страницы, что уже есть в базе")

    def handle(self, *args, force: bool = False, **options):
        rows = sitemap_rows()
        for path, file in FILES.items():
            if not (ROOT / file).exists():
                self.stdout.write(f"нет файла: {file}")
                continue
            if Page.objects.filter(path=path).exists() and not force:
                self.stdout.write(f"уже в базе: {path}")
                continue
            fields = parse(path, file)
            lastmod, freq, priority = rows.get(path, (None, None, None))
            fields.update(
                in_sitemap=path in rows,
                lastmod=date.fromisoformat(lastmod) if lastmod else date.today(),
                changefreq=freq or "monthly",
                priority=Decimal(priority or "0.5"),
            )
            Page.objects.update_or_create(path=path, defaults=fields)
            form = "с формой" if LEAD_FORM in fields["body"] else "без формы"
            self.stdout.write(f"перенесена: {path} ({form})")

        _, created = Page.objects.get_or_create(path="/soglasie/", defaults={
            "title": "Согласие на обработку персональных данных — Падача",
            "body": CONSENT_BODY,
            "noindex": True,
            "in_sitemap": False,
            "is_published": False,
        })
        if created:
            self.stdout.write("черновик: /soglasie/ — вписать реквизиты и опубликовать в админке")
