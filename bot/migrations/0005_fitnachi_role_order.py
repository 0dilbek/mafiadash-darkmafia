from django.db import migrations
from django.utils import timezone


# Freeze the previous defaults so later role releases cannot change this migration.
LEGACY_ORDER = ['DON', 'KOMISSAR', 'DOKTOR', 'FUQARO', 'KOLDUN', 'DAYDI', 'MAFIA', 'KEZUVCHI', 'BORI', 'AFSUNGAR', 'FUQARO', 'SUIDSID', 'ADVOKAT', 'QOTIL', 'FUQARO', 'JANOB', 'JURNALIST', 'AFERIST', 'FUQARO', 'SEHRGAR', 'AFSUNGAR', 'SERJANT', 'MAFIA', 'GAZABDOR', 'OVCHI', 'BORI', 'MINIOR', 'KIMYOGAR', 'AFSUNGAR', 'JOKER', 'FUQARO', 'BORI', 'AFSUNGAR', 'FUQARO', 'MAFIA', 'QOTIL', 'FUQARO', 'AFSUNGAR', 'BORI', 'MAFIA', 'FUQARO', 'AFSUNGAR', 'FUQARO', 'QOTIL', 'MAFIA', 'FUQARO', 'BORI', 'AFSUNGAR', 'FUQARO', 'MAFIA', 'FUQARO', 'QOTIL', 'AFSUNGAR', 'FUQARO', 'MAFIA', 'BORI', 'FUQARO', 'AFSUNGAR', 'FUQARO', 'MAFIA']


def add_fitnachi_to_legacy_defaults(apps, schema_editor):
    model = apps.get_model('bot', 'ChatRoleOrder')
    manager = model.objects.using(schema_editor.connection.alias)
    for row in manager.all().iterator():
        roles = row.roles
        if not isinstance(roles, list) or len(roles) not in (30, 60):
            continue
        legacy = LEGACY_ORDER[:len(roles)]
        legacy_citizen = list(legacy)
        legacy_citizen[4] = 'FUQARO'
        if roles != legacy and roles != legacy_citizen:
            continue
        updated = list(roles)
        updated[18] = 'FITNACHI'
        # Do not overwrite an administrator's concurrent edit.
        manager.filter(pk=row.pk, roles=roles).update(roles=updated, updated_at=timezone.now())


class Migration(migrations.Migration):
    dependencies = [('bot', '0004_chat_role_order')]
    operations = [migrations.RunPython(add_fitnachi_to_legacy_defaults, migrations.RunPython.noop)]
