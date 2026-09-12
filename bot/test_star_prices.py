from types import SimpleNamespace
from unittest.mock import patch

from django.db import connection
from django.test import RequestFactory, TransactionTestCase

from .diamond_prices import PRICE_DEFINITIONS, ensure_default_prices, group_price_definitions, parse_price_updates
from .models import DiamondPriceSetting
from .views import diamond_price_settings


class StarPriceSettingsTests(TransactionTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # This table is managed by the bot in production.
        with connection.schema_editor() as editor:
            editor.create_model(DiamondPriceSetting)

    @classmethod
    def tearDownClass(cls):
        with connection.schema_editor() as editor:
            editor.delete_model(DiamondPriceSetting)
        super().tearDownClass()

    def setUp(self):
        DiamondPriceSetting.objects.all().delete()
        self.payload = {f"price_{item['key']}": str(item['default']) for item in PRICE_DEFINITIONS}

    def post(self):
        request = RequestFactory().post('/panel/diamond-prices/', self.payload)
        request.user = SimpleNamespace(is_authenticated=True)
        with patch('bot.views.messages.success'), patch('bot.views.messages.error'):
            return diamond_price_settings(request)

    def test_admin_saves_both_amounts_to_shared_table(self):
        self.payload['price_star_pack_50'] = '123'
        self.payload['price_star_pack_50_diamonds'] = '75'
        self.assertEqual(self.post().status_code, 302)
        ensure_default_prices(DiamondPriceSetting)
        values = dict(DiamondPriceSetting.objects.values_list('key', 'amount'))
        self.assertEqual(values['star_pack_50'], 123)
        self.assertEqual(values['star_pack_50_diamonds'], 75)
        group = next(g for g in group_price_definitions(values) if g['name'] == 'Telegram Stars')
        self.assertEqual(len(group['items']), 5)
        self.assertEqual(group['items'][0]['diamonds'], 75)
        self.assertEqual(group['items'][0]['amount'], 123)
        self.assertEqual(group['items'][0]['label'], 'Paket 1')

    def test_invalid_diamonds_prevent_partial_price_save(self):
        ensure_default_prices(DiamondPriceSetting)
        self.payload['price_star_pack_50'] = '123'
        self.payload['price_star_pack_50_diamonds'] = '0'
        response = self.post()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(DiamondPriceSetting.objects.get(key='star_pack_50').amount, 250)
        self.assertContains(response, 'name="price_star_pack_50_diamonds"', status_code=400)
        self.assertContains(response, 'name="price_star_pack_50"', status_code=400)

    def test_both_star_fields_require_positive_integers(self):
        for key in ('star_pack_50', 'star_pack_50_diamonds'):
            for invalid in ('0', '-1', '1.5', '', str(2**63)):
                with self.subTest(key=key, invalid=invalid):
                    payload = dict(self.payload, **{f'price_{key}': invalid})
                    _, errors = parse_price_updates(payload)
                    self.assertIn(key, errors)
