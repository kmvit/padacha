"""Статьи блога padacha.ru.

Раньше (в репозитории padacha-landing) каждая статья была отдельным
index.html на четыреста строк, где девяносто процентов файла — одинаковая
обвязка; её собирал tools/article.py из content/blog/*.md. Теперь текст в базе, обвязку рисует шаблон
(templates/blog/article.html), а .md-файлы остались форматом для партий:
`manage.py import_articles` заливает их сюда.

Поля разбиты на три группы: что видит поисковик (title, description),
что видит читатель (h1, лид, тело) и что идёт после текста (вопросы,
ссылки по теме, призыв) — на сайте эти блоки у каждой статьи свои.
"""
import re

from django.db import models
from django.urls import reverse
from django.utils import timezone

from . import markup


class ArticleQuerySet(models.QuerySet):
    def live(self):
        """Вышедшие: опубликованы и время выхода наступило."""
        return self.filter(is_published=True, published_at__lte=timezone.now())


class Article(models.Model):
    slug = models.SlugField(
        "Адрес", max_length=120, unique=True,
        help_text="Часть ссылки: /blog/&lt;адрес&gt;/. Менять после публикации нельзя — "
                  "поисковик и внешние ссылки ведут на старый.",
    )
    title = models.CharField(
        "Заголовок для поиска", max_length=120,
        help_text="До 60 знаков видно в выдаче целиком. Идёт в &lt;title&gt; и в og:title.",
    )
    description = models.CharField(
        "Описание для поиска", max_length=200,
        help_text="До 160 знаков. Сниппет в выдаче и описание при репосте.",
    )
    h1 = models.CharField(
        "Заголовок на странице", max_length=160, blank=True,
        help_text="Если пусто — берётся заголовок для поиска. Перенос строки: &lt;br&gt;",
    )
    crumb = models.CharField("Хлебная крошка", max_length=80, help_text="Короткое имя статьи: Падача → Статьи → …")
    meta = models.CharField("Рубрики", max_length=80, blank=True, help_text="Над карточкой в списке: «Деньги · Учёт».")
    card = models.TextField("Текст карточки", blank=True,
                            help_text="Две-три фразы в списке статей. Если пусто — описание для поиска.")
    lede = models.TextField("Вводка", help_text="Абзац под заголовком, крупным шрифтом.")
    body = models.TextField(
        "Текст статьи",
        help_text="Markdown: ## подзаголовок, **жирный**, списки, таблицы, [ссылка](/sklad/). "
                  "Цитата через > становится врезкой, > [Метка] — врезкой с ярлыком.",
    )

    faq_title = models.CharField("Заголовок вопросов", max_length=160, blank=True,
                                 help_text="Если пусто — «Частые вопросы».")
    call_title = models.CharField("Призыв: заголовок", max_length=160, blank=True)
    call_text = models.TextField("Призыв: текст", blank=True)

    published_at = models.DateTimeField(
        "Выход", default=timezone.now,
        help_text="Статья появится на сайте, в списке и в sitemap в это время (по Москве).",
    )
    show_time = models.BooleanField(
        "Время в микроразметке", default=True,
        help_text="Писать datePublished с часами. Выключено у старых статей, где была только дата.",
    )
    modified = models.DateField("Заметно обновлена", null=True, blank=True,
                                help_text="dateModified и lastmod в sitemap. Если пусто — дата выхода.")
    is_published = models.BooleanField(
        "Опубликована", default=True,
        help_text="Снимите, чтобы убрать статью с сайта. Черновик виден по ссылке только вошедшему в админку.",
    )
    indexnow_at = models.DateTimeField("Отправлена в IndexNow", null=True, blank=True, editable=False)
    updated_at = models.DateTimeField("Сохранена", auto_now=True)

    objects = ArticleQuerySet.as_manager()

    class Meta:
        verbose_name = "статья"
        verbose_name_plural = "Статьи"
        ordering = ["-published_at", "-id"]

    def __str__(self) -> str:
        return self.title

    def get_absolute_url(self) -> str:
        return reverse("article", args=[self.slug])

    @property
    def heading(self) -> str:
        return self.h1 or self.title

    @property
    def heading_line(self) -> str:
        """Заголовок без переносов <br> — для карточек и микроразметки."""
        return re.sub(r"\s*<br\s*/?>\s*", " ", self.heading)

    @property
    def is_live(self) -> bool:
        return self.is_published and self.published_at <= timezone.now()

    def published_iso(self) -> str:
        local = timezone.localtime(self.published_at)
        return local.isoformat(timespec="seconds") if self.show_time else local.date().isoformat()

    def modified_iso(self) -> str:
        return self.modified.isoformat() if self.modified else self.published_iso()

    @property
    def lastmod(self):
        return self.modified or timezone.localtime(self.published_at).date()

    def body_html(self) -> str:
        return markup.render(self.body)


class Question(models.Model):
    """Вопрос-ответ в конце статьи. Отдельной моделью, а не разметкой в тексте:
    из них собирается FAQPage для расширенного сниппета, и для этого вопрос
    должен быть отделён от ответа машинно, а не «по виду»."""

    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name="questions")
    order = models.PositiveSmallIntegerField("Порядок", default=0)
    question = models.CharField("Вопрос", max_length=200)
    answer = models.TextField("Ответ", help_text="Markdown. Абзацы разделяются пустой строкой.")

    class Meta:
        verbose_name = "вопрос"
        verbose_name_plural = "вопросы"
        ordering = ["order", "id"]

    def __str__(self) -> str:
        return self.question

    def answer_html(self) -> str:
        return markup.render(self.answer)


class Related(models.Model):
    """Ссылка «рядом по теме». Ведёт и на статью, и на страницу продукта,
    поэтому адрес хранится строкой, а не связью."""

    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name="related")
    order = models.PositiveSmallIntegerField("Порядок", default=0)
    href = models.CharField("Адрес", max_length=200)
    title = models.CharField("Название", max_length=120)
    note = models.CharField("Подпись", max_length=200, blank=True)

    class Meta:
        verbose_name = "ссылка по теме"
        verbose_name_plural = "ссылки по теме"
        ordering = ["order", "id"]

    def __str__(self) -> str:
        return self.title
