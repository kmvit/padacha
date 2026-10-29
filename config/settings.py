"""Сайт padacha.ru — страницы, статьи блога и заявки.

Отдельно от пульта (лицензии и клиенты живут со сервисом): у сайта свой
сервер, своя база и своя админка. Устроен так же просто: SQLite (сотни
страниц и заявок, бэкап — копия одного файла), админка Django вместо
своего UI.

Картинки, стили и скрипты сайта — обычные файлы в public/, их отдаёт
nginx. Django рисует только html: страницы, статьи, sitemap.xml.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
# Веб-корень со статикой сайта (nav.css, *.webp, robots.txt …) — его отдаёт nginx
SITE_ROOT = BASE_DIR / "public"
# Исходники для переноса: страницы статического сайта и статьи в Markdown
LEGACY_DIR = BASE_DIR / "legacy"
CONTENT_DIR = BASE_DIR / "content"
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-insecure-change-me")
DEBUG = os.getenv("DJANGO_DEBUG", "1") == "1"
ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
# Изнутри сервера сайт открывает ассистент — за главной с ценами и FAQ
# (KB_SITE_URL=http://127.0.0.1:8120/). Снаружи сюда так не попасть: nginx
# пропускает только padacha.ru.
ALLOWED_HOSTS += [h for h in ("127.0.0.1", "localhost") if h not in ALLOWED_HOSTS]
CSRF_TRUSTED_ORIGINS = [o for o in os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",") if o]
ADMIN_PATH = os.getenv("ADMIN_PATH", "upravlenie/")

SITE_URL = "https://padacha.ru"
METRIKA = 112273830

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "django.contrib.redirects",
    "leads",
    "pages",
    "blog",
]
SITE_ID = 1

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Редиректы со старых адресов заводятся в админке (раздел «Перенаправления»)
    "django.contrib.redirects.middleware.RedirectFallbackMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "pages.context.site",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# База — файл рядом с кодом, но вне git (var/ в .gitignore).
VAR_DIR = BASE_DIR / "var"
VAR_DIR.mkdir(exist_ok=True)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": VAR_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
]

LANGUAGE_CODE = "ru-ru"
TIME_ZONE = "Europe/Moscow"
USE_I18N = True
USE_TZ = True

# Статика нужна только админке. Префикс — чтобы не пересекаться со статикой
# сайта, которая лежит прямо в корне.
STATIC_URL = "/admin-static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Адрес без «/» на конце — 301 на адрес со «/», как делал nginx.
APPEND_SLASH = True

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
