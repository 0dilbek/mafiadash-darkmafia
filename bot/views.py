import uuid as _uuid
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Sum, Count, Q, Subquery, OuterRef, Exists, F
from django.db.models.functions import TruncHour, TruncDay, TruncMonth
from django.core.paginator import Paginator
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
from urllib.parse import urlencode
import json as _json
from .models import (
    User, BlockedUser, Profile, Transfer, VipUser, Para, Chat, Giveaway,
    Game, GamePlayer, GamePhase, GroupBalance, BlockGroups, AdminLoginToken,
    ChatRoleOrder,
)

# ── Rol tizimlari ──────────────────────────────────────────────────────────────
# Kalit = botdagi RoleNames qiymati (bazada shu holda saqlanadi)

ROLE_TEAMS = {
    '🕵🏼 Komissar katani': 'tinch',
    '👮🏼 Serjant':         'tinch',
    '⚡️ Koldun':           'tinch',
    '🧙‍♂️ Daydi':           'tinch',
    '👨🏼‍⚕️ Doktor':         'tinch',
    '💊 Anistizolog':       'tinch',
    '👨🏼 Tinch axoli':     'tinch',
    '🎖 Janob':             'tinch',
    '💣 Afsungar':          'tinch',
    '🤵🏻 Don':              'mafia',
    '🤵🏼 Mafia':            'mafia',
    '👨🏼‍💼 Advokat':         'mafia',
    '🥷 Убийца':            'mafia',
    '👩🏼‍💻 Jurnalist':       'mafia',
    '🤹🏻 Aferist':          'yakka',
    "🧌 G'azabkor":         'yakka',
    '🤡 Joker':             'yakka',
    '👨‍🔬 Kimyogar':         'yakka',
    '☠️ Minior':            'yakka',
    '🔪 Qotil':             'yakka',
    '🤦🏼 Suidsid':          'yakka',
    '🧛🏻 Vampir':           'yakka',
    '🦎 Buqalamun':         'yakka',
    '🧙 Sehrgar':           'yakka',
}

DEFAULT_ROLE_ORDER = [
    '🤵🏻 Don',        '🕵🏼 Komissar katani', '👨🏼‍⚕️ Doktor',     '👨🏼 Tinch axoli',
    '👨🏼 Tinch axoli', '🧙‍♂️ Daydi',          '🤵🏼 Mafia',        '💊 Anistizolog',
    '🦎 Buqalamun',   '💣 Afsungar',          '👨🏼 Tinch axoli',  '🤦🏼 Suidsid',
    '👨🏼‍💼 Advokat',    '🔪 Qotil',            '👨🏼 Tinch axoli',  '🎖 Janob',
    '👩🏼‍💻 Jurnalist',  '🤹🏻 Aferist',         '👨🏼 Tinch axoli',  '🧙 Sehrgar',
    '💣 Afsungar',    '👮🏼 Serjant',          '🤵🏼 Mafia',        "🧌 G'azabkor",
    '🥷 Убийца',      '🦎 Buqalamun',         '👨🏼 Tinch axoli',  '☠️ Minior',
    '💣 Afsungar',    '🤡 Joker',             '👨🏼 Tinch axoli',  '🧛🏻 Vampir',
    '🤵🏼 Mafia',      '👮🏼 Serjant',          '👨🏼 Tinch axoli',  '👨‍🔬 Kimyogar',
    '💣 Afsungar',    '🦎 Buqalamun',         '🤵🏼 Mafia',        '👮🏼 Serjant',
    '👨🏼 Tinch axoli', '🧛🏻 Vampir',          '🤵🏼 Mafia',        '👨🏼 Tinch axoli',
    '👨🏼 Tinch axoli',
]


def _validate_role_order(roles):
    """Har bir o'yinchilar sonida mafia < tinch bo'lishini tekshiradi."""
    errors = []
    for n in range(4, len(roles) + 1):
        sl = roles[:n]
        mafia = sum(1 for r in sl if ROLE_TEAMS.get(r) == 'mafia')
        tinch = sum(1 for r in sl if ROLE_TEAMS.get(r) == 'tinch')
        if mafia >= tinch:
            errors.append(f"{n} kishi: mafia ({mafia}) ≥ tinch ({tinch})")
    return errors


def _stat_period_filter(period):
    now = timezone.now()
    opts = {
        'today': (now.replace(hour=0, minute=0, second=0, microsecond=0), 'Bugun'),
        'week':  (now - timedelta(days=7),   'Shu hafta'),
        'month': (now - timedelta(days=30),  'Shu oy'),
        'year':  (now - timedelta(days=365), 'Shu yil'),
    }
    return opts.get(period, (None, 'Barcha vaqt'))


@login_required
def dashboard(request):
    sp = request.GET.get('sp', '')
    start_dt, period_label = _stat_period_filter(sp)

    def gte(qs, field='created_at'):
        return qs.filter(**{f'{field}__gte': start_dt}) if start_dt else qs

    total_users = User.objects.filter(profile__isnull=False).count()
    total_vip = VipUser.objects.count()
    total_chats = Chat.objects.count()
    active_games_count = Game.objects.filter(is_active=True).count()

    period_games = gte(Game.objects.all()).count()
    period_players = gte(GamePlayer.objects.all(), 'joined_at').count()
    period_new_chats = gte(Chat.objects.all()).count()
    transfers_qs = gte(Transfer.objects.all())
    period_transfers = transfers_qs.count()
    dollar_total = transfers_qs.filter(type='dollar').aggregate(s=Sum('amount'))['s'] or 0
    diamond_total = transfers_qs.filter(type='diamond').aggregate(s=Sum('amount'))['s'] or 0

    top_players = Profile.objects.select_related('user').order_by('-wins')[:10]
    richest = Profile.objects.select_related('user').order_by('-dollar')[:10]
    recent_transfers = Transfer.objects.select_related('from_user', 'to_user').order_by('-created_at')[:10]
    recent_active = (
        Game.objects.filter(is_active=True)
        .select_related('chat')
        .annotate(
            total_pl=Count('players', distinct=True),
            alive_pl=Count('players', filter=Q(players__is_alive=True), distinct=True),
        )
        .order_by('-created_at')[:6]
    )

    return render(request, 'bot/dashboard.html', {
        'total_users': total_users,
        'total_vip': total_vip,
        'total_chats': total_chats,
        'active_games_count': active_games_count,
        'period_games': period_games,
        'period_players': period_players,
        'period_transfers': period_transfers,
        'period_new_chats': period_new_chats,
        'dollar_total': dollar_total,
        'diamond_total': diamond_total,
        'top_players': top_players,
        'richest': richest,
        'recent_transfers': recent_transfers,
        'recent_active': recent_active,
        'sp': sp,
        'period_label': period_label,
    })


@login_required
def dashboard_chart_data(request):
    period = request.GET.get('period', '12h')
    now = timezone.now()

    cfg = {
        '12h':   (now - timedelta(hours=12), TruncHour,  'hour',  '%H:00', timedelta(hours=1)),
        '24h':   (now - timedelta(hours=24), TruncHour,  'hour',  '%H:00', timedelta(hours=1)),
        'today': (now.replace(hour=0, minute=0, second=0, microsecond=0), TruncHour, 'hour', '%H:00', timedelta(hours=1)),
        'week':  (now - timedelta(days=7),   TruncDay,   'day',   '%d.%m', timedelta(days=1)),
        'month': (now - timedelta(days=30),  TruncDay,   'day',   '%d.%m', timedelta(days=1)),
        'year':  (now - timedelta(days=365), TruncMonth, 'month', '%m.%Y', None),
    }
    start, trunc_fn, trunc_type, fmt, delta = cfg.get(period, cfg['12h'])

    buckets = []
    if trunc_type == 'month':
        cur = start.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        while cur <= now:
            buckets.append(cur)
            cur = cur.replace(year=cur.year + (1 if cur.month == 12 else 0),
                              month=cur.month % 12 + 1)
    elif trunc_type == 'hour':
        cur = start.replace(minute=0, second=0, microsecond=0)
        while cur <= now:
            buckets.append(cur)
            cur += delta
    else:
        cur = start.replace(hour=0, minute=0, second=0, microsecond=0)
        while cur <= now:
            buckets.append(cur)
            cur += delta

    def bucket_dict(qs, field):
        return {
            row['bucket']: row['count']
            for row in qs.filter(**{f'{field}__gte': start})
            .annotate(bucket=trunc_fn(field))
            .values('bucket')
            .annotate(count=Count('id'))
            .order_by('bucket')
        }

    games_d = bucket_dict(Game.objects, 'created_at')
    players_d = bucket_dict(GamePlayer.objects, 'joined_at')

    return JsonResponse({
        'labels':  [b.strftime(fmt) for b in buckets],
        'games':   [games_d.get(b, 0) for b in buckets],
        'players': [players_d.get(b, 0) for b in buckets],
    })


@login_required
def active_games(request):
    games = (
        Game.objects.filter(is_active=True)
        .select_related('chat', 'creator')
        .annotate(
            total_players=Count('players', distinct=True),
            alive_players=Count('players', filter=Q(players__is_alive=True), distinct=True),
        )
        .order_by('-created_at')
    )
    return render(request, 'bot/active_games.html', {'games': games})


@login_required
def game_detail(request, pk):
    game = get_object_or_404(
        Game.objects.select_related('chat', 'creator').annotate(
            total_players=Count('players', distinct=True),
            alive_players=Count('players', filter=Q(players__is_alive=True), distinct=True),
        ),
        pk=pk,
    )
    players = GamePlayer.objects.filter(game=game).select_related('user').order_by('id')
    phases = GamePhase.objects.filter(game=game).order_by('number')
    return render(request, 'bot/game_detail.html', {
        'game': game, 'players': players, 'phases': phases,
    })


@login_required
def users_list(request):
    query = request.GET.get('q', '')
    sort = request.GET.get('sort', '-id')

    sort_map = {
        'name': 'full_name', '-name': '-full_name',
        'dollar': 'profile__dollar', '-dollar': '-profile__dollar',
        'diamond': 'profile__diamond', '-diamond': '-profile__diamond',
        'wins': 'profile__wins', '-wins': '-profile__wins',
        'id': 'id', '-id': '-id',
    }
    users = User.objects.filter(profile__isnull=False).prefetch_related('profile').order_by(sort_map.get(sort, '-id'))

    if query:
        users = users.filter(
            Q(full_name__icontains=query) | Q(mention__icontains=query) | Q(user_id__icontains=query)
        )

    paginator = Paginator(users, 50)
    users = paginator.get_page(request.GET.get('page'))
    return render(request, 'bot/users.html', {'users': users, 'query': query, 'sort': sort})


@login_required
def user_detail(request, user_id):
    user = get_object_or_404(User, id=user_id)
    profile = Profile.objects.filter(user=user).first()
    is_vip = VipUser.objects.filter(user=user).exists()
    is_blocked = BlockedUser.objects.filter(user=user).exists()
    transfers_sent = Transfer.objects.filter(from_user=user).order_by('-created_at')[:20]
    transfers_received = Transfer.objects.filter(to_user=user).order_by('-created_at')[:20]
    pairs = Para.objects.filter(Q(user1=user) | Q(user2=user)).select_related('user1', 'user2')[:10]

    return render(request, 'bot/user_detail.html', {
        'user': user, 'profile': profile,
        'is_vip': is_vip, 'is_blocked': is_blocked,
        'transfers_sent': transfers_sent, 'transfers_received': transfers_received,
        'pairs': pairs,
    })


@login_required
def transfers_list(request):
    type_filter = request.GET.get('type', '')
    transfers = Transfer.objects.select_related('from_user', 'to_user').order_by('-created_at')
    if type_filter:
        transfers = transfers.filter(type=type_filter)
    paginator = Paginator(transfers, 50)
    transfers = paginator.get_page(request.GET.get('page'))
    return render(request, 'bot/transfers.html', {'transfers': transfers, 'type_filter': type_filter})


@login_required
def vip_list(request):
    vips = VipUser.objects.select_related('user').order_by('-created_at')
    return render(request, 'bot/vip.html', {'vips': vips})


@login_required
def top_players(request):
    profiles = Profile.objects.select_related('user').order_by('-wins')
    paginator = Paginator(profiles, 50)
    profiles = paginator.get_page(request.GET.get('page'))
    return render(request, 'bot/top.html', {'profiles': profiles})


@login_required
def blocked_list(request):
    query = request.GET.get('q', '')
    blocked = BlockedUser.objects.select_related('user').order_by('-created_at')
    if query:
        blocked = blocked.filter(
            Q(user__full_name__icontains=query) |
            Q(user__mention__icontains=query) |
            Q(user__user_id__icontains=query)
        )
    paginator = Paginator(blocked, 50)
    blocked = paginator.get_page(request.GET.get('page'))
    return render(request, 'bot/blocked.html', {'blocked': blocked, 'query': query})


@login_required
def block_user(request):
    if request.method == 'POST':
        user_id_input = request.POST.get('user_id', '').strip()
        user = None
        if user_id_input.isdigit():
            user = User.objects.filter(user_id=int(user_id_input)).first()
        if not user:
            user = User.objects.filter(
                Q(full_name__icontains=user_id_input) | Q(mention__icontains=user_id_input)
            ).first()
        if not user:
            messages.error(request, f'Foydalanuvchi topilmadi: {user_id_input}')
        elif BlockedUser.objects.filter(user=user).exists():
            messages.warning(request, f'{user.full_name or user.mention} allaqachon bloklangan.')
        else:
            BlockedUser.objects.create(user=user)
            messages.success(request, f'{user.full_name or user.mention} bloklandi.')
    return redirect('blocked')


@login_required
def unblock_user(request, blocked_id):
    if request.method == 'POST':
        blocked = get_object_or_404(BlockedUser, id=blocked_id)
        name = blocked.user.full_name or blocked.user.mention
        blocked.delete()
        messages.success(request, f'{name} blokdan chiqarildi.')
    return redirect('blocked')


@login_required
def giveaways_list(request):
    query = request.GET.get('q', '')
    sort = request.GET.get('sort', '-created_at')
    sort_map = {
        'total': 'total_amount', '-total': '-total_amount',
        'remaining': 'remaining_amount', '-remaining': '-remaining_amount',
        'date': 'created_at', '-date': '-created_at',
    }
    chat_title_sq = Chat.objects.filter(chat_id=OuterRef('chat_id')).values('title')[:1]
    giveaways = (
        Giveaway.objects.select_related('creator')
        .exclude(remaining_amount=0)
        .annotate(chat_title=Subquery(chat_title_sq))
        .order_by(sort_map.get(sort, '-created_at'))
    )
    if query:
        giveaways = giveaways.filter(
            Q(creator__full_name__icontains=query) |
            Q(creator__mention__icontains=query) |
            Q(creator__user_id__icontains=query)
        )
    paginator = Paginator(giveaways, 50)
    giveaways = paginator.get_page(request.GET.get('page'))
    return render(request, 'bot/giveaways.html', {'giveaways': giveaways, 'query': query, 'sort': sort})


@login_required
def chats_list(request):
    query = request.GET.get('q', '')
    type_filter = request.GET.get('type', '')
    sort = request.GET.get('sort', '-date')
    date_filter = request.GET.get('date_filter', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    balance_sq = Subquery(
        GroupBalance.objects.filter(chat_id=OuterRef('chat_id')).values('balance')[:1]
    )
    chats = Chat.objects.annotate(
        games_count=Count('games', distinct=True),
        balance=balance_sq,
        is_blocked=Exists(BlockGroups.objects.filter(chat_id=OuterRef('chat_id'))),
    )

    if query:
        chats = chats.filter(Q(title__icontains=query) | Q(chat_id__icontains=query))
    if type_filter:
        chats = chats.filter(type=type_filter)

    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    date_filter_map = {
        'today':     {'created_at__gte': today_start},
        'yesterday': {'created_at__gte': today_start - timedelta(days=1), 'created_at__lt': today_start},
        'week':      {'created_at__gte': now - timedelta(days=7)},
        'month':     {'created_at__gte': now - timedelta(days=30)},
        'year':      {'created_at__gte': now - timedelta(days=365)},
    }
    if date_filter in date_filter_map:
        chats = chats.filter(**date_filter_map[date_filter])
    elif date_from or date_to:
        if date_from:
            chats = chats.filter(created_at__date__gte=date_from)
        if date_to:
            chats = chats.filter(created_at__date__lte=date_to)

    sort_map = {
        'games':    '-games_count',
        '-games':   'games_count',
        'balance':  F('balance').desc(nulls_last=True),
        '-balance': F('balance').asc(nulls_last=True),
        'date':     'created_at',
        '-date':    '-created_at',
    }
    chats = chats.order_by(sort_map.get(sort, '-created_at'))

    qs = urlencode({k: v for k, v in request.GET.items() if k != 'page'})
    paginator = Paginator(chats, 50)
    chats = paginator.get_page(request.GET.get('page'))

    return render(request, 'bot/chats.html', {
        'chats': chats,
        'query': query,
        'type_filter': type_filter,
        'sort': sort,
        'date_filter': date_filter,
        'date_from': date_from,
        'date_to': date_to,
        'qs': qs,
    })


@login_required
def chat_toggle_block(request, pk):
    if request.method == 'POST':
        chat = get_object_or_404(Chat, pk=pk)
        block_obj = BlockGroups.objects.filter(chat_id=chat.chat_id).first()
        if block_obj:
            block_obj.delete()
            messages.success(request, f'"{chat.title}" blokdan chiqarildi.')
        else:
            BlockGroups.objects.create(chat_id=chat.chat_id)
            messages.warning(request, f'"{chat.title}" bloklandi.')
    return redirect(request.POST.get('next', '/chats/'))


@login_required
def chat_clear_balance(request, pk):
    if request.method == 'POST':
        chat = get_object_or_404(Chat, pk=pk)
        GroupBalance.objects.filter(chat_id=chat.chat_id).update(
            balance=0, last_reset_at=timezone.now()
        )
        messages.success(request, f'"{chat.title}" balansi tozalandi.')
    return redirect(request.POST.get('next', '/chats/'))


# ── Magic Link autentifikatsiya ────────────────────────────────────────────────
# Django auth sistemasidan to'liq mustaqil — faqat session ishlatadi.

def magic_login(request):
    """
    Botdan yuborilgan magic-link token orqali foydalanuvchi sessiyasini ochadi.
    Django auth.User bilan hech qanday aloqasi yo'q.
    """
    token_str = request.GET.get('token', '').strip()

    if not token_str:
        return render(request, 'bot/magic_error.html', {'reason': 'no_token'})

    try:
        token_uuid = _uuid.UUID(token_str)
    except ValueError:
        return render(request, 'bot/magic_error.html', {'reason': 'invalid'})

    try:
        auth_token = AdminLoginToken.objects.get(token=token_uuid)
    except AdminLoginToken.DoesNotExist:
        return render(request, 'bot/magic_error.html', {'reason': 'invalid'})

    if not auth_token.is_valid():
        auth_token.delete()
        return render(request, 'bot/magic_error.html', {'reason': 'expired'})

    telegram_user_id = auth_token.user_id
    tg_chat_id = auth_token.chat_id  # delete() dan oldin saqlaymiz
    auth_token.delete()  # Bir martalik — darhol o'chiramiz

    # Faqat session — Django auth bilan aloqa yo'q
    request.session['tg_user_id'] = telegram_user_id
    request.session['tg_chat_id'] = tg_chat_id
    request.session['tg_authenticated'] = True
    request.session.set_expiry(86400)  # 24 soat

    return redirect('group_dashboard')


def magic_login_error(request):
    """Session yo'q yoki muddati o'tgan foydalanuvchilar uchun."""
    return render(request, 'bot/magic_error.html', {'reason': 'session_expired'})


def generate_panel_link(request):
    """
    Bot → Django: magic-link URL yaratib qaytaradi.

    GET /api/generate-link/?chat_id=-1001234567890

    Response: {"url": "https://domain/group/<uuid>/", "expires_at": "2026-..."}
    """
    chat_id_raw = request.GET.get('chat_id', '').strip()
    if not chat_id_raw:
        return JsonResponse({'error': 'chat_id required'}, status=400)
    try:
        chat_id = int(chat_id_raw)
    except ValueError:
        return JsonResponse({'error': 'invalid chat_id'}, status=400)

    # Bir vaqtda faqat bitta aktiv token — eskisini o'chiramiz
    AdminLoginToken.objects.filter(chat_id=chat_id).delete()

    expires_at = timezone.now() + timedelta(days=1)
    token_obj = AdminLoginToken.objects.create(
        user_id=0,       # bot generate qilganda user_id shart emas
        chat_id=chat_id,
        expires_at=expires_at,
    )
    url = f"{settings.DASHBOARD_URL}/group/{token_obj.token}/"
    return JsonResponse({'url': url, 'expires_at': expires_at.isoformat()})


# ── Guruh egasi / admin uchun sahifa ──────────────────────────────────────────

def panel_entry(request, token):
    """
    GET /group/<uuid:token>/
    Token orqali sessiya ochadi va guruh paneliga yo'naltiradi.
    """
    try:
        obj = AdminLoginToken.objects.get(token=token)
    except AdminLoginToken.DoesNotExist:
        return render(request, 'bot/magic_error.html', {'reason': 'invalid'})

    if timezone.now() > obj.expires_at:
        obj.delete()
        return render(request, 'bot/magic_error.html', {'reason': 'expired'})

    tg_chat_id = obj.chat_id

    if not tg_chat_id:
        return render(request, 'bot/magic_error.html', {'reason': 'no_chat'})

    request.session['tg_chat_id'] = tg_chat_id
    request.session['tg_authenticated'] = True
    request.session.set_expiry(86400)
    return redirect('group_dashboard')


def _tg_auth_required(request):
    """Session tekshiradi, False bo'lsa error response qaytaradi."""
    return request.session.get('tg_authenticated') and request.session.get('tg_chat_id')


def group_dashboard(request):
    if not _tg_auth_required(request):
        return redirect('magic_login_error')

    tg_chat_id = request.session['tg_chat_id']
    chat = Chat.objects.filter(chat_id=tg_chat_id).first()
    if not chat:
        return render(request, 'bot/magic_error.html', {'reason': 'no_chat'})

    total_games = Game.objects.filter(chat=chat).count()
    active_game = (
        Game.objects.filter(chat=chat, is_active=True)
        .annotate(
            total_pl=Count('players', distinct=True),
            alive_pl=Count('players', filter=Q(players__is_alive=True), distinct=True),
        )
        .order_by('-created_at')
        .first()
    )
    balance_obj = GroupBalance.objects.filter(chat_id=tg_chat_id).first()
    balance = balance_obj.balance if balance_obj else 0

    return render(request, 'bot/group_dashboard.html', {
        'chat': chat,
        'total_games': total_games,
        'active_game': active_game,
        'balance': balance,
    })


def group_chart_data(request):
    if not _tg_auth_required(request):
        return HttpResponseForbidden()

    tg_chat_id = request.session['tg_chat_id']
    chat = Chat.objects.filter(chat_id=tg_chat_id).first()
    if not chat:
        return JsonResponse({'labels': [], 'games': [], 'players': []})

    period = request.GET.get('period', 'week')
    now = timezone.now()
    cfg = {
        '12h':   (now - timedelta(hours=12), TruncHour,  'hour',  '%H:00', timedelta(hours=1)),
        '24h':   (now - timedelta(hours=24), TruncHour,  'hour',  '%H:00', timedelta(hours=1)),
        'today': (now.replace(hour=0, minute=0, second=0, microsecond=0), TruncHour, 'hour', '%H:00', timedelta(hours=1)),
        'week':  (now - timedelta(days=7),   TruncDay,   'day',   '%d.%m', timedelta(days=1)),
        'month': (now - timedelta(days=30),  TruncDay,   'day',   '%d.%m', timedelta(days=1)),
        'year':  (now - timedelta(days=365), TruncMonth, 'month', '%m.%Y', None),
    }
    start, trunc_fn, trunc_type, fmt, delta = cfg.get(period, cfg['week'])

    buckets = []
    if trunc_type == 'month':
        cur = start.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        while cur <= now:
            buckets.append(cur)
            cur = cur.replace(year=cur.year + (1 if cur.month == 12 else 0),
                              month=cur.month % 12 + 1)
    elif trunc_type == 'hour':
        cur = start.replace(minute=0, second=0, microsecond=0)
        while cur <= now:
            buckets.append(cur)
            cur += delta
    else:
        cur = start.replace(hour=0, minute=0, second=0, microsecond=0)
        while cur <= now:
            buckets.append(cur)
            cur += delta

    games_d = {
        row['bucket']: row['count']
        for row in Game.objects.filter(chat=chat, created_at__gte=start)
        .annotate(bucket=trunc_fn('created_at'))
        .values('bucket').annotate(count=Count('id')).order_by('bucket')
    }
    players_d = {
        row['bucket']: row['count']
        for row in GamePlayer.objects.filter(game__chat=chat, joined_at__gte=start)
        .annotate(bucket=trunc_fn('joined_at'))
        .values('bucket').annotate(count=Count('id')).order_by('bucket')
    }

    return JsonResponse({
        'labels':  [b.strftime(fmt) for b in buckets],
        'games':   [games_d.get(b, 0) for b in buckets],
        'players': [players_d.get(b, 0) for b in buckets],
    })


def group_role_order(request):
    if not _tg_auth_required(request):
        return redirect('magic_login_error')

    tg_chat_id = request.session['tg_chat_id']
    chat = Chat.objects.filter(chat_id=tg_chat_id).first()

    obj, _ = ChatRoleOrder.objects.get_or_create(
        chat_id=tg_chat_id,
        defaults={'roles': DEFAULT_ROLE_ORDER},
    )

    if request.method == 'POST':
        try:
            data = _json.loads(request.body)
            roles = list(data['roles'])
        except (KeyError, ValueError, _json.JSONDecodeError):
            return JsonResponse({'ok': False, 'error': 'bad_request'}, status=400)

        valid = set(ROLE_TEAMS.keys())
        bad = [r for r in roles if r not in valid]
        if bad:
            return JsonResponse({'ok': False, 'error': f"Noto'g'ri rol: {bad[0]}"}, status=400)

        errs = _validate_role_order(roles)
        if errs:
            return JsonResponse({'ok': False, 'errors': errs}, status=422)

        obj.roles = roles
        obj.save()
        return JsonResponse({'ok': True})

    role_data = [
        {'name': r, 'team': ROLE_TEAMS.get(r, 'unknown')}
        for r in obj.roles
    ]
    return render(request, 'bot/group_role_order.html', {
        'chat': chat,
        'role_data': role_data,
        'roles_json': _json.dumps(obj.roles),
        'default_roles_json': _json.dumps(DEFAULT_ROLE_ORDER),
        'role_teams_json': _json.dumps(ROLE_TEAMS),
    })
