"""Заявки с формы «Подключить» (блок #call на каждой странице)."""
from django.db import models


class Lead(models.Model):
    class Venue(models.TextChoices):
        COUNTER = "counter", "Точка без зала"
        HALL = "hall", "Кафе с залом"
        UNKNOWN = "", "Не указан"

    class Status(models.TextChoices):
        NEW = "new", "Новая"
        WORK = "work", "В работе"
        DONE = "done", "Подключили"
        LOST = "lost", "Отказ"
        SPAM = "spam", "Спам"

    created_at = models.DateTimeField("Пришла", auto_now_add=True)
    name = models.CharField("Имя", max_length=120)
    phone = models.CharField("Телефон или мессенджер", max_length=120)
    venue = models.CharField("Формат", max_length=20, choices=Venue.choices, blank=True)
    comment = models.TextField("Комментарий", blank=True)
    consent_at = models.DateTimeField("Согласие на обработку ПД", null=True, blank=True,
                                      help_text="Когда посетитель поставил галочку (152-ФЗ).")

    status = models.CharField("Статус", max_length=10, choices=Status.choices, default=Status.NEW)
    note = models.TextField("Заметка", blank=True, help_text="Для себя: о чём договорились, когда перезвонить.")

    # откуда пришла: страница с формой и первая метка визита
    page = models.CharField("Страница", max_length=300, blank=True)
    referrer = models.CharField("Пришёл с", max_length=500, blank=True)
    utm_source = models.CharField("utm_source", max_length=120, blank=True)
    utm_medium = models.CharField("utm_medium", max_length=120, blank=True)
    utm_campaign = models.CharField("utm_campaign", max_length=200, blank=True)
    utm_content = models.CharField("utm_content", max_length=200, blank=True)
    utm_term = models.CharField("utm_term", max_length=200, blank=True)
    ip = models.GenericIPAddressField("IP", null=True, blank=True)
    user_agent = models.CharField("Браузер", max_length=300, blank=True)

    class Meta:
        verbose_name = "заявка"
        verbose_name_plural = "Заявки"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.name} · {self.phone}"
