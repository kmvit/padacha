"""Приём заявки с формы. Форма шлёт fetch и ждёт JSON; без JavaScript —
обычный POST, и в ответ страница «Заявка отправлена».

CSRF отключён намеренно: страницы отдаются без сессий и кук, а подделать
от чужого имени тут нечего. От ботов — скрытое поле и лимит по IP.
"""
from datetime import timedelta

from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import Lead

LIMIT_PER_IP = 5          # заявок с одного адреса
LIMIT_WINDOW = timedelta(minutes=30)
UTM = ("utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term")


def client_ip(request) -> str | None:
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    return (forwarded.split(",")[0].strip() if forwarded else request.META.get("REMOTE_ADDR")) or None


def answer(request, ok: bool, error: str = "", status: int = 200):
    if "application/json" in request.headers.get("Accept", ""):
        return JsonResponse({"ok": ok, "error": error}, status=status)
    meta = {"title": "Заявка — Падача", "noindex": True, "path": request.path}
    return render(request, "leads/sent.html", {"ok": ok, "error": error, "meta": meta}, status=status)


@csrf_exempt
@require_POST
def submit(request):
    data = request.POST
    cut = lambda key, n: (data.get(key) or "").strip()[:n]  # noqa: E731

    if data.get("website"):  # скрытое поле: человек его не видит и не заполняет
        return answer(request, True)

    name, phone = cut("name", 120), cut("phone", 120)
    if not name or len("".join(c for c in phone if c.isdigit())) < 5 and "@" not in phone:
        return answer(request, False, "Оставьте имя и телефон — без них не перезвонить.", 400)

    # 152-ФЗ: без отдельного согласия персональные данные не принимаем
    if not data.get("consent"):
        return answer(request, False, "Отметьте согласие на обработку персональных данных.", 400)

    ip = client_ip(request)
    if ip and Lead.objects.filter(ip=ip, created_at__gte=timezone.now() - LIMIT_WINDOW).count() >= LIMIT_PER_IP:
        return answer(request, False, "Слишком много заявок подряд. Позвоните нам — так быстрее.", 429)

    venue = cut("venue", 20)
    Lead.objects.create(
        name=name,
        phone=phone,
        venue=venue if venue in Lead.Venue.values else "",
        comment=cut("comment", 2000),
        consent_at=timezone.now(),
        page=cut("page", 300),
        referrer=cut("referrer", 500),
        ip=ip,
        user_agent=request.headers.get("User-Agent", "")[:300],
        **{key: cut(key, 200) for key in UTM},
    )
    return answer(request, True)
