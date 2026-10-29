from django.contrib import admin

from .models import Lead


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ("created_at", "name", "phone", "venue", "status", "page", "utm_source")
    list_display_links = ("created_at", "name")
    list_editable = ("status",)
    list_filter = ("status", "venue", "created_at", "utm_source")
    search_fields = ("name", "phone", "comment", "note")
    date_hierarchy = "created_at"
    readonly_fields = ("created_at", "consent_at", "page", "referrer", "utm_source", "utm_medium", "utm_campaign",
                       "utm_content", "utm_term", "ip", "user_agent")
    fieldsets = (
        (None, {"fields": ("created_at", "name", "phone", "venue", "comment", "consent_at")}),
        ("Работа с заявкой", {"fields": ("status", "note")}),
        ("Откуда пришла", {"classes": ("collapse",), "fields": (
            "page", "referrer", "utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term",
            "ip", "user_agent")}),
    )
