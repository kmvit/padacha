"""Добавить примеры учёта и переставить существующий блок сверки кассы."""
from datetime import date

from django.db import migrations


CAFE = '''  <section id="shift-summary" class="landing-feature">
    <div class="wrap">
      <div class="head">
        <div class="lbl">Учёт в кафе</div>
        <h2>Что владелец видит к концу смены</h2>
      </div>
      <div class="feature-spread">
        <img src="/process-shift.webp" width="1536" height="1024" loading="lazy" alt="Команда кафе подводит итоги смены">
        <div class="feature-notes">
          <h3><a href="/oplata/#cash-check">Сколько денег прошло через кассу</a></h3>
          <p>Откройте день и сверьте наличные с кассой, оплату картой и онлайн — с выписками банка. В журнале можно найти платёж по заказу и проверить возврат.</p>
          <h3><a href="/sklad/#portion-cost">Какие продукты ушли со склада</a></h3>
          <p>Когда кухня отдаёт пасту, со склада списываются макароны, соус и сыр по техкарте. Остатки обновляются, а стоимость порции считается по последним закупочным ценам.</p>
          <h3><a href="/personal/">Сколько начислено команде</a></h3>
          <p>Менеджер отмечает, кто работал и сколько часов. По выбранным правилам система рассчитывает ставку, долю выручки или личные надбавки. В ведомости видно, сколько начислено, сколько уже выплатили и сколько осталось.</p>
        </div>
      </div>
    </div>
  </section>

'''

STOCK = '''  <section id="portion-cost" class="landing-feature">
    <div class="wrap">
      <div class="head">
        <div class="lbl">Пример калькуляции</div>
        <h2>Сколько стоит порция пасты</h2>
        <p>В техкарте укажите расход продуктов на порцию. «Падача» возьмёт цены из последнего прихода. Вот как выглядит расчёт на условных ценах.</p>
      </div>
      <div class="feature-spread">
        <img src="/pasta-cost.webp" width="1100" height="733" loading="lazy" alt="Пенне с томатным соусом и сыром рядом с ингредиентами для порции">
        <div class="portion-sheet">
          <table>
            <caption>Пенне с томатным соусом · 1 порция</caption>
            <thead><tr><th scope="col">Продукт</th><th scope="col">Расход</th><th scope="col">₽/кг</th><th scope="col">Сумма</th></tr></thead>
            <tbody>
              <tr><th scope="row">Пенне</th><td>100 г</td><td>200</td><td>20 ₽</td></tr>
              <tr><th scope="row">Соус</th><td>120 г</td><td>250</td><td>30 ₽</td></tr>
              <tr><th scope="row">Пармезан</th><td>20 г</td><td>1 500</td><td>30 ₽</td></tr>
              <tr><th scope="row">Масло</th><td>10 г</td><td>500</td><td>5 ₽</td></tr>
            </tbody>
            <tfoot><tr><th colspan="3" scope="row">Себестоимость порции</th><td>85 ₽</td></tr></tfoot>
          </table>
          <p>При цене в меню 340 ₽ продукты составляют четверть цены блюда. <strong>Фудкост — 25 %.</strong></p>
        </div>
      </div>
    </div>
  </section>

'''


def section_start(body, heading):
    return body.rindex('  <section', 0, body.index(f'<h2>{heading}</h2>'))


def update_body(path, body):
    if path == '/dlya-kafe/' and 'id="shift-summary"' not in body:
        start = section_start(body, 'Всё о столе — на одном экране')
        body = body[:start] + CAFE + body[start:]
        end = body.index('</p>', body.index('<p class="lede">'))
        return body[:end] + ' В конце смены вы видите выручку, расход продуктов и начисления сотрудникам. Тариф «Зал» — 5 990 ₽ в месяц за заведение.' + body[end:]
    if path == '/sklad/' and 'id="portion-cost"' not in body:
        start = section_start(body, 'Продали блюдо — склад уже знает')
        return body[:start] + STOCK + body[start:]
    if path == '/oplata/' and 'id="cash-check"' not in body:
        start = section_start(body, 'День в деньгах — на одном экране')
        end = body.index('</section>', start) + len('</section>')
        section = body[start:end].replace('<section>', '<section id="cash-check" class="landing-feature">', 1)
        body = body[:start] + body[end:].lstrip('\n')
        start = section_start(body, 'Заказ на Эвоторе, оплата в Падаче')
        return body[:start] + section + '\n\n' + body[start:]
    return body


def forwards(apps, schema_editor):
    pages = apps.get_model('pages', 'Page').objects.using(schema_editor.connection.alias)
    for page in pages.filter(path__in=['/dlya-kafe/', '/sklad/', '/oplata/']):
        body = update_body(page.path, page.body)
        if body != page.body:
            pages.filter(pk=page.pk).update(body=body, lastmod=max(page.lastmod, date(2026, 11, 23)))


class Migration(migrations.Migration):
    dependencies = [('pages', '0006_order_channels')]
    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
