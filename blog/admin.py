from django.contrib import admin
from django.utils import timezone

from .models import Article, Question, Related


class QuestionInline(admin.StackedInline):
    model = Question
    extra = 0


class RelatedInline(admin.TabularInline):
    model = Related
    extra = 0


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "published_at", "state", "updated_at")
    list_filter = ("is_published",)
    search_fields = ("title", "slug", "body")
    date_hierarchy = "published_at"
    save_on_top = True
    inlines = [QuestionInline, RelatedInline]
    fieldsets = (
        (None, {"fields": ("slug", "is_published", "published_at", "modified")}),
        ("Поиск", {"fields": ("title", "description")}),
        ("На странице", {"fields": ("h1", "crumb", "lede", "body")}),
        ("В списке статей", {"fields": ("meta", "card")}),
        ("После текста", {"fields": ("faq_title", "call_title", "call_text")}),
        ("Служебное", {"classes": ("collapse",), "fields": ("show_time", "indexnow_at")}),
    )
    readonly_fields = ("indexnow_at",)

    @admin.display(description="Состояние")
    def state(self, obj):
        if not obj.is_published:
            return "черновик"
        return "на сайте" if obj.published_at <= timezone.now() else "ждёт выхода"

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        field = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name == "body":
            field.widget.attrs.update(rows=40, style="width:100%;font-family:ui-monospace,Menlo,monospace;font-size:13px")
        return field
