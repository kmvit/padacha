# Деплой padacha.ru на сервер hackit

Сайт переезжает со старого сервера (там остаётся сервис: пульт, лицензии,
клиенты) на Jino VPS hackit, рядом с hack-its.ru:

```bash
ssh -J vpn -p 49263 root@cf24caf415b6.vps.myjino.ru
```

| что | юнит | адрес |
|---|---|---|
| сайт: страницы, статьи, заявки, админка | `padacha-web` | 127.0.0.1:8120 |
| ассистент на главной | `padacha-assistant` | 127.0.0.1:8101 (8100 — ассистент hack-its) |
| отправка новых статей в IndexNow | `padacha-indexnow.timer` | раз в 15 минут |
| стили, картинки, `robots.txt` (`public/`) | nginx | — |

TLS снимает прокси Jino (195.161.41.70), nginx на VPS слушает только :80 —
так же, как у hack-its.ru. Админка: `https://padacha.ru/upravlenie/`
(`ADMIN_PATH` в `.env`), разделы **Заявки**, **Страницы**, **Статьи**.

Пульт и `/api/license/` остаются на старом сервере. nginx проксирует эти
адреса туда по имени `pult.padacha.ru`, поэтому инстансы заведений менять
не нужно (шаг 1).

## 1. Старый сервер: отдельное имя для пульта

1. DNS: `A pult.padacha.ru` → IP старого сервера.
2. На старом сервере — server-блок `server_name pult.padacha.ru;` с теми же
   локациями `/pult/`, `/api/license/`, `/pult-static/`, что сейчас в
   `/etc/nginx/sites-available/padacha`, затем:

   ```bash
   sudo nginx -t && sudo systemctl reload nginx
   sudo certbot --nginx -d pult.padacha.ru
   ```

3. В `/opt/padacha/pult/.env` дописать `pult.padacha.ru` в
   `DJANGO_ALLOWED_HOSTS`, перезапустить `padacha-pult`.
4. Проверить: `curl -X POST https://pult.padacha.ru/api/license/ -d '{"key":"x"}'`
   отвечает 404 «Ключ не найден».

## 2. hackit: код и окружение

```bash
git clone https://github.com/kmvit/padacha.git /opt/padacha
cd /opt/padacha
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env
python3 -c "import secrets; print(secrets.token_urlsafe(50))"   # → DJANGO_SECRET_KEY в .env
```

## 3. База: перенос страниц и статей

Страницы берутся из `legacy/` (снимок статического сайта), статьи — из
`content/blog/*.md`:

```bash
cd /opt/padacha
.venv/bin/python manage.py migrate
.venv/bin/python manage.py import_pages
.venv/bin/python manage.py import_articles
.venv/bin/python manage.py createsuperuser
.venv/bin/python manage.py collectstatic --noinput
chown -R www-data:www-data var staticfiles
```

`import_pages` создаёт черновик `/soglasie/` — согласие на обработку
персональных данных, на него ведёт обязательная галочка в форме заявки
(152-ФЗ). **До переключения DNS** вписать в него реквизиты (ФИО ИП или
организация, ИНН, ОГРНИП, адрес, e-mail) и поставить «Опубликована».

Отложенные статьи получают время выхода и появятся на сайте сами.

## 4. Сервисы

```bash
cd /opt/padacha
cp deploy/padacha-web.service deploy/padacha-indexnow.service deploy/padacha-indexnow.timer /etc/systemd/system/
cp assistant/deploy/assistant.service /etc/systemd/system/padacha-assistant.service
systemctl daemon-reload
systemctl enable --now padacha-web padacha-indexnow.timer
```

Ассистент: venv и `.env` с ключами Yandex Cloud (перенести со старого
сервера, `/opt/padacha/assistant/.env`):

```bash
cd /opt/padacha/assistant
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env    # вписать YC_FOLDER_ID, YC_API_KEY, RELOAD_TOKEN
chown -R www-data:www-data data
systemctl enable --now padacha-assistant
```

Цены и FAQ ассистент берёт с главной у самого сайта (`KB_SITE_URL` в юните).
Поменяли цены в админке — `systemctl restart padacha-assistant`.

## 5. nginx

Конфиг рассчитан на соседство с hack-its.ru: свой `server_name`, только
:80, адрес пульта ищется при запросе (без записи `pult.padacha.ru` nginx
всё равно стартует).

```bash
cp /opt/padacha/deploy/nginx-padacha.conf /etc/nginx/sites-available/padacha
ln -s /etc/nginx/sites-available/padacha /etc/nginx/sites-enabled/padacha
nginx -t && systemctl reload nginx
```

Проверка до переключения DNS — прямо на сервере:

```bash
curl -sI -H 'Host: padacha.ru' http://127.0.0.1/sklad/        # 200
curl -s  -H 'Host: padacha.ru' http://127.0.0.1/sitemap.xml | head
curl -sI -H 'Host: padacha.ru' http://127.0.0.1/nav.css       # 200, файл
curl -s  -H 'Host: padacha.ru' http://127.0.0.1/api/assistant/health
curl -sI -H 'Host: hack-its.ru' http://127.0.0.1/             # соседа не задели
```

## 6. Переключение

1. За сутки снизить TTL записей `padacha.ru` и `www.padacha.ru` до 300.
2. В панели Jino привязать домены `padacha.ru` и `www.padacha.ru` к этому
   VPS и выпустить для них сертификат (как для hack-its.ru).
3. Если страницы на старом сайте правились после импорта —
   `import_pages --force` (статьи — `import_articles` без `--force`).
4. Направить `padacha.ru` и `www.padacha.ru` на прокси Jino (как у
   hack-its.ru).
5. Проверить: главная, статья, отправка заявки (появляется в админке),
   `https://padacha.ru/pult/` открывает вход в пульт, ассистент отвечает.
6. На старом сервере выключить cron `tools/publish.sh` и отдачу сайта —
   там остаётся только пульт.

## Обновление

```bash
cd /opt/padacha && git pull --ff-only
systemctl restart padacha-web        # миграции и статика админки — при старте
systemctl restart padacha-assistant  # если менялся assistant/
```

## Бэкап

Вся база — один файл: `cp /opt/padacha/var/db.sqlite3 ~/padacha-$(date +%F).sqlite3`.
