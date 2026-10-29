"""Страницы сайта, список статей, статья, sitemap.xml и 404."""
import json
from pathlib import Path

from django.conf import settings
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.views.decorators.http import require_safe
from django.views.static import serve

from blog import markup
from blog.models import Article

from .models import ARTICLES, LEAD_FORM, Page

ORG = {"@type": "Organization", "name": "Падача", "url": f"{settings.SITE_URL}/"}


def page_meta(page: Page, **extra) -> dict:
    return {
        "path": page.path, "title": page.title, "description": page.description,
        "og_title": page.og_title, "og_description": page.og_description,
        "theme_color": page.theme_color, "noindex": page.noindex, "jsonld": page.jsonld, **extra,
    }


def fill(page: Page, request, meta: dict, **ctx) -> str:
    """Тело страницы с метками: форма заявки и карточки статей."""
    body = page.body
    if LEAD_FORM in body:
        body = body.replace(LEAD_FORM, render_to_string("partials/lead_form.html", {"meta": meta}, request).rstrip("\n"))
    if ARTICLES in body:
        body = body.replace(ARTICLES, render_to_string("blog/cards.html", ctx, request).rstrip("\n"))
    return mark_safe(body)


def visible(page: Page, request) -> bool:
    return page.is_published or request.user.is_staff


@require_safe
def page_view(request, path: str = ""):
    page = Page.objects.filter(path=f"/{path}").first()
    if not page or not visible(page, request):
        raise Http404
    if page.path == "/blog/":
        return blog_index(request, page)
    meta = page_meta(page)
    template = "pages/home.html" if page.layout == Page.Layout.HOME else "pages/page.html"
    return render(request, template, {"page": page, "meta": meta, "body": fill(page, request, meta)})


def blog_index(request, page: Page):
    articles = list(Article.objects.live())
    meta = page_meta(page)
    # микроразметка Blog: список статей — из базы, остальное — как в поле страницы
    if page.jsonld:
        data = json.loads(page.jsonld)
        for node in data.get("@graph", []):
            if node.get("@type") == "Blog":
                node["blogPost"] = [
                    {
                        "@type": "BlogPosting",
                        "headline": a.heading_line,
                        "description": a.card or a.description,
                        "url": f"{settings.SITE_URL}{a.get_absolute_url()}",
                        "datePublished": a.published_iso(),
                        "author": {"@type": "Organization", "name": "Падача"},
                    }
                    for a in articles
                ]
        meta["jsonld"] = json.dumps(data, ensure_ascii=False, indent=2)
    body = fill(page, request, meta, articles=articles)
    return render(request, "pages/page.html", {"page": page, "meta": meta, "body": body})


def article_jsonld(a: Article, questions) -> str:
    url = f"{settings.SITE_URL}{a.get_absolute_url()}"
    graph = [
        {
            "@type": "Article",
            "headline": a.heading_line,
            "description": a.description,
            "inLanguage": "ru",
            "datePublished": a.published_iso(),
            "dateModified": a.modified_iso(),
            "image": f"{settings.SITE_URL}/promo-poster.jpg",
            "mainEntityOfPage": {"@type": "WebPage", "@id": url},
            "author": ORG,
            "publisher": ORG,
        },
        {
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Падача", "item": f"{settings.SITE_URL}/"},
                {"@type": "ListItem", "position": 2, "name": "Статьи", "item": f"{settings.SITE_URL}/blog/"},
                {"@type": "ListItem", "position": 3, "name": a.crumb, "item": url},
            ],
        },
    ]
    if questions:
        graph.append({
            "@type": "FAQPage",
            "mainEntity": [
                {"@type": "Question", "name": q.question,
                 "acceptedAnswer": {"@type": "Answer", "text": markup.plain(q.answer)}}
                for q in questions
            ],
        })
    return json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False, indent=2)


@require_safe
def article_view(request, slug: str):
    article = get_object_or_404(Article, slug=slug)
    if not article.is_live and not request.user.is_staff:
        raise Http404
    questions, related = list(article.questions.all()), list(article.related.all())
    meta = {
        "path": article.get_absolute_url(), "title": article.title, "description": article.description,
        "og_type": "article", "jsonld": article_jsonld(article, questions),
    }
    return render(request, "blog/article.html", {
        "article": article, "questions": questions, "related": related, "meta": meta,
    })


@require_safe
def sitemap(request):
    pages = [(p.path, p.lastmod, p.changefreq, p.priority)
             for p in Page.objects.filter(is_published=True, in_sitemap=True, noindex=False)]
    articles = list(Article.objects.live())
    if articles:  # список статей меняется вместе с новой статьей
        newest = max(a.lastmod for a in articles)
        pages = [(p, max(m, newest) if p == "/blog/" else m, f, pr) for p, m, f, pr in pages]
    pages.sort(key=lambda row: (-row[3], row[0] != "/", row[0]))
    rows = pages + [(a.get_absolute_url(), a.lastmod, "monthly", 0.8) for a in articles]
    xml = render_to_string("sitemap.xml", {"rows": rows, "SITE_URL": settings.SITE_URL})
    return HttpResponse(xml, content_type="application/xml; charset=utf-8")


def not_found(request, exception=None):
    page = Page.objects.filter(path="/404/").first()
    if not page:
        return HttpResponse("Страница не найдена", status=404, content_type="text/plain; charset=utf-8")
    meta = page_meta(page, noindex=True)
    return render(request, "pages/page.html", {"page": page, "meta": meta, "body": fill(page, request, meta)},
                  status=404)


def site_file(request, path: str):
    """Только для разработки: картинки и стили сайта из public/.
    На сервере их отдаёт nginx, сюда такие запросы не доходят."""
    if any(part.startswith(".") for part in Path(path).parts):
        raise Http404
    return serve(request, path, document_root=settings.SITE_ROOT)
