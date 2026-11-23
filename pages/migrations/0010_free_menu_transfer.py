from django.db import migrations
from django.db.models import F, Value
from django.db.models.functions import Replace
from django.utils import timezone


def forwards(apps, schema_editor):
    old = "Внедрение с переносом меню — 15\xa0000\xa0₽ один раз."
    new = "Подключение и перенос меню бесплатны на обоих тарифах."
    pages = apps.get_model("pages", "Page").objects.using(schema_editor.connection.alias)
    pages.filter(path="/sravnenie/", body__contains=old).update(
        body=Replace(F("body"), Value(old), Value(new)),
        lastmod=timezone.localdate(),
    )


class Migration(migrations.Migration):
    dependencies = [("pages", "0009_site_contacts")]
    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
