"""Страницы сайта: главная, страницы продукта и форматов, список статей, 404.

У каждой страницы своя вёрстка, поэтому тело хранится html-ом как есть, а
всё одинаковое — head, шапка, подвал, Метрика, скрипты — рисует шаблон
(templates/base.html). Поисковые поля вынесены отдельно, чтобы их можно было
править, не трогая разметку.
"""
from django.db import models
from django.utils import timezone

#: Метки, которые можно ставить в тело страницы
LEAD_FORM = "[[форма-заявки]]"
ARTICLES = "[[статьи]]"


# Подсказки к полям админка выводит как html, поэтому теги в них — сущностями.


class Page(models.Model):
    class Layout(models.TextChoices):
        INNER = "inner", "Внутренняя (шапка, тело, подвал)"
        HOME = "home", "Главная (своя вёрстка и скрипты)"

    path = models.CharField(
        "Адрес", max_length=200, unique=True,
        help_text="Например /sklad/. Менять после публикации нельзя без перенаправления "
                  "со старого адреса — на него ведут поисковик и внешние ссылки.",
    )
    title = models.CharField("Заголовок для поиска", max_length=200, help_text="&lt;title&gt;. До 60 знаков видно в выдаче.")
    description = models.CharField(
        "Описание для поиска", max_length=300, blank=True, help_text="До 160 знаков. Сниппет в выдаче.",
    )
    og_title = models.CharField("Заголовок при репосте", max_length=200, blank=True,
                                help_text="og:title. Если пусто — заголовок для поиска.")
    og_description = models.CharField("Описание при репосте", max_length=300, blank=True,
                                      help_text="og:description. Если пусто — описание для поиска.")
    theme_color = models.CharField("Цвет строки браузера", max_length=20, default="#FF7A18")
    noindex = models.BooleanField("Скрыть от поисковиков", default=False)

    layout = models.CharField("Вёрстка", max_length=10, choices=Layout.choices, default=Layout.INNER)
    head = models.TextField(
        "Дополнительно в <head>", blank=True,
        help_text="Для главной — шрифты, стили и Метрика целиком. Внутренним страницам обычно не нужно.",
    )
    jsonld = models.TextField("Микроразметка (JSON-LD)", blank=True,
                              help_text="Содержимое &lt;script type=\"application/ld+json\"&gt;, без самого тега.")
    body = models.TextField(
        "Тело страницы (html)",
        help_text=f"Всё между шапкой и подвалом: &lt;main&gt;…&lt;/main&gt;. Метка {LEAD_FORM} — форма заявки, "
                  f"{ARTICLES} — карточки статей (только на /blog/).",
    )

    is_published = models.BooleanField("Опубликована", default=True)
    in_sitemap = models.BooleanField("В sitemap.xml", default=True)
    priority = models.DecimalField("Приоритет в sitemap", max_digits=2, decimal_places=1, default=0.8)
    changefreq = models.CharField("Как часто меняется", max_length=10, default="monthly",
                                  choices=[(v, v) for v in ("daily", "weekly", "monthly", "yearly")])
    lastmod = models.DateField("Изменена (для sitemap)", default=timezone.localdate,
                               help_text="Поставьте сегодняшнюю дату, если правка заметная.")
    updated_at = models.DateTimeField("Сохранена", auto_now=True)

    class Meta:
        verbose_name = "страница"
        verbose_name_plural = "Страницы"
        ordering = ["path"]

    def __str__(self) -> str:
        return f"{self.path} — {self.title}"

    def get_absolute_url(self) -> str:
        return self.path
