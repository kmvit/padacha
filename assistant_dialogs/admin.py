from django.contrib import admin

from .models import Conversation, Message


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    fields = ("created_at", "role", "text")
    readonly_fields = fields
    can_delete = False
    show_change_link = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("created_at", "updated_at", "first_question", "message_count")
    list_display_links = ("created_at", "first_question")
    search_fields = ("session_id", "messages__text")
    date_hierarchy = "created_at"
    readonly_fields = ("session_id", "created_at", "updated_at")
    inlines = (MessageInline,)

    def get_queryset(self, request):
        from django.db.models import Count, OuterRef, Subquery

        first_question = Message.objects.filter(
            conversation=OuterRef("pk"), role=Message.Role.USER
        ).order_by("created_at", "pk").values("text")[:1]
        return super().get_queryset(request).annotate(
            _message_count=Count("messages"), _first_question=Subquery(first_question)
        )

    @admin.display(description="Первый вопрос")
    def first_question(self, obj):
        return (obj._first_question or "—")[:120]

    @admin.display(description="Сообщений")
    def message_count(self, obj):
        return obj._message_count

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
