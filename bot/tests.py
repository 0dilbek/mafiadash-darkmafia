import json
from types import SimpleNamespace
from unittest.mock import patch

from django.db import DatabaseError
from django.test import RequestFactory, SimpleTestCase

from . import views


class LargeGameSettingsTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_default_role_order_has_60_balanced_prefixes(self):
        self.assertEqual(len(views.DEFAULT_ROLE_ORDER), 60)
        self.assertEqual(views._validate_role_order(views.DEFAULT_ROLE_ORDER), [])

    def test_old_30_role_order_is_extended_without_changing_prefix(self):
        old_roles = list(views.DEFAULT_ROLE_ORDER[:30])

        normalized = views._normalize_role_order(old_roles)

        self.assertEqual(len(normalized), 60)
        self.assertEqual(normalized[:30], old_roles)
        self.assertEqual(normalized[30:], views.DEFAULT_ROLE_ORDER[30:])

    def test_invalid_role_order_is_reset_to_default(self):
        normalized = views._normalize_role_order(['NOT_A_ROLE'])

        self.assertEqual(normalized, views.DEFAULT_ROLE_ORDER)
        self.assertIsNot(normalized, views.DEFAULT_ROLE_ORDER)

    def test_max_player_options_keep_30_and_allow_60(self):
        self.assertEqual(
            views.MAX_PLAYER_OPTIONS,
            (10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60),
        )

    def test_max_player_read_failure_falls_back_to_30(self):
        with patch.object(
            views.GroupMoreSet.objects,
            'filter',
            side_effect=DatabaseError('table unavailable'),
        ):
            result = views._get_group_max_players(-1001)

        self.assertEqual(result, 30)

    def test_max_player_endpoint_rejects_unlisted_value(self):
        request = self.factory.post(
            '/group/max-players/',
            data=json.dumps({'max_players': 65}),
            content_type='application/json',
        )
        request.session = {'tg_authenticated': True, 'tg_chat_id': -1001}

        response = views.group_max_players(request)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.content)['error'], 'invalid_max_players')

    def test_max_player_endpoint_saves_valid_value(self):
        request = self.factory.post(
            '/group/max-players/',
            data=json.dumps({'max_players': 60}),
            content_type='application/json',
        )
        request.session = {'tg_authenticated': True, 'tg_chat_id': -1001}
        with patch.object(
            views.GroupMoreSet.objects,
            'update_or_create',
            return_value=(SimpleNamespace(max_players=60), False),
        ) as update_or_create:
            response = views.group_max_players(request)

        self.assertEqual(response.status_code, 200)
        update_or_create.assert_called_once_with(
            chat_id=-1001,
            defaults={'max_players': 60},
        )

    def test_max_player_endpoint_returns_503_on_database_failure(self):
        request = self.factory.post(
            '/group/max-players/',
            data=json.dumps({'max_players': 60}),
            content_type='application/json',
        )
        request.session = {'tg_authenticated': True, 'tg_chat_id': -1001}

        with patch.object(
            views.GroupMoreSet.objects,
            'update_or_create',
            side_effect=DatabaseError('table unavailable'),
        ):
            response = views.group_max_players(request)

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            json.loads(response.content)['error'],
            'settings_storage_unavailable',
        )
