"""Django mappings of Dark Cinema's Tortoise models, sharing the same database.

Schema owner: dark cinema bot/app/models and migrations/001..003.
Keep field names, types and db_table in sync; Django must not create these tables.
"""
import uuid

from django.db import models


class CinemaMovie(models.Model):
    id = models.BigAutoField(primary_key=True)
    code = models.CharField(max_length=64, unique=True)
    file_id = models.CharField(max_length=512)
    message_text = models.TextField(default="", blank=True)
    request_count = models.BigIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = "cinema_movie"
        ordering = ["-created_at"]


class CinemaChannel(models.Model):
    id = models.BigAutoField(primary_key=True)
    chat_id = models.BigIntegerField(unique=True)
    title = models.CharField(max_length=255)
    invite_link = models.CharField(max_length=512)
    accepts_join_requests = models.BooleanField(default=False)

    class Meta:
        managed = False
        db_table = "cinema_subscription_channel"
        ordering = ["id"]


class CinemaJoinRequest(models.Model):
    id = models.BigAutoField(primary_key=True)
    channel = models.ForeignKey(CinemaChannel, related_name="join_requests", on_delete=models.CASCADE)
    user_id = models.BigIntegerField()
    requested_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "cinema_subscription_join_request"
        unique_together = (("channel", "user_id"),)


class CinemaPlan(models.Model):
    id = models.IntegerField(primary_key=True, default=1)
    price_diamonds = models.BigIntegerField(default=100)
    duration_days = models.IntegerField(default=30)
    is_enabled = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = "cinema_plan"


class CinemaSubscription(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.OneToOneField("bot.User", related_name="cinema_subscription", on_delete=models.CASCADE)
    expires_at = models.DateTimeField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = "cinema_subscription"


class CinemaPurchase(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey("bot.User", related_name="cinema_purchases", on_delete=models.CASCADE)
    price_diamonds = models.BigIntegerField()
    duration_days = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    valid_until = models.DateTimeField()
    paid_at = models.DateTimeField(null=True, blank=True)
    subscription_expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = "cinema_purchase"
        ordering = ["-created_at"]
