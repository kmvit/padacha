"""Carousel arrow migration."""
from django.db import migrations
OLD_STYLE = "  .hp-dots button[aria-current=\"true\"] { width: 34px; background: var(--poppy); }"
NEW_STYLE = OLD_STYLE + """
  .hp-arrow { position: absolute; z-index: 2; top: 50%; transform: translateY(-50%); display: grid; place-items: center; width: 48px; height: 52px; padding: 0; color: var(--ink); background: var(--bone); border: 2px solid var(--ink); box-shadow: 3px 3px 0 var(--ink); cursor: pointer; transition: color .15s, background .15s, box-shadow .15s, transform .15s; }
  .hp-arrow:hover { color: var(--bone); background: var(--poppy); box-shadow: 1px 1px 0 var(--ink); }
  .hp-arrow:active { transform: translate(2px, calc(-50% + 2px)); }
  .hp-arrow:focus-visible { outline: 3px solid var(--jade-deep); outline-offset: 3px; }
  .hp-arrow svg { width: 24px; height: 24px; fill: none; stroke: currentColor; stroke-width: 2.5; stroke-linecap: round; stroke-linejoin: round; }
  .hp-prev { left: 12px; }
  .hp-next { right: 12px; }
  @media (max-width: 600px) { .hp-arrow { width: 42px; height: 46px; } .hp-prev { left: 8px; } .hp-next { right: 8px; } }"""
OLD_BODY = '        <div class="hp-dots" role="group" aria-label="Слайды">'
NEW_BODY = '        <button class="hp-arrow hp-prev" id="hpPrev" type="button" aria-label="Предыдущий слайд"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="m15 18-6-6 6-6"></path></svg></button>\n        <button class="hp-arrow hp-next" id="hpNext" type="button" aria-label="Следующий слайд"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="m9 18 6-6-6-6"></path></svg></button>\n' + OLD_BODY
def forwards(apps, schema_editor):
    Page = apps.get_model("pages", "Page")
    page = Page.objects.filter(path="/").first()
    if page is None: return
    head = page.head.replace(OLD_STYLE, NEW_STYLE, 1) if OLD_STYLE in page.head else page.head
    body = page.body.replace(OLD_BODY, NEW_BODY, 1) if OLD_BODY in page.body else page.body
    Page.objects.filter(pk=page.pk).update(head=head, body=body)
class Migration(migrations.Migration):
    dependencies = [("pages", "0003_hero_carousel")]
    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
