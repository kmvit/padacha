from django.db import migrations
from django.utils import timezone


SECTION = '''  <section id="kitchen-bar">
    <div class="wrap">
      <div class="head">
        <div class="lbl">Кухня и бар</div>
        <h2>Один заказ со стола, два экрана</h2>
        <p>Гость заказал пасту и лимонад. Официант отправляет заказ один раз. Повар получает пасту на экран кухни, а бармен видит лимонад в своей очереди.</p>
      </div>
      <div class="feature-spread">
        <img src="/kitchen.webp" width="2000" height="1288" loading="lazy" alt="Экран повара с очередью заказов, временем ожидания и готовностью блюд">
        <div class="feature-notes">
          <h3>Повар и бармен видят, что готовить дальше</h3>
          <p>Новая позиция появляется со звуком и подсветкой. На экране видно, что уже взяли в работу и сколько времени готовится каждое блюдо.</p>
          <h3>Лимонад можно подать сразу</h3>
          <p>Бармен отмечает лимонад готовым. У официанта в блоке «К подаче» появляются напиток и номер стола. Когда повар отметит пасту, официант увидит её там же.</p>
          <h3>Стоп-лист обновляется прямо со станции</h3>
          <p>Если на баре закончились лимоны, бармен ставит лимонад в стоп-лист со своего экрана. Напиток сразу пропадает из меню гостей.</p>
          <p><a href="/ekran-kuhni/">Подробнее об экранах кухни и бара →</a></p>
        </div>
      </div>
    </div>
  </section>

'''


def update_body(body):
    if 'id="kitchen-bar"' in body:
        return body
    anchor = '  <section id="shift-summary"'
    if anchor not in body:
        anchor = '</main>'
    body = body.replace(anchor, SECTION + anchor, 1)
    return body.replace('отправляет блюда на кухню, а напитки в бар.',
                        'отправляет блюда <a href="#kitchen-bar">на кухню, а напитки в бар</a>.', 1)


def forwards(apps, schema_editor):
    pages = apps.get_model('pages', 'Page').objects.using(schema_editor.connection.alias)
    for page in pages.filter(path='/dlya-kafe/'):
        body = update_body(page.body)
        if body != page.body:
            pages.filter(pk=page.pk).update(body=body, lastmod=timezone.localdate())


class Migration(migrations.Migration):
    dependencies = [('pages', '0007_landing_examples')]
    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
