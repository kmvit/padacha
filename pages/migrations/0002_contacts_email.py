"""Почта info@padacha.ru в блоке контактов уже заведённых страниц."""
from django.db import migrations


def add_email(apps, schema_editor):
    from pages.contacts import with_email

    Page = apps.get_model("pages", "Page")
    for page in Page.objects.all():
        body = with_email(page.body)
        if body != page.body:
            Page.objects.filter(pk=page.pk).update(body=body)


class Migration(migrations.Migration):
    dependencies = [("pages", "0001_initial")]
    operations = [migrations.RunPython(add_email, migrations.RunPython.noop)]
