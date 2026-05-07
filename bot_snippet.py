"""
Bot tomoni (Tortoise ORM) uchun Magic Link snippet.
Bu kodni o'zingizning aiogram botingizga qo'shing.

Zarur o'rnatmalar (.env yoki config):
    ADMIN_IDS = [123456789, 987654321]   # ruxsat berilgan admin Telegram IDlari
    DASHBOARD_URL = https://domain.uz    # veb-panel manzili
"""
import uuid
import os
from datetime import datetime, timezone, timedelta

from aiogram import Router, types
from aiogram.filters import Command
from tortoise import fields
from tortoise.models import Model

# ── Tortoise modeli (Django ning admin_login_tokens jadvalidek bir xil) ────────

class AdminLoginToken(Model):
    id = fields.BigIntField(pk=True)
    user_id = fields.BigIntField()
    token = fields.UUIDField(default=uuid.uuid4)
    created_at = fields.DatetimeField(auto_now_add=True)
    expires_at = fields.DatetimeField()

    class Meta:
        table = "admin_login_tokens"

    @classmethod
    async def create_for_user(cls, telegram_user_id: int, days: int = 1):
        # Avvalgi eskirgan tokenlarni tozalaymiz
        now = datetime.now(timezone.utc)
        await cls.filter(user_id=telegram_user_id, expires_at__lt=now).delete()

        return await cls.create(
            user_id=telegram_user_id,
            expires_at=now + timedelta(days=days),
        )


# ── Config ─────────────────────────────────────────────────────────────────────

ADMIN_IDS: list[int] = [
    int(x.strip())
    for x in os.environ.get("ADMIN_TELEGRAM_IDS", "").split(",")
    if x.strip().isdigit()
]
DASHBOARD_URL: str = os.environ.get("DASHBOARD_URL", "https://domain.uz")


# ── Handler ────────────────────────────────────────────────────────────────────

router = Router()


@router.message(Command("dashboard"))
async def dashboard_command(message: types.Message):
    user_id = message.from_user.id

    if user_id not in ADMIN_IDS:
        await message.answer("❌ Siz admin emassiz.")
        return

    token_obj = await AdminLoginToken.create_for_user(user_id)
    link = f"{DASHBOARD_URL}/auth/login/?token={token_obj.token}"

    text = (
        "🔐 <b>MafiaDash kirish havolasi</b>\n\n"
        f'<a href="{link}">👉 Dashboard ga kirish</a>\n\n'
        "⚠️ <i>Havola 24 soat amal qiladi va faqat bir marta ishlatiladi.</i>\n"
        "🔒 Havolani hech kim bilan ulashmang!"
    )

    await message.answer(
        text,
        parse_mode="HTML",
        disable_web_page_preview=True,
    )
