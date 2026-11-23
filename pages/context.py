from django.conf import settings

from .contacts import MAX_URL, TELEGRAM_URL


def site(request):
    return {"SITE_URL": settings.SITE_URL, "METRIKA": settings.METRIKA, "COMPANY": settings.COMPANY,
            "TELEGRAM_URL": TELEGRAM_URL, "MAX_URL": MAX_URL}
