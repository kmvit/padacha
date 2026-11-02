from django.db import models


class Conversation(models.Model):
    session_id = models.CharField("ID сессии", max_length=64, unique=True)
    created_at = models.DateTimeField("Начат", auto_now_add=True)
    updated_at = models.DateTimeField("Последнее сообщение", auto_now=True)

    class Meta:
        verbose_name = "диалог"
        verbose_name_plural = "Диалоги"
        ordering = ["-updated_at"]

    def __str__(self) -> str:
        return f"Диалог {self.pk} · {self.created_at:%d.%m.%Y %H:%M}"


class Message(models.Model):
    class Role(models.TextChoices):
        USER = "user", "Посетитель"
        ASSISTANT = "assistant", "Ассистент"

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE,
                                     related_name="messages", verbose_name="Диалог")
    role = models.CharField("Автор", max_length=10, choices=Role.choices)
    text = models.TextField("Текст")
    created_at = models.DateTimeField("Время", auto_now_add=True)

    class Meta:
        verbose_name = "сообщение"
        verbose_name_plural = "Сообщения"
        ordering = ["created_at", "pk"]
