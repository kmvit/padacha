"""Адреса сайта. Html рисует Django, файлы (стили, картинки, robots.txt)
отдаёт nginx из public/ — см. deploy/nginx-padacha.conf.
"""
from django.conf import settings
from django.contrib import admin
from django.urls import path, re_path

from leads.views import submit
from pages import views

admin.site.site_header = "Падача — сайт"
admin.site.site_title = "Падача — сайт"
admin.site.index_title = "Заявки, страницы и статьи"

urlpatterns = [
    path(settings.ADMIN_PATH, admin.site.urls),
    path("api/lead/", submit, name="lead"),
    path("sitemap.xml", views.sitemap, name="sitemap"),
    path("blog/<slug:slug>/", views.article_view, name="article"),
]

if settings.DEBUG:
    # файл с расширением — статика сайта; на сервере до Django не доходит
    urlpatterns.append(re_path(r"^(?P<path>(?:[\w.-]+/)*[\w.-]+\.\w+)$", views.site_file))

urlpatterns += [
    path("", views.page_view, name="home"),
    re_path(r"^(?P<path>(?:[\w-]+/)+)$", views.page_view, name="page"),
]

handler404 = "pages.views.not_found"
