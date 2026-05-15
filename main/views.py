from django.shortcuts import render
from django.core.cache import cache
from django.db import connection
from django.utils import timezone
from datetime import timedelta

from bot.models import GroupBalance, Chat, Game

CHUNK_SIZE = 500
CACHE_TTL  = 60 * 15  # 15 daqiqa


def _period_start(period):
    now = timezone.now()
    if period == 'today':
        return now.replace(hour=0, minute=0, second=0, microsecond=0)
    if period == 'week':
        return (now - timedelta(days=now.weekday())).replace(
            hour=0, minute=0, second=0, microsecond=0)
    if period == 'month':
        return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return None  # 'all'


def _score_chunk(game_ids, acc):
    """Bir chunk game_ids uchun score hisoblaydi, acc dict ga qo'shadi."""
    with connection.cursor() as cur:
        cur.execute("""
            WITH gs AS (
                SELECT game_id,
                       COUNT(*)                             AS total,
                       COUNT(*) FILTER (WHERE win = true)  AS win_cnt
                FROM gameplayer
                WHERE game_id = ANY(%s)
                GROUP BY game_id
            ),
            pd AS (
                SELECT gp.id AS player_id,
                       gp.user_id,
                       CASE WHEN gp.win
                            THEN (2 * gs.total - gs.win_cnt)
                            ELSE -gs.win_cnt
                       END AS delta
                FROM gameplayer gp
                JOIN gs ON gp.game_id = gs.game_id
            ),
            ex AS (
                SELECT pgb.player_id, COALESCE(SUM(pgb.ball), 0) AS extra
                FROM playersgameball pgb
                WHERE pgb.player_id IN (SELECT player_id FROM pd)
                GROUP BY pgb.player_id
            )
            SELECT pd.user_id,
                   u.full_name,
                   SUM(pd.delta + COALESCE(ex.extra, 0)) AS score,
                   COUNT(*)                               AS played
            FROM pd
            JOIN "user" u ON u.user_id = pd.user_id
            LEFT JOIN ex ON ex.player_id = pd.player_id
            GROUP BY pd.user_id, u.full_name
        """, [game_ids])

        for user_id, full_name, score, played in cur.fetchall():
            if user_id in acc:
                acc[user_id]['score']  += int(score)
                acc[user_id]['played'] += int(played)
            else:
                acc[user_id] = {
                    'score':     int(score),
                    'played':    int(played),
                    'full_name': full_name,
                }


def calculate_stats(period, chat_id=None):
    """
    Reyting hisoblash.
    Qaytaradi: [{'user_id', 'full_name', 'score', 'played'}, ...]
               score bo'yicha DESC tartibda.
    Cache TTL = 15 daqiqa.
    """
    cache_key = f'stats:{period}:{chat_id or "global"}'
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    start = _period_start(period)

    # Tugagan o'yinlar (is_active=False)
    sql = "SELECT id FROM game WHERE is_active = false"
    params = []
    if start:
        sql += " AND created_at >= %s"
        params.append(start)
    if chat_id:
        sql += " AND chat_id = %s"
        params.append(chat_id)

    with connection.cursor() as cur:
        cur.execute(sql, params)
        game_ids = [row[0] for row in cur.fetchall()]

    acc = {}
    for i in range(0, len(game_ids), CHUNK_SIZE):
        _score_chunk(game_ids[i:i + CHUNK_SIZE], acc)

    result = sorted(
        [{'user_id': uid, **data} for uid, data in acc.items()],
        key=lambda x: x['score'],
        reverse=True,
    )

    cache.set(cache_key, result, CACHE_TTL)
    return result


def landing(request):
    top_players = calculate_stats('month')[:30]

    month_start = _period_start('month')
    total_games = Game.objects.filter(is_active=False, created_at__gte=month_start).count()

    top_balances = (
        GroupBalance.objects
        .filter(balance__gt=0)
        .order_by('-balance')[:5]
    )
    chat_map = {
        c.chat_id: c.title
        for c in Chat.objects.filter(
            chat_id__in=[g.chat_id for g in top_balances]
        )
    }
    top_groups = [
        {
            'title':   chat_map.get(g.chat_id, f'Guruh #{g.chat_id}'),
            'balance': g.balance,
        }
        for g in top_balances
    ]

    return render(request, 'main/landing.html', {
        'top_players': top_players,
        'top_groups':  top_groups,
        'total_games': total_games,
    })
