from django.db import migrations
from django.utils import timezone


# Frozen defaults: migrations must not depend on future application code.
DEFAULT_ORDER = ['DON', 'KOMISSAR', 'DOKTOR', 'FUQARO', 'KOLDUN', 'DAYDI', 'MAFIA', 'KEZUVCHI', 'BORI', 'AFSUNGAR', 'FUQARO', 'SUIDSID', 'ADVOKAT', 'QOTIL', 'FUQARO', 'JANOB', 'JURNALIST', 'AFERIST', 'FITNACHI', 'SEHRGAR', 'AFSUNGAR', 'SERJANT', 'MAFIA', 'GAZABDOR', 'OVCHI', 'BORI', 'MINIOR', 'KIMYOGAR', 'AFSUNGAR', 'JOKER', 'FUQARO', 'BORI', 'AFSUNGAR', 'FUQARO', 'MAFIA', 'QOTIL', 'FUQARO', 'AFSUNGAR', 'BORI', 'MAFIA', 'FUQARO', 'AFSUNGAR', 'FUQARO', 'QOTIL', 'MAFIA', 'FUQARO', 'BORI', 'AFSUNGAR', 'FUQARO', 'MAFIA', 'FUQARO', 'QOTIL', 'AFSUNGAR', 'FUQARO', 'MAFIA', 'BORI', 'FUQARO', 'AFSUNGAR', 'FUQARO', 'MAFIA']
FITNACHI_INDEX = 18


def place_fitnachi_at_19(roles):
    if not isinstance(roles, list) or not all(isinstance(role, str) for role in roles):
        return list(DEFAULT_ORDER)
    updated = (roles[:60] + DEFAULT_ORDER[len(roles):60])[:60]
    if 'FITNACHI' in updated:
        first = updated.index('FITNACHI')
        # Keep every slot when repairing duplicate copies of this unique role.
        for index in range(first + 1, len(updated)):
            if updated[index] == 'FITNACHI':
                updated[index] = 'FUQARO'
        updated.pop(first)
    else:
        # Replace a civilian rather than discard a special role at position 19.
        civilians = [index for index, role in enumerate(updated) if role == 'FUQARO']
        replacement = next((index for index in civilians if index >= FITNACHI_INDEX),
                           civilians[-1] if civilians else FITNACHI_INDEX)
        updated.pop(replacement)
    updated.insert(FITNACHI_INDEX, 'FITNACHI')
    return updated


def update_all_group_orders(apps, schema_editor):
    model = apps.get_model('bot', 'ChatRoleOrder')
    manager = model.objects.using(schema_editor.connection.alias)
    for row in manager.select_for_update().all().iterator():
        updated = place_fitnachi_at_19(row.roles)
        if updated != row.roles:
            manager.filter(pk=row.pk).update(roles=updated, updated_at=timezone.now())


class Migration(migrations.Migration):
    dependencies = [('bot', '0005_fitnachi_role_order')]
    operations = [
        # Original custom positions cannot be reconstructed on rollback.
        migrations.RunPython(update_all_group_orders, migrations.RunPython.noop),
    ]
