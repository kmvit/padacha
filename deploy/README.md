# Деплой padacha.ru на сервер hackit

Сайт переезжает со старого сервера на Jino VPS hackit, рядом с hack-its.ru.
На старом сервере остаётся сервис: hub и поддомены заведений. Кафе,
подписки, платежи и лицензии ведутся в hub (`hub.padacha.ru/admin/`), сайт
к ним отношения не имеет.

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

## 1. hackit: код и окружение

```bash
git clone https://github.com/kmvit/padacha.git /opt/padacha
cd /opt/padacha
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env
python3 -c "import secrets; print(secrets.token_urlsafe(50))"   # → DJANGO_SECRET_KEY в .env
```

## 2. База: перенос страниц и статей

Страницы берутся из `legacy/` (снимок статического сайта), статьи — из
`content/blog/*.md`:

```bash
cd /opt/padacha
.venv/bin/python manage.py migrate
.venv/bin/python manage.py import_pages
.venv/bin/python manage.py import_articles
.venv/bin/python manage.py createsuperuser
.venv/bin/python manage.py collectstatic --noinput
chown -R www-data:www-data var staticfiles .env && chmod 640 .env
```

`import_pages` создаёт черновик `/soglasie/` — согласие на обработку
персональных данных, на него ведёт обязательная галочка в форме заявки
(152-ФЗ). **До переключения DNS** вписать в него реквизиты (ФИО ИП или
организация, ИНН, ОГРНИП, адрес, e-mail) и поставить «Опубликована».

Отложенные статьи получают время выхода и появятся на сайте сами.

## 3. Сервисы

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

## 4. nginx

Конфиг рассчитан на соседство с hack-its.ru: свой `server_name`, только :80.

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

## 5. Переключение

1. Проверить сертификат для `padacha.ru` и `www.padacha.ru` в панели Jino
   (для привязки к hackit он нужен на прокси, как у hack-its.ru).
2. Если после 29.10 что-то правили в `padacha-landing`, перенести сюда:
   новые статьи `content/blog/*.md` → `content/blog/` и `import_articles`;
   правки страниц → `legacy/` и `import_pages --force` (перезапишет правки,
   сделанные в админке).
3. В Яндекс Метрике (счётчик 112273830) добавить цель «JavaScript-событие»
   `lead_form` — её шлёт форма заявки после отправки. Цели кликов
   (`click_connect`, `click_phone`, `click_messenger`, `click_demo`) прежние.
4. В панели Jino перепривязать `padacha.ru` и `www.padacha.ru` со старого
   VPS на hackit (`cf24caf415b6.vps.myjino.ru`). DNS менять не нужно —
   домен уже смотрит на прокси Jino; откат — привязать обратно.
5. Проверить: главная, статья, отправка заявки (появляется в админке),
   ассистент отвечает; hub и поддомены заведений работают как раньше.
6. На старом сервере выключить cron `tools/publish.sh` и отдачу сайта
   из конфига nginx `padacha` (старый пульт `/pult/` уехал в hub и больше не
   нужен; сервис `padacha-pult` можно выключить). Поддомены — в `padacha-app`,
   их не трогать.
7. Сертификат `padacha.ru` на старом сервере общий: `padacha.ru`, `www`,
   `demo`, `hub`, `monti` (до 11.12.2026). После переезда certbot не продлит
   его из-за `padacha.ru` и `www` — перевыпустить без них:
   `certbot --nginx --cert-name padacha.ru -d demo.padacha.ru -d hub.padacha.ru -d monti.padacha.ru`.

## Обновление

```bash
cd /opt/padacha && git pull --ff-only
systemctl restart padacha-web        # миграции и статика админки — при старте
systemctl restart padacha-assistant  # если менялся assistant/
```

## Бэкап

Вся база — один файл: `cp /opt/padacha/var/db.sqlite3 ~/padacha-$(date +%F).sqlite3`.
