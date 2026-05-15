from django.shortcuts import render
from django.core.cache import cache
from django.db import connection
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta

from django.db import models as djmodels
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
                SELECT gp.id  AS player_id,
                       gp.user_id,          -- bu user.id (Django PK)
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
            JOIN "user" u ON u.id = pd.user_id   -- user.id = Django PK
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

    # Tugagan o'yinlar: phase='end' YOKI is_active=false
    sql = "SELECT id FROM game WHERE (phase = 'end' OR is_active = false)"
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


def debug_stats(request):
    """Vaqtinchalik debug endpoint — DB strukturasini tekshirish."""
    out = {}
    month_start = _period_start('month')

    with connection.cursor() as cur:
        # 1. Jami o'yinlar va phase taqsimoti
        cur.execute("""
            SELECT phase, is_active, COUNT(*) AS cnt
            FROM game
            GROUP BY phase, is_active
            ORDER BY cnt DESC
        """)
        out['games_by_phase'] = [
            {'phase': r[0], 'is_active': r[1], 'count': r[2]}
            for r in cur.fetchall()
        ]

        # 2. Bu oy: hamma o'yinlar vs filtrdan o'tganlar
        cur.execute("SELECT COUNT(*) FROM game WHERE created_at >= %s", [month_start])
        out['games_this_month_total'] = cur.fetchone()[0]

        cur.execute(
            "SELECT COUNT(*) FROM game WHERE (phase='end' OR is_active=false) AND created_at >= %s",
            [month_start]
        )
        out['games_this_month_filtered'] = cur.fetchone()[0]

        # 3. Filtrsiz (hamma vaqt) tugagan o'yinlar
        cur.execute("SELECT COUNT(*) FROM game WHERE phase='end' OR is_active=false")
        out['games_finished_alltime'] = cur.fetchone()[0]

        # 4. So'nggi 5 o'yin
        cur.execute("""
            SELECT id, phase, is_active, created_at
            FROM game ORDER BY id DESC LIMIT 5
        """)
        out['recent_games'] = [
            {'id': r[0], 'phase': r[1], 'is_active': r[2], 'created_at': str(r[3])}
            for r in cur.fetchall()
        ]

        # 5. Bu oy ichidagi so'nggi 5 o'yin
        cur.execute("""
            SELECT id, phase, is_active, created_at
            FROM game WHERE created_at >= %s ORDER BY id DESC LIMIT 5
        """, [month_start])
        out['recent_games_this_month'] = [
            {'id': r[0], 'phase': r[1], 'is_active': r[2], 'created_at': str(r[3])}
            for r in cur.fetchall()
        ]

        # 6. gameplayer join test (u.id)
        cur.execute("""
            SELECT gp.id, gp.user_id, gp.win, u.id AS uid, u.user_id AS tg_uid, u.full_name
            FROM gameplayer gp
            JOIN "user" u ON u.id = gp.user_id
            LIMIT 3
        """)
        rows = cur.fetchall()
        out['join_by_u_id'] = [
            {'gp_id': r[0], 'gp_user_id': r[1], 'win': r[2],
             'user_pk': r[3], 'tg_id': r[4], 'name': r[5]}
            for r in rows
        ] if rows else 'NO ROWS'

        # 7. gameplayer join test (u.user_id)
        cur.execute("""
            SELECT gp.id, gp.user_id, u.id AS uid, u.user_id AS tg_uid, u.full_name
            FROM gameplayer gp
            JOIN "user" u ON u.user_id = gp.user_id
            LIMIT 3
        """)
        rows2 = cur.fetchall()
        out['join_by_u_user_id'] = [
            {'gp_id': r[0], 'gp_user_id': r[1],
             'user_pk': r[2], 'tg_id': r[3], 'name': r[4]}
            for r in rows2
        ] if rows2 else 'NO ROWS'

        # 8. Sample score calc for 5 finished games (any time)
        cur.execute("""
            SELECT id FROM game WHERE phase='end' OR is_active=false
            ORDER BY id DESC LIMIT 5
        """)
        sample_ids = [r[0] for r in cur.fetchall()]
        if sample_ids:
            cur.execute("""
                SELECT gp.user_id, u.full_name, COUNT(*) AS played,
                       COUNT(*) FILTER (WHERE gp.win=true) AS wins
                FROM gameplayer gp
                JOIN "user" u ON u.id = gp.user_id
                WHERE gp.game_id = ANY(%s)
                GROUP BY gp.user_id, u.full_name
                ORDER BY wins DESC LIMIT 5
            """, [sample_ids])
            rows3 = cur.fetchall()
            out['sample_scores_join_by_uid'] = [
                {'user_id': r[0], 'name': r[1], 'played': r[2], 'wins': r[3]}
                for r in rows3
            ] if rows3 else 'NO ROWS'
        else:
            out['sample_scores_join_by_uid'] = 'NO FINISHED GAMES'

        # 9. gameplayer first row raw
        cur.execute("SELECT * FROM gameplayer LIMIT 1")
        if cur.description:
            cols = [d[0] for d in cur.description]
            row = cur.fetchone()
            out['gameplayer_first_row'] = dict(zip(cols, [str(v) for v in row])) if row else 'EMPTY'

        # 10. month_start value used
        out['month_start_used'] = str(month_start)

    return JsonResponse(out, json_dumps_params={'ensure_ascii': False, 'indent': 2})


def landing(request):
    top_players = calculate_stats('month')[:30]
    period_label = 'Oylik'

    # Agar bu oy ma'lumot bo'lmasa — barcha vaqt bo'yicha ko'rsat
    if not top_players:
        top_players = calculate_stats('all')[:30]
        period_label = "Barcha vaqt"

    month_start = _period_start('month')
    total_games = Game.objects.filter(
        created_at__gte=month_start
    ).filter(
        djmodels.Q(phase='end') | djmodels.Q(is_active=False)
    ).count()

    # Agar bu oy o'yin bo'lmasa — jami hisoblash
    if total_games == 0:
        total_games = Game.objects.filter(
            djmodels.Q(phase='end') | djmodels.Q(is_active=False)
        ).count()

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
            'chat_id': g.chat_id,
        }
        for g in top_balances
    ]

    return render(request, 'main/landing.html', {
        'top_players':   top_players,
        'top_groups':    top_groups,
        'total_games':   total_games,
        'period_label':  period_label,
    })
