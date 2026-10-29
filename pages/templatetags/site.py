from django import template
from django.utils.safestring import mark_safe

from pages import nav

register = template.Library()


@register.simple_tag
def site_header(url: str) -> str:
    return mark_safe(nav.header(url))


@register.simple_tag
def footer_links() -> str:
    return mark_safe(nav.footer_links())


@register.simple_tag
def home_footer_links() -> str:
    return mark_safe(nav.home_footer_links())
