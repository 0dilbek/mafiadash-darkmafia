from django.test import SimpleTestCase
from . import views
from .diamond_prices import PRICE_DEFINITIONS_BY_KEY
from main.views import _role_meta


class FitnachiPanelTests(SimpleTestCase):
    def test_role_can_be_configured_and_has_correct_default_price(self):
        self.assertEqual(views.RoleNames.FITNACHI, '😈 Fitnachi')
        self.assertEqual(views.ROLE_TEAMS['FITNACHI'], 'yakka')
        self.assertEqual(views.DEFAULT_ROLE_ORDER.count('FITNACHI'), 1)
        self.assertEqual(views._validate_role_order(views.DEFAULT_ROLE_ORDER), [])
        self.assertEqual(views._normalize_role_order(views.DEFAULT_ROLE_ORDER), views.DEFAULT_ROLE_ORDER)
        price = PRICE_DEFINITIONS_BY_KEY['active_role_fitnachi']
        self.assertEqual((price['currency'], price['default']), ('diamond', 3))

    def test_statistics_recognize_canonical_and_key_names(self):
        for name in ('FITNACHI', '😈 Fitnachi'):
            meta = _role_meta(name)
            self.assertEqual(meta['team'], 'neutral')
            self.assertEqual(meta['label'], 'Fitnachi')
