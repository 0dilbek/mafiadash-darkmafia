from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import connection
from django.test import Client, TransactionTestCase
from django.urls import reverse
from django.utils import timezone

from .cinema_models import (
    CinemaChannel, CinemaJoinRequest, CinemaMovie, CinemaPlan, CinemaPurchase, CinemaSubscription,
)
from .models import Profile, User


class CinemaDashboardTests(TransactionTestCase):
    shared_models = [User, Profile, CinemaMovie, CinemaChannel, CinemaJoinRequest,
                     CinemaPlan, CinemaSubscription, CinemaPurchase]

    def setUp(self):
        # managed=False mirrors the bot's tables; Django migrations don't create them.
        with connection.schema_editor() as editor:
            for model in self.shared_models:
                editor.create_model(model)
        self.admin = get_user_model().objects.create_user(username="cinemaadmin", password="test", is_staff=True)
        self.client.force_login(self.admin)
        self.plan = CinemaPlan.objects.create(pk=1, price_diamonds=100, duration_days=30)

    def tearDown(self):
        with connection.schema_editor() as editor:
            for model in reversed(self.shared_models):
                editor.delete_model(model)

    def test_anonymous_and_nonstaff_cannot_read_or_change_plan(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse("cinema")).status_code, 302)
        normal = get_user_model().objects.create_user(username="normal", password="test")
        self.client.force_login(normal)
        self.assertEqual(self.client.get(reverse("cinema")).status_code, 403)
        self.assertEqual(self.client.post(reverse("cinema"), {"price_diamonds": 1, "duration_days": 1}).status_code, 403)
        self.plan.refresh_from_db()
        self.assertEqual(self.plan.price_diamonds, 100)

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

    def test_movie_normalization_edit_and_delete_confirmation(self):
        response = self.client.post(reverse("cinema_movie_add"), {"code": " Kino_42 ", "file_id": "file", "message_text": "Kino"})
        self.assertEqual(response.status_code, 302)
        movie = CinemaMovie.objects.get(code="kino_42")
        CinemaMovie.objects.filter(pk=movie.pk).update(request_count=8)
        response = self.client.post(reverse("cinema_movie_edit", args=[movie.pk]), {"code": "NEW", "file_id": "newfile", "message_text": "New"})
        self.assertEqual(response.status_code, 302)
        movie.refresh_from_db()
        self.assertEqual((movie.code, movie.request_count), ("new", 8))
        delete_url = reverse("cinema_movie_delete", args=[movie.pk])
        self.assertEqual(self.client.get(delete_url).status_code, 200)
        self.assertTrue(CinemaMovie.objects.filter(pk=movie.pk).exists())
        self.assertEqual(self.client.post(delete_url).status_code, 302)
        self.assertFalse(CinemaMovie.objects.filter(pk=movie.pk).exists())

    def test_duplicate_movie_code_rejected_and_csrf_required(self):
        CinemaMovie.objects.create(code="42", file_id="file")
        response = self.client.post(reverse("cinema_movie_add"), {"code": "42", "file_id": "other"})
        self.assertEqual(response.status_code, 400)
        strict = Client(enforce_csrf_checks=True)
        strict.force_login(self.admin)
        self.assertEqual(strict.post(reverse("cinema"), {"price_diamonds": 1, "duration_days": 1}).status_code, 403)

    def test_missing_schema_gives_actionable_page(self):
        from django.db import OperationalError
        with patch.object(CinemaPlan.objects, "get_or_create", side_effect=OperationalError("missing table")):
            response = self.client.get(reverse("cinema"))
        self.assertContains(response, "migratsiyalarini tekshiring", status_code=503)
