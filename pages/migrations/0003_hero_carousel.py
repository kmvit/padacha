"""Первый экран главной: карусель из шести рисованных сцен вместо мозаики блюд.

Перенос коммита 270e766 из padacha-landing. Стили главной лежат в поле head,
разметка — в теле страницы, поэтому правка — заменой кусков. Скрипт карусели —
в шаблоне pages/home.html, картинки — в public/riso/img/hero-*.webp.

Кусок, которого нет (главную успели поправить в админке), пропускается, а не
роняет миграцию: она идёт при старте сайта, и падение остановило бы его.
"""
from django.db import migrations

#: (было, стало) — каждое «было» встречается в head или body ровно один раз
CHANGES = [
    [
        "    align-items: start;\n  }\n\n  .mosaic {\n",
        "    align-items: start;\n  }\n\n  /* Первый экран — карусель рисованных сцен: гость заказывает сам, кухня,\n     касса, склад, смены, деньги — по одной роли на кадр. Подписи — текстом поверх,\n     а не в картинке: читаются чётко и видны поисковику. */\n  .hero-pic { margin: 0; position: relative; border: 2px solid var(--ink); box-shadow: 8px 8px 0 var(--ink); background: var(--bone); overflow: hidden; }\n  .hp-track { display: flex; overflow-x: auto; scroll-snap-type: x mandatory; scrollbar-width: none; overscroll-behavior-x: contain; }\n  .hp-track::-webkit-scrollbar { display: none; }\n  .hp-slide { position: relative; flex: 0 0 100%; scroll-snap-align: start; aspect-ratio: 9 / 10; }\n  .hp-slide img { display: block; width: 100%; height: 100%; object-fit: cover; }\n  .hp-cap {\n    position: absolute; left: 0; bottom: 0; margin: 0; max-width: 86%;\n    background: var(--bone); color: var(--ink);\n    border-top: 2px solid var(--ink); border-right: 2px solid var(--ink);\n    padding: 12px 16px 14px;\n  }\n  .hp-cap b { display: block; font-family: var(--disp); font-weight: 900; font-size: clamp(20px, 2.1vw, 28px); line-height: 1.05; letter-spacing: -.01em; color: var(--poppy); }\n  .hp-cap span { display: block; font-family: var(--mono); font-size: 11px; font-weight: 500; letter-spacing: .06em; text-transform: uppercase; color: var(--jade-deep); margin-top: 6px; }\n  .hp-cap .hp-n { margin: 0 0 6px; font-weight: 700; color: var(--ink); }\n  .hp-dots { position: absolute; top: 12px; right: 12px; display: flex; gap: 6px; }\n  .hp-dots button { width: 20px; height: 10px; padding: 0; border: 2px solid var(--ink); background: var(--bone); cursor: pointer; transition: background .2s, width .2s var(--ease); }\n  .hp-dots button[aria-current=\"true\"] { width: 34px; background: var(--poppy); }\n\n  .mosaic {\n"
    ],
    [
        "    .hero-cta { margin-top: 16px; }\n    .mosaic { gap: 8px; }\n  }\n",
        "    .hero-cta { margin-top: 16px; }\n  }\n"
    ],
    [
        "    .hero-text { order: 1; }\n    .mosaic { order: 2; }\n    .ordergrid { grid-template-columns: 1fr; gap: 40px; }\n",
        "    .hero-text { order: 1; }\n    .hero-pic { order: 2; }\n    .ordergrid { grid-template-columns: 1fr; gap: 40px; }\n"
    ],
    [
        "    .brand { font-size: 1.45rem; }\n    .mosaic { grid-template-columns: repeat(3, 1fr); }\n    .tile.hide-sm { display: none; }\n",
        "    .brand { font-size: 1.45rem; }\n    .hero-pic { box-shadow: 5px 5px 0 var(--ink); }\n    .hp-cap { padding: 10px 12px 12px; }\n    .hp-cap b { font-size: 21px; }\n    .hp-cap span { font-size: 10px; }\n    .tile.hide-sm { display: none; }\n"
    ],
    [
        "\n      <div class=\"mosaic\" id=\"mosaic\" aria-label=\"Нарисованные блюда\">\n        <div class=\"tile pic\"><img src=\"/riso/img/tile-01.webp\" alt=\"Стопка блинов с маслом и сиропом\" width=\"560\" height=\"560\" loading=\"eager\"></div>\n        <div class=\"tile pic\"><img src=\"/riso/img/tile-02.webp\" alt=\"Яичница из двух яиц\" width=\"560\" height=\"560\" loading=\"eager\"></div>\n        <div class=\"tile pic\"><img src=\"/riso/img/tile-03.webp\" alt=\"Бургер\" width=\"560\" height=\"560\" loading=\"eager\"></div>\n        <div class=\"tile pic\"><img src=\"/riso/img/tile-04.webp\" alt=\"Кусок вишнёвого пирога\" width=\"560\" height=\"560\" loading=\"eager\"></div>\n        <div class=\"tile pic\"><img src=\"/riso/img/tile-05.webp\" alt=\"Чашка горячего кофе\" width=\"560\" height=\"560\" loading=\"eager\"></div>\n        <div class=\"tile pic hide-sm\"><img src=\"/riso/img/tile-06.webp\" alt=\"Молочный коктейль\" width=\"560\" height=\"560\" loading=\"eager\"></div>\n        <div class=\"tile gap\">№ 7 ·<br>рисуется</div>\n        <div class=\"tile pic\"><img src=\"/riso/img/tile-08.webp\" alt=\"Полоски бекона\" width=\"560\" height=\"560\" loading=\"lazy\"></div>\n        <div class=\"tile pic\"><img src=\"/riso/img/tile-09.webp\" alt=\"Вафли с маслом\" width=\"560\" height=\"560\" loading=\"lazy\"></div>\n        <div class=\"tile pic hide-sm\"><img src=\"/riso/img/tile-10.webp\" alt=\"Стакан апельсинового сока\" width=\"560\" height=\"560\" loading=\"lazy\"></div>\n        <div class=\"tile pic\"><img src=\"/riso/img/tile-11.webp\" alt=\"Барный стул\" width=\"560\" height=\"560\" loading=\"lazy\"></div>\n        <div class=\"tile pic hide-sm\"><img src=\"/riso/img/tile-12.webp\" alt=\"Кетчуп, соль и перец\" width=\"560\" height=\"560\" loading=\"lazy\"></div>\n      </div>\n\n",
        "\n      <figure class=\"hero-pic\" id=\"heroPic\" aria-roledescription=\"карусель\" aria-label=\"Падача в работе\">\n        <div class=\"hp-track\" id=\"hpTrack\">\n          <div class=\"hp-slide\" role=\"group\" aria-roledescription=\"слайд\" aria-label=\"1 из 6: Гость заказывает сам\">\n            <img src=\"/riso/img/hero-order.webp\" srcset=\"/riso/img/hero-order-600.webp 600w, /riso/img/hero-order.webp 900w\" sizes=\"(max-width: 1000px) 100vw, 46vw\" alt=\"Бургерная: гость сам выбирает заказ на планшете у стойки, пара за столиком сканирует QR-меню, над окном кухни — экран с заказами\" width=\"900\" height=\"1000\" loading=\"eager\" fetchpriority=\"high\">\n            <p class=\"hp-cap\"><span class=\"hp-n\">01 / 06</span><b>Гость заказывает сам</b><span>с планшета на стойке или по QR со стола</span></p>\n          </div>\n          <div class=\"hp-slide\" role=\"group\" aria-roledescription=\"слайд\" aria-label=\"2 из 6: Кухня видит заказы\">\n            <img src=\"/riso/img/hero-kitchen.webp\" srcset=\"/riso/img/hero-kitchen-600.webp 600w, /riso/img/hero-kitchen.webp 900w\" sizes=\"(max-width: 1000px) 100vw, 46vw\" alt=\"Повар у гриля смотрит на экран кухни с карточками заказов\" width=\"900\" height=\"1000\" loading=\"lazy\">\n            <p class=\"hp-cap\"><span class=\"hp-n\">02 / 06</span><b>Кухня видит заказы</b><span>экран кухни: очередь и тайминги блюд</span></p>\n          </div>\n          <div class=\"hp-slide\" role=\"group\" aria-roledescription=\"слайд\" aria-label=\"3 из 6: Принимайте заказы\">\n            <img src=\"/riso/img/hero-till.webp\" srcset=\"/riso/img/hero-till-600.webp 600w, /riso/img/hero-till.webp 900w\" sizes=\"(max-width: 1000px) 100vw, 46vw\" alt=\"Кассир у стойки пробивает заказ на планшете с фото блюд, рядом печатается чек\" width=\"900\" height=\"1000\" loading=\"lazy\">\n            <p class=\"hp-cap\"><span class=\"hp-n\">03 / 06</span><b>Принимайте заказы</b><span>касса и официант на одном планшете</span></p>\n          </div>\n          <div class=\"hp-slide\" role=\"group\" aria-roledescription=\"слайд\" aria-label=\"4 из 6: Ведите склад\">\n            <img src=\"/riso/img/hero-stock.webp\" srcset=\"/riso/img/hero-stock-600.webp 600w, /riso/img/hero-stock.webp 900w\" sizes=\"(max-width: 1000px) 100vw, 46vw\" alt=\"Кладовщик в кладовой сверяет остатки на планшете среди коробок и ящиков с овощами\" width=\"900\" height=\"1000\" loading=\"lazy\">\n            <p class=\"hp-cap\"><span class=\"hp-n\">04 / 06</span><b>Ведите склад</b><span>приход, остатки и списания без тетрадки</span></p>\n          </div>\n          <div class=\"hp-slide\" role=\"group\" aria-roledescription=\"слайд\" aria-label=\"5 из 6: Создавайте смены\">\n            <img src=\"/riso/img/hero-shifts.webp\" srcset=\"/riso/img/hero-shifts-600.webp 600w, /riso/img/hero-shifts.webp 900w\" sizes=\"(max-width: 1000px) 100vw, 46vw\" alt=\"Управляющая составляет график смен на ноутбуке, тот же график — на большом экране, за ней кухня\" width=\"900\" height=\"1000\" loading=\"lazy\">\n            <p class=\"hp-cap\"><span class=\"hp-n\">05 / 06</span><b>Создавайте смены</b><span>график, табель и зарплата — в одном окне</span></p>\n          </div>\n          <div class=\"hp-slide\" role=\"group\" aria-roledescription=\"слайд\" aria-label=\"6 из 6: Считайте деньги\">\n            <img src=\"/riso/img/hero-money.webp\" srcset=\"/riso/img/hero-money-600.webp 600w, /riso/img/hero-money.webp 900w\" sizes=\"(max-width: 1000px) 100vw, 46vw\" alt=\"Бухгалтер за столом смотрит отчёт о выручке на ноутбуке, рядом калькулятор и распечатки, за окном кухня\" width=\"900\" height=\"1000\" loading=\"lazy\">\n            <p class=\"hp-cap\"><span class=\"hp-n\">06 / 06</span><b>Считайте деньги</b><span>выручка, себестоимость и ведомость — сами</span></p>\n          </div>\n        </div>\n        <div class=\"hp-dots\" role=\"group\" aria-label=\"Слайды\">\n          <button type=\"button\" aria-label=\"Гость заказывает сам\" aria-current=\"true\"></button>\n          <button type=\"button\" aria-label=\"Кухня видит заказы\"></button>\n          <button type=\"button\" aria-label=\"Принимайте заказы\"></button>\n          <button type=\"button\" aria-label=\"Ведите склад\"></button>\n          <button type=\"button\" aria-label=\"Создавайте смены\"></button>\n          <button type=\"button\" aria-label=\"Считайте деньги\"></button>\n        </div>\n      </figure>\n\n"
    ]
]


def apply(apps, schema_editor):
    Page = apps.get_model("pages", "Page")
    page = Page.objects.filter(path="/").first()
    if page is None:
        return
    for old, new in CHANGES:
        for field in ("head", "body"):
            text = getattr(page, field)
            if text.count(old) == 1:
                setattr(page, field, text.replace(old, new))
                break
        else:
            if new not in page.head and new not in page.body:
                print(f"  карусель: не нашёлся кусок главной: {old[:60]!r} — пропущен")
    Page.objects.filter(pk=page.pk).update(head=page.head, body=page.body)


class Migration(migrations.Migration):
    dependencies = [("pages", "0002_contacts_email")]
    operations = [migrations.RunPython(apply, migrations.RunPython.noop)]
