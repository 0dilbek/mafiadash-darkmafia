import importlib
from collections import Counter
from types import SimpleNamespace

from django.apps import apps
from django.db import connection
from django.test import SimpleTestCase, TestCase

from .models import ChatRoleOrder

migration = importlib.import_module('bot.migrations.0006_fitnachi_all_group_orders')


class FitnachiPositionTests(SimpleTestCase):
    def test_moves_existing_fitnachi_from_any_position(self):
        for index in range(60):
            roles = list(migration.DEFAULT_ORDER)
            roles[18], roles[index] = roles[index], roles[18]
            updated = migration.place_fitnachi_at_19(roles)
            self.assertEqual(updated[18], 'FITNACHI')
            self.assertEqual(Counter(updated), Counter(roles))
            self.assertEqual([r for r in updated if r != 'FITNACHI'], [r for r in roles if r != 'FITNACHI'])

    def test_adds_missing_role_without_discarding_special_role_at_19(self):
        roles = list(migration.DEFAULT_ORDER)
        roles[18] = 'DOKTOR'
        expected_counts = Counter(roles)
        expected_counts['FUQARO'] -= 1
        expected_counts['FITNACHI'] += 1
        updated = migration.place_fitnachi_at_19(roles)
        self.assertEqual(updated[18], 'FITNACHI')
        self.assertEqual(Counter(updated), expected_counts)
        self.assertEqual(len(updated), 60)
        self.assertEqual(roles[18], 'DOKTOR')

    def test_removes_duplicate_fitnachi_and_preserves_slots(self):
        roles = list(migration.DEFAULT_ORDER)
        roles[3] = roles[40] = 'FITNACHI'
        updated = migration.place_fitnachi_at_19(roles)
        self.assertEqual(updated[18], 'FITNACHI')
        self.assertEqual(updated.count('FITNACHI'), 1)
        self.assertEqual(len(updated), 60)

    def test_handles_short_empty_invalid_and_no_civilian_orders(self):
        for roles in ([], None, {}, ['DON'] * 60, migration.DEFAULT_ORDER[:10], migration.DEFAULT_ORDER[:30], [None]):
            with self.subTest(roles=roles):
                updated = migration.place_fitnachi_at_19(roles)
                self.assertEqual(len(updated), 60)
                self.assertEqual(updated[18], 'FITNACHI')
                self.assertEqual(updated.count('FITNACHI'), 1)

    def test_repeat_does_not_change_correct_order(self):
        self.assertEqual(migration.place_fitnachi_at_19(migration.DEFAULT_ORDER), migration.DEFAULT_ORDER)


class AllGroupOrdersMigrationTests(TestCase):
    def test_updates_every_custom_group_and_is_idempotent(self):
        for chat_id, index in enumerate((0, 4, 18, 35, 59), 1):
            roles = list(migration.DEFAULT_ORDER)
            roles[18], roles[index] = roles[index], roles[18]
            ChatRoleOrder.objects.create(chat_id=-chat_id, roles=roles)
        ChatRoleOrder.objects.create(chat_id=-6, roles=['FUQARO'] * 30)
        migration.update_all_group_orders(apps, SimpleNamespace(connection=connection))
        timestamps = {}
        for row in ChatRoleOrder.objects.all():
            self.assertEqual(row.roles[18], 'FITNACHI')
            self.assertEqual(row.roles.count('FITNACHI'), 1)
            self.assertEqual(len(row.roles), 60)
            timestamps[row.pk] = row.updated_at
        migration.update_all_group_orders(apps, SimpleNamespace(connection=connection))
        self.assertEqual(dict(ChatRoleOrder.objects.values_list('pk', 'updated_at')), timestamps)
