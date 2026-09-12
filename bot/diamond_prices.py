def _price(key, label, category, currency, default):
    currency_labels = {
        "diamond": "💎 Olmos",
        "dollar": "💵 Dollar",
        "uzs": "so'm",
        "stars": "⭐ Stars",
    }
    return {
        "key": key,
        "label": label,
        "category": category,
        "currency": currency,
        "currency_label": currency_labels[currency],
        "default": default,
    }


PRICE_DEFINITIONS = (
    _price("transfer_dollar_commission", "Dollar transfer komissiyasi", "Asosiy", "dollar", 100),
    _price("transfer_diamond_commission", "Olmos transfer komissiyasi", "Asosiy", "diamond", 1),
    _price("transfer_diamond_giveaway_commission", "Olmos giveaway komissiyasi", "Asosiy", "diamond", 0),
    _price("profile_transfer", "Profilni ko'chirish", "Asosiy", "diamond", 5),
    _price("active_role_delete", "Faol rolni o'chirish", "Asosiy", "dollar", 64),

    _price("shop_himoya", "Himoya", "Do'kon", "dollar", 200),
    _price("shop_hujjat", "Hujjat", "Do'kon", "dollar", 190),
    _price("shop_verbana", "Verbana", "Do'kon", "diamond", 1),
    _price("shop_dori_himoya", "Doridan himoya", "Do'kon", "dollar", 100),
    _price("shop_maska", "Maska", "Do'kon", "dollar", 100),
    _price("shop_miltiq", "Miltiq", "Do'kon", "diamond", 1),
    _price("shop_osish_himoya", "Osishdan himoya", "Do'kon", "diamond", 1),
    _price("shop_qotil_himoya", "Qotildan himoya", "Do'kon", "diamond", 2),
    _price("shop_geroy", "Geroy", "Do'kon", "diamond", 90),
    _price("shop_geroy_himoya", "Geroydan himoya", "Do'kon", "diamond", 7),
    _price("shop_slip_himoya", "Sirpanishdan himoya", "Do'kon", "dollar", 1000),

    _price("diamond_pack_5", "5 olmos", "Karta paketlari", "uzs", 6_000),
    _price("diamond_pack_10", "10 olmos", "Karta paketlari", "uzs", 12_000),
    _price("diamond_pack_30", "30 olmos", "Karta paketlari", "uzs", 35_000),
    _price("diamond_pack_50", "50 olmos", "Karta paketlari", "uzs", 55_000),
    _price("diamond_pack_100", "100 olmos", "Karta paketlari", "uzs", 105_000),
    _price("diamond_pack_250", "250 olmos", "Karta paketlari", "uzs", 260_000),
    _price("diamond_pack_1000", "1000 olmos", "Karta paketlari", "uzs", 1_000_000),

    _price("star_pack_50", "50 olmos", "Telegram Stars", "stars", 250),
    _price("star_pack_100", "100 olmos", "Telegram Stars", "stars", 500),
    _price("star_pack_200", "200 olmos", "Telegram Stars", "stars", 1000),
    _price("star_pack_500", "500 olmos", "Telegram Stars", "stars", 2500),
    _price("star_pack_1000", "1000 olmos", "Telegram Stars", "stars", 5000),

    _price("dollar_pack_250", "250 dollar", "Dollar ayirboshlash", "diamond", 1),
    _price("dollar_pack_500", "500 dollar", "Dollar ayirboshlash", "diamond", 2),
    _price("dollar_pack_750", "750 dollar", "Dollar ayirboshlash", "diamond", 3),
    _price("dollar_pack_1000", "1000 dollar", "Dollar ayirboshlash", "diamond", 4),
    _price("dollar_pack_5000", "5000 dollar", "Dollar ayirboshlash", "diamond", 18),
    _price("dollar_pack_10000", "10000 dollar", "Dollar ayirboshlash", "diamond", 30),

    _price("active_role_minior", "☠️  Minior", "Faol rollar", "diamond", 6),
    _price("active_role_joker", "🤡 Joker", "Faol rollar", "diamond", 6),
    _price("active_role_kimyogar", "👨‍🔬 Kimyogar", "Faol rollar", "diamond", 6),
    _price("active_role_ovchi", "🥷 Убийца", "Faol rollar", "diamond", 5),
    _price("active_role_vampir", "🧛🏻 Vampir", "Faol rollar", "diamond", 5),
    _price("active_role_janob", "🎖 Janob", "Faol rollar", "diamond", 3),
    _price("active_role_sehrgar", "🧙 Sehrgar", "Faol rollar", "diamond", 3),
    _price("active_role_komissar", "🕵🏼 Komissar katani", "Faol rollar", "diamond", 2),
    _price("active_role_don", "🤵🏻 Don", "Faol rollar", "diamond", 2),
    _price("active_role_qotil", "🔪 Qotil", "Faol rollar", "diamond", 2),
    _price("active_role_koldun", "⚡️ Koldun", "Faol rollar", "diamond", 2),
    _price("active_role_gazabdor", "🧌 G'azabkor", "Faol rollar", "diamond", 1),
    _price("active_role_mafia", "🤵🏼 Mafia", "Faol rollar", "diamond", 1),
    _price("active_role_serjant", "👮🏼 Serjant", "Faol rollar", "diamond", 1),
    _price("active_role_aferist", "🤹🏻 Aferist", "Faol rollar", "diamond", 1),
    _price("active_role_doktor", "👨🏼‍⚕️️ Doktor", "Faol rollar", "dollar", 600),
    _price("active_role_kezuvchi", "💊 Anistizolog", "Faol rollar", "dollar", 500),
    _price("active_role_jurnalist", "👩🏼‍💻 Jurnalist", "Faol rollar", "dollar", 500),
    _price("active_role_advokat", "👨🏼‍💼 Advokat", "Faol rollar", "dollar", 500),
    _price("active_role_afsungar", "💣 Afsungar", "Faol rollar", "dollar", 500),
    _price("active_role_bori", "🦎Buqalamun", "Faol rollar", "dollar", 500),
    _price("active_role_daydi", "🧙‍♂️ Daydi", "Faol rollar", "dollar", 400),
    _price("active_role_suidsid", "🤦🏼 Suidsid", "Faol rollar", "dollar", 300),
    _price("active_role_fuqaro", "👨🏼 Tinch axoli", "Faol rollar", "dollar", 100),
)

STAR_PACK_KEYS = {count: f"star_pack_{count}" for count in (50, 100, 200, 500, 1000)}
PRICE_DEFINITIONS += tuple(
    _price(f"{key}_diamonds", f"Stars paket {index}: olmos", "Telegram Stars", "diamond", count)
    for index, (count, key) in enumerate(STAR_PACK_KEYS.items(), start=1)
)

PRICE_DEFINITIONS_BY_KEY = {item["key"]: item for item in PRICE_DEFINITIONS}
MAX_PRICE = 2**63 - 1


def ensure_default_prices(model):
    existing = set(model.objects.values_list("key", flat=True))
    missing = [
        model(key=item["key"], amount=item["default"])
        for item in PRICE_DEFINITIONS
        if item["key"] not in existing
    ]
    if missing:
        model.objects.bulk_create(missing, ignore_conflicts=True)


def parse_price_updates(payload):
    values = {}
    errors = {}
    for item in PRICE_DEFINITIONS:
        key = item["key"]
        raw_value = str(payload.get(f"price_{key}", "")).strip()
        try:
            value = int(raw_value)
        except (TypeError, ValueError):
            errors[key] = "Butun son kiriting."
            continue
        if key.startswith("star_pack_") and value <= 0:
            errors[key] = "Stars va olmos miqdori 0 dan katta bo'lishi kerak."
        elif value < 0:
            errors[key] = "Narx manfiy bo'lishi mumkin emas."
        elif value > MAX_PRICE:
            errors[key] = "Narx ruxsat etilgan chegaradan katta."
        else:
            values[key] = value
    return values, errors


def group_price_definitions(amounts, errors=None):
    errors = errors or {}
    categories = []
    grouped = {}
    for definition in PRICE_DEFINITIONS:
        if definition["key"].endswith("_diamonds"):
            continue
        item = dict(definition)
        item["min"] = 1 if item["currency"] == "stars" else 0
        if item["currency"] == "stars":
            diamond_key = f"{item['key']}_diamonds"
            diamond_default = PRICE_DEFINITIONS_BY_KEY[diamond_key]["default"]
            item.update({
                "label": f"Paket {list(STAR_PACK_KEYS.values()).index(item['key']) + 1}",
                "diamond_key": diamond_key,
                "diamonds": amounts.get(diamond_key, diamond_default),
                "diamond_default": diamond_default,
                "diamond_error": errors.get(diamond_key),
            })
        item["amount"] = amounts.get(item["key"], item["default"])
        item["error"] = errors.get(item["key"])
        if item["category"] not in grouped:
            group = {"name": item["category"], "items": []}
            grouped[item["category"]] = group
            categories.append(group)
        grouped[item["category"]]["items"].append(item)
    return categories
