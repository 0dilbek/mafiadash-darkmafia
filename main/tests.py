from django.test import SimpleTestCase

from .views import _game_mode_context, _normalize_game_team


class GameStatsModeContextTests(SimpleTestCase):
    def test_teamgame_uses_winning_color_and_team_count(self):
        context = _game_mode_context(
            'classic:vsgame3',
            [
                {'game_team': 'red'},
                {'game_team': 'red'},
                {'game_team': 'blue'},
            ],
        )

        self.assertTrue(context['is_team_game'])
        self.assertEqual(context['result_variant'], 'teamgame')
        self.assertEqual(context['winning_team_color'], 'red')
        self.assertEqual(context['winning_team_label'], 'Qizil')
        self.assertEqual(context['mode_label'], 'Teamgame · 3 jamoa')

    def test_para_uses_single_para_result_variant(self):
        context = _game_mode_context('para x classic', [])

        self.assertTrue(context['is_para_game'])
        self.assertEqual(context['result_variant'], 'para')
        self.assertEqual(context['mode_label'], 'Para · Classic')

    def test_only_supported_team_colors_are_exposed_to_css(self):
        self.assertEqual(_normalize_game_team(' PURPLE '), 'purple')
        self.assertEqual(_normalize_game_team('not-a-color'), '')
