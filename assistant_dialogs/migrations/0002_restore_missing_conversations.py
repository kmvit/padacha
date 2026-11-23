import uuid

from django.db import migrations
from django.db.models import Max, Min


def restore_parents(apps, schema_editor):
    db = schema_editor.connection.alias
    conversations = apps.get_model("assistant_dialogs", "Conversation").objects.using(db)
    messages = apps.get_model("assistant_dialogs", "Message").objects.using(db)
    missing = (messages.exclude(conversation_id__in=conversations.values("pk"))
               .order_by().values("conversation_id")
               .annotate(first=Min("created_at"), last=Max("created_at")))
    for row in list(missing):
        conversation = conversations.create(pk=row["conversation_id"], session_id=uuid.uuid4().hex)
        conversations.filter(pk=conversation.pk).update(created_at=row["first"], updated_at=row["last"])


class Migration(migrations.Migration):
    dependencies = [("assistant_dialogs", "0001_initial")]
    operations = [migrations.RunPython(restore_parents, migrations.RunPython.noop)]
