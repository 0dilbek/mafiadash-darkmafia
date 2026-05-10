"""
Bot tomoni uchun MafiaDash panel link snippet.
Bu kodni o'zingizning aiogram botingizga qo'shing.

Zarur .env o'zgaruvchilari:
    PANEL_API_URL=http://77.42.67.218/api/generate-link/
    ADMIN_TELEGRAM_IDS=123456789,987654321

Ishlash tartibi:
    Bot → GET /api/generate-link/?chat_id=... → Django token yaratadi → URL qaytaradi → Bot tugma ko'rsatadi

Rol tartibi haqida:
    chat_role_order jadvalidagi roles maydoni RoleNames qiymatlarini saqlaydi.
    Masalan: ["🤵🏻 Don", "🕵🏼 Komissar katani", "👨🏼 Tinch axoli", ...]
    Bot rol taqsimlashda shu jadvaldan o'qiydi, yo'q bo'lsa DEFAULT_ROLE_ORDER ishlatadi.
"""
import os
import logging

import aiohttp
from aiogram import Router, types
from aiogram.filters import Command

logger = logging.getLogger(__name__)


# ── Config ─────────────────────────────────────────────────────────────────────

ADMIN_IDS: list[int] = [
    int(x.strip())
    for x in os.environ.get("ADMIN_TELEGRAM_IDS", "").split(",")
    if x.strip().isdigit()
]
PANEL_API_URL: str = os.environ.get("PANEL_API_URL", "")
BOT_API_SECRET: str = os.environ.get("BOT_API_SECRET", "")


# ── Panel URL olish ─────────────────────────────────────────────────────────────

async def fetch_panel_url(chat_id: int) -> str | None:
    """
    Django dan magic-link URL so'raydi (GET).
    Xato bo'lsa yoki sozlanmagan bo'lsa — None qaytaradi.
    """
    if not PANEL_API_URL:
        return None

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                PANEL_API_URL,
                params={"chat_id": chat_id},
                timeout=aiohttp.ClientTimeout(total=5),
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("url")
    except Exception as e:
        logger.warning("fetch_panel_url xatosi: %s", e)

    return None


# ── Handler ────────────────────────────────────────────────────────────────────

router = Router()


@router.message(Command("dashboard"))
async def dashboard_command(message: types.Message):
    user_id = message.from_user.id

    if user_id not in ADMIN_IDS:
        await message.answer("❌ Siz admin emassiz.")
        return

    is_group = message.chat.type in ("group", "supergroup")
    chat_id = message.chat.id if is_group else None

    if not PANEL_API_URL:
        await message.answer("⚙️ Panel hali sozlanmagan.")
        return

    if not is_group:
        await message.answer("ℹ️ Bu buyruqni guruh ichida yuboring.")
        return

    url = await fetch_panel_url(chat_id=chat_id, user_id=user_id)
    if not url:
        await message.answer("❌ Panel bilan bog'lanishda xato. Keyinroq urinib ko'ring.")
        return

    group_name = message.chat.title or "guruh"
    text = (
        f"🔐 <b>MafiaDash — {group_name}</b>\n\n"
        f'<a href="{url}">👉 Guruh panelini ochish</a>\n\n'
        "⚠️ <i>Havola 24 soat amal qiladi va faqat bir marta ishlatiladi.</i>\n"
        "🔒 Havolani hech kim bilan ulashmang!"
    )

    await message.answer(
        text,
        parse_mode="HTML",
        disable_web_page_preview=True,
    )
