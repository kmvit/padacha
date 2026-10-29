# padacha.ru — сайт «Падачи»

Сайт системы автоматизации кафе: страницы продукта, блог, заявки и
ИИ-ассистент. Django + SQLite. В админке редактируются страницы и статьи,
туда же приходят заявки с формы «Подключить».

Кафе, подписки, платежи и лицензии сюда не входят: они ведутся в hub
(`hub.padacha.ru/admin/`) на сервере сервиса.

| папка | что |
|---|---|
| `config/`, `pages/`, `blog/`, `leads/`, `templates/` | Django: страницы, статьи, заявки |
| `public/` | статика сайта (стили, картинки, `robots.txt`) — её отдаёт nginx |
| `content/blog/` | статьи в Markdown для заливки партиями (`import_articles`) |
| `legacy/` | снимок статического сайта, из него `import_pages` переносит страницы |
| `assistant/` | ИИ-ассистент на главной, отдельный процесс |
| `deploy/` | nginx, systemd и инструкция деплоя на hackit |

## Локально

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python manage.py migrate
.venv/bin/python manage.py import_pages
.venv/bin/python manage.py import_articles
.venv/bin/python manage.py createsuperuser
.venv/bin/python manage.py runserver
```

Сайт — http://127.0.0.1:8000/, админка — http://127.0.0.1:8000/upravlenie/.
В режиме разработки Django сам отдаёт файлы из `public/`.

## Что где править

- **Текст страницы** — админка → Страницы. Тело — html между шапкой и
  подвалом; метка `[[форма-заявки]]` ставит форму, `[[статьи]]` — карточки
  статей (на `/blog/`).
- **Статья** — админка → Статьи, текст в Markdown.
- **Меню шапки и ссылки подвала** — `pages/nav.py`.
- **Общий head, Метрика, подвал** — `templates/base.html`; главная —
  `templates/pages/home.html`.
- **Форма заявки** — `templates/partials/lead_form.html`, `public/lead.css`,
  `public/lead.js`.

Деплой — [deploy/README.md](deploy/README.md).
