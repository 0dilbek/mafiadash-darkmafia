from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import connection
from django.test import Client, TransactionTestCase
from django.urls import reverse
from django.utils import timezone

from .cinema_models import (
    CinemaChannel, CinemaJoinRequest, CinemaMovie, CinemaPlan, CinemaPurchase, CinemaSubscription, CinemaViewer,
)
from .models import Profile, User


class CinemaDashboardTests(TransactionTestCase):
    shared_models = [User, Profile, CinemaMovie, CinemaChannel, CinemaJoinRequest,
                     CinemaPlan, CinemaSubscription, CinemaPurchase, CinemaViewer]

    def setUp(self):
        # managed=False mirrors the bot's tables; Django migrations don't create them.
        with connection.schema_editor() as editor:
            for model in self.shared_models:
                editor.create_model(model)
        self.admin = get_user_model().objects.create_user(username="cinemaadmin", password="test", is_staff=False, is_superuser=False)
        self.client.force_login(self.admin)
        self.plan = CinemaPlan.objects.create(pk=1, price_diamonds=100, duration_days=30)

    def tearDown(self):
        with connection.schema_editor() as editor:
            for model in reversed(self.shared_models):
                editor.delete_model(model)

    def test_anonymous_and_telegram_only_sessions_cannot_access_cinema(self):
        self.client.logout()
        movie = CinemaMovie.objects.create(code="42", file_id="file")
        urls = [reverse("cinema")]
        for telegram_session in (False, True):
            if telegram_session:
                session = self.client.session
                session["tg_authenticated"] = True
                session.save()
            for url in urls:
                for method in (self.client.get, self.client.post):
                    with self.subTest(url=url, method=method.__name__, telegram_session=telegram_session):
                        response = method(url)
                        self.assertEqual(response.status_code, 302)
                        self.assertIn("/panel/login/", response.url)
        self.plan.refresh_from_db()
        self.assertEqual(self.plan.price_diamonds, 100)
        self.assertTrue(CinemaMovie.objects.filter(pk=movie.pk).exists())

    def test_dashboard_account_without_staff_flag_sees_menu_and_can_open_it(self):
        self.assertFalse(self.admin.is_staff)
        self.assertFalse(self.admin.is_superuser)
        response = self.client.get(reverse("cinema"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'href="' + reverse("cinema") + '" class="nav-link active"')
        self.assertContains(response, 'bi bi-film')

    def test_settings_save_to_shared_table_and_keep_active_subscriptions(self):
        user = User.objects.create(user_id=777, full_name="Viewer", mention="Viewer")
        expiry = timezone.now() + timedelta(days=10)
        subscription = CinemaSubscription.objects.create(user=user, expires_at=expiry)
        response = self.client.post(reverse("cinema"), {"price_diamonds": "25", "duration_days": "7", "is_enabled": "on"})
        self.assertEqual(response.status_code, 302)
        self.plan.refresh_from_db()
        self.assertEqual((self.plan.price_diamonds, self.plan.duration_days, self.plan.is_enabled), (25, 7, True))
        subscription.refresh_from_db()
        self.assertEqual(subscription.expires_at, expiry)

    def test_invalid_settings_do_not_partially_save(self):
        for field, value in [("price_diamonds", "-1"), ("price_diamonds", "0"),
                             ("price_diamonds", "1.2"), ("price_diamonds", str(10**12 + 1)),
                             ("duration_days", "0"), ("duration_days", "3651")]:
            with self.subTest(field=field, value=value):
                payload = {"price_diamonds": "20", "duration_days": "7", "is_enabled": "on", field: value}
                response = self.client.post(reverse("cinema"), payload)
                self.assertEqual(response.status_code, 400)
                self.plan.refresh_from_db()
                self.assertEqual((self.plan.price_diamonds, self.plan.duration_days), (100, 30))
                self.assertEqual(response.context['plan'].price_diamonds, 100)

    def test_all_tabs_render_shared_records_and_ignore_unpaid_offers_in_revenue(self):
        user = User.objects.create(user_id=777, full_name="Viewer", mention="Viewer")
        Profile.objects.create(user=user, diamond=123)
        CinemaMovie.objects.create(code="test42", file_id="file")
        channel = CinemaChannel.objects.create(chat_id=-100123, title="Channel", invite_link="https://t.me/test", accepts_join_requests=True)
        CinemaJoinRequest.objects.create(channel=channel, user_id=777, requested_at=timezone.now())
        CinemaSubscription.objects.create(user=user, expires_at=timezone.now() + timedelta(days=5))
        for paid_at in [timezone.now(), None]:
            CinemaPurchase.objects.create(user=user, price_diamonds=100, duration_days=30,
                                          valid_until=timezone.now(), paid_at=paid_at)
        for tab in ["settings", "movies", "channels", "subscriptions", "purchases"]:
            with self.subTest(tab=tab):
                response = self.client.get(reverse("cinema"), {"tab": tab})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.context["revenue"], 100)
                self.assertEqual(response.context["active_count"], 1)
                if tab == "subscriptions":
                    self.assertContains(response, "123 💎")
                    self.assertContains(response, reverse("user_detail", args=[user.id]))

    def test_movies_are_read_only_and_old_mutation_urls_are_gone(self):
        movie = CinemaMovie.objects.create(code="42", file_id="file", request_count=8)
        response = self.client.get(reverse("cinema"), {"tab": "movies"})
        self.assertContains(response, "42")
        for forbidden in ("Kino qo'shish", "Tahrirlash", "O'chirish", "/movies/add/"):
            self.assertNotContains(response, forbidden)
        for path in ("/panel/cinema/movies/add/", f"/panel/cinema/movies/{movie.pk}/",
                     f"/panel/cinema/movies/{movie.pk}/delete/"):
            for method in (self.client.get, self.client.post):
                self.assertEqual(method(path).status_code, 404)
        movie.refresh_from_db()
        self.assertEqual((movie.code, movie.request_count), ("42", 8))

    def test_settings_still_require_csrf(self):
        strict = Client(enforce_csrf_checks=True)
        strict.force_login(self.admin)
        self.assertEqual(strict.post(reverse("cinema"), {"price_diamonds": 1, "duration_days": 1}).status_code, 403)

    def test_audience_includes_free_and_legacy_visitors_without_mafia_only_users(self):
        regular = User.objects.create(user_id=1001, full_name="Regular", mention="Regular")
        CinemaViewer.objects.create(user=regular, last_seen_at=timezone.now())
        legacy = User.objects.create(user_id=1002, full_name="Legacy", mention="Legacy")
        # Even an unpaid offer proves Cinema usage, but is not a premium subscription.
        CinemaPurchase.objects.create(user=legacy, price_diamonds=100, duration_days=30, valid_until=timezone.now())
        paid = User.objects.create(user_id=1003, full_name="Paid", mention="Paid")
        CinemaViewer.objects.create(user=paid, last_seen_at=timezone.now())
        CinemaSubscription.objects.create(user=paid, expires_at=timezone.now() + timedelta(days=2))
        User.objects.create(user_id=1004, full_name="Mafia only", mention="Mafia")
        response = self.client.get(reverse("cinema"))
        self.assertEqual(response.context["viewer_count"], 3)
        self.assertEqual(response.context["active_count"], 1)
        self.assertEqual(response.context["page_obj"].paginator.count, 3)
        self.assertContains(response, "Regular")
        self.assertContains(response, "Legacy")
        self.assertNotContains(response, "Mafia only")
        self.assertEqual(next(row.balance for row in response.context["rows"] if row.pk == regular.pk), 0)
        premium = self.client.get(reverse("cinema"), {"access": "premium"})
        self.assertEqual([row.pk for row in premium.context["rows"]], [paid.pk])
        standard = self.client.get(reverse("cinema"), {"access": "standard", "q": "1001"})
        self.assertEqual([row.pk for row in standard.context["rows"]], [regular.pk])
        self.assertEqual(standard.context["viewer_count"], 3)

    def test_expired_subscriptions_are_in_total_but_not_active_count(self):
        user = User.objects.create(user_id=998, mention="Expired")
        CinemaSubscription.objects.create(user=user, expires_at=timezone.now() - timedelta(seconds=1))
        response = self.client.get(reverse("cinema"), {"access": "standard"})
        self.assertEqual(response.context["viewer_count"], 1)
        self.assertEqual(response.context["active_count"], 0)
        self.assertEqual(response.context["page_obj"].paginator.count, 1)

    def test_missing_viewer_migration_shows_legacy_data_and_notice(self):
        user = User.objects.create(user_id=999, full_name="Legacy", mention="Legacy")
        CinemaSubscription.objects.create(user=user, expires_at=timezone.now() + timedelta(days=1))
        with connection.schema_editor() as editor:
            editor.delete_model(CinemaViewer)
        try:
            response = self.client.get(reverse("cinema"))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.context["viewer_count"], 1)
            self.assertContains(response, "Foydalanuvchilar hisobi hali yoqilmagan")
            self.assertContains(response, "Legacy")
        finally:
            with connection.schema_editor() as editor:
                editor.create_model(CinemaViewer)

    def test_missing_schema_gives_actionable_page(self):
        from django.db import OperationalError
        with patch.object(CinemaPlan.objects, "get_or_create", side_effect=OperationalError("missing table")):
            response = self.client.get(reverse("cinema"))
        self.assertContains(response, "migratsiyalarini tekshiring", status_code=503)
