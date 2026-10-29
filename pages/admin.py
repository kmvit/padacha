from django.contrib import admin

from .models import Page


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ("path", "title", "is_published", "in_sitemap", "lastmod", "updated_at")
    list_filter = ("is_published", "layout")
    search_fields = ("path", "title", "body")
    save_on_top = True
    fieldsets = (
        (None, {"fields": ("path", "is_published", "layout")}),
        ("Поиск и репосты", {"fields": ("title", "description", "og_title", "og_description", "noindex")}),
        ("Содержимое", {"fields": ("body", "jsonld")}),
        ("sitemap.xml", {"fields": ("in_sitemap", "priority", "changefreq", "lastmod")}),
        ("Служебное", {"classes": ("collapse",), "fields": ("head", "theme_color")}),
    )

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        field = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name in ("body", "head", "jsonld"):
            # моноширинный и широкий: это разметка, а не текст
            field.widget.attrs.update(rows=40 if db_field.name == "body" else 14, spellcheck="false",
                                      style="width:100%;font-family:ui-monospace,Menlo,monospace;font-size:12px")
        return field

    def view_on_site(self, obj):
        return obj.path
