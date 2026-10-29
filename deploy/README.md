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

Оба сервера — VPS Jino, и `padacha.ru` (как и любой `*.padacha.ru`)
уже смотрит на прокси Jino 195.161.41.70. Куда прокси отправит домен,
решает привязка в панели Jino, а не A-запись. Пока `pult.padacha.ru`
никуда не привязан, прокси отвечает на него 400.

1. В панели Jino привязать `pult.padacha.ru` к старому VPS
   (`a318f7177847.vps.myjino.ru`) и выпустить для него сертификат.
2. На старом сервере — server-блок `server_name pult.padacha.ru;` с теми же
   локациями `/pult/`, `/api/license/`, `/pult-static/`, что сейчас в
   `/etc/nginx/sites-available/padacha`, затем:

   ```bash
   sudo nginx -t && sudo systemctl reload nginx
   ```

   (если старый VPS сам держит сертификаты через certbot, как для
   padacha.ru, — ещё `sudo certbot --nginx -d pult.padacha.ru`)

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
chown -R www-data:www-data var staticfiles .env && chmod 640 .env
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

1. Убедиться, что шаг 1 сделан: `https://pult.padacha.ru/api/license/`
   отвечает, иначе после переключения инстансы заведений потеряют лицензии.
2. Проверить сертификат для `padacha.ru` и `www.padacha.ru` в панели Jino
   (для привязки к hackit он нужен на прокси, как у hack-its.ru).
3. Если после 29.10 что-то правили в `padacha-landing`, перенести сюда:
   новые статьи `content/blog/*.md` → `content/blog/` и `import_articles`;
   правки страниц → `legacy/` и `import_pages --force` (перезапишет правки,
   сделанные в админке).
4. В Яндекс Метрике (счётчик 112273830) добавить цель «JavaScript-событие»
   `lead_form` — её шлёт форма заявки после отправки. Цели кликов
   (`click_connect`, `click_phone`, `click_messenger`, `click_demo`) прежние.
5. В панели Jino перепривязать `padacha.ru` и `www.padacha.ru` со старого
   VPS на hackit (`cf24caf415b6.vps.myjino.ru`). DNS менять не нужно —
   домен уже смотрит на прокси Jino; откат — привязать обратно.
6. Проверить: главная, статья, отправка заявки (появляется в админке),
   `https://padacha.ru/pult/` открывает вход в пульт, ассистент отвечает.
7. На старом сервере выключить cron `tools/publish.sh` и отдачу сайта —
   там остаётся только пульт.

## Обновление

```bash
cd /opt/padacha && git pull --ff-only
systemctl restart padacha-web        # миграции и статика админки — при старте
systemctl restart padacha-assistant  # если менялся assistant/
```

## Бэкап

Вся база — один файл: `cp /opt/padacha/var/db.sqlite3 ~/padacha-$(date +%F).sqlite3`.
