import importlib
import json
from types import SimpleNamespace
from unittest.mock import patch

from django.apps import apps
from django.db import connection
from django.test import RequestFactory, TestCase

from . import views
from .models import ChatRoleOrder

migration = importlib.import_module('bot.migrations.0005_fitnachi_role_order')


class RoleOrderMigrationTests(TestCase):
    def test_upgrades_old_30_and_60_defaults_once(self):
        for count in (30, 60):
            for fifth in ('KOLDUN', 'FUQARO'):
                roles = list(migration.LEGACY_ORDER[:count])
                roles[4] = fifth
                row = ChatRoleOrder.objects.create(chat_id=ChatRoleOrder.objects.count() + 1, roles=roles)
                migration.add_fitnachi_to_legacy_defaults(apps, SimpleNamespace(connection=connection))
                row.refresh_from_db()
                expected = list(roles)
                expected[18] = 'FITNACHI'
                self.assertEqual(row.roles, expected)
                timestamp = row.updated_at
                migration.add_fitnachi_to_legacy_defaults(apps, SimpleNamespace(connection=connection))
                row.refresh_from_db()
                self.assertEqual(row.updated_at, timestamp)

    def test_preserves_custom_order_and_existing_fitnachi_position(self):
        custom = list(migration.LEGACY_ORDER)
        custom[3], custom[5] = custom[5], custom[3]
        updated = list(views.DEFAULT_ROLE_ORDER)
        updated[4], updated[18] = updated[18], updated[4]
        for i, roles in enumerate((custom, updated), 1):
            row = ChatRoleOrder.objects.create(chat_id=i, roles=roles)
            migration.add_fitnachi_to_legacy_defaults(apps, SimpleNamespace(connection=connection))
            row.refresh_from_db()
            self.assertEqual(row.roles, roles)


class RoleOrderViewTests(TestCase):
    def request(self, roles=None):
        factory = RequestFactory()
        request = factory.get('/group/roles/') if roles is None else factory.post(
            '/group/roles/', json.dumps({'roles': roles}), content_type='application/json')
        request.session = {'tg_authenticated': True, 'tg_chat_id': -1001}
        return request

    def render_view(self, request):
        with patch.object(views.Chat.objects, 'filter') as query:
            query.return_value.first.return_value = SimpleNamespace(title='Test group')
            return views.group_role_order(request)

    def test_custom_order_without_fitnachi_offers_role_selector(self):
        ChatRoleOrder.objects.create(chat_id=-1001, roles=list(migration.LEGACY_ORDER))
        response = self.render_view(self.request())
        html = response.content.decode().split('<script')[0]
        self.assertEqual(html.count('class="role-label role-select"'), 60)
        self.assertContains(response, '<option value="FITNACHI">', count=60)
        self.assertContains(response, '19 kishidan boshlab chiqadi')

    def test_saves_fitnachi_in_an_earlier_position(self):
        roles = list(views.DEFAULT_ROLE_ORDER)
        roles[4], roles[18] = roles[18], roles[4]
        response = self.render_view(self.request(roles))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(json.loads(response.content)['ok'])
        self.assertEqual(ChatRoleOrder.objects.get(chat_id=-1001).roles, roles)

    def test_duplicate_fitnachi_does_not_overwrite_saved_order(self):
        roles = list(views.DEFAULT_ROLE_ORDER)
        roles[4] = 'FITNACHI'
        response = self.render_view(self.request(roles))
        self.assertEqual(response.status_code, 422)
        self.assertIn('Fitnachi', json.loads(response.content)['errors'][0])
        self.assertEqual(ChatRoleOrder.objects.get(chat_id=-1001).roles, views.DEFAULT_ROLE_ORDER)
