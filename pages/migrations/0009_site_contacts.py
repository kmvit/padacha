from django.db import migrations
from django.utils import timezone

from pages.contacts import update_messengers


def forwards(apps, schema_editor):
    pages = apps.get_model("pages", "Page").objects.using(schema_editor.connection.alias)
    for page in pages.all():
        body = update_messengers(page.body)
        if body != page.body:
            pages.filter(pk=page.pk).update(body=body, lastmod=timezone.localdate())


class Migration(migrations.Migration):
    dependencies = [("pages", "0008_cafe_kitchen_bar")]
    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
