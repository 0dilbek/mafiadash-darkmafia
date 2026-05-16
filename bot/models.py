import uuid as _uuid
from django.db import models
from django.utils import timezone as tz
from datetime import datetime, timezone, timedelta


class AdminLoginToken(models.Model):
    """Magic-link token: botdan yaratiladi, Django sessiyasini ochadi."""
    user_id = models.BigIntegerField(db_index=True)       # Telegram admin ID
    chat_id = models.BigIntegerField(null=True, blank=True)  # Qaysi guruh uchun
    token = models.UUIDField(default=_uuid.uuid4, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        db_table = "admin_login_tokens"

    def is_valid(self):
        return tz.now() < self.expires_at

    @classmethod
    def create_for_user(cls, telegram_user_id: int, chat_id: int = None, days: int = 1):
        """Yangi token yaratadi; avvalgi eskirgan tokenlarni tozalaydi."""
        cls.objects.filter(user_id=telegram_user_id, expires_at__lt=tz.now()).delete()
        return cls.objects.create(
            user_id=telegram_user_id,
            chat_id=chat_id,
            expires_at=tz.now() + timedelta(days=days),
        )


class User(models.Model):
    id = models.BigAutoField(primary_key=True)
    user_id = models.BigIntegerField()
    full_name = models.CharField(max_length=100, default="", null=True, blank=True)
    is_bot = models.BooleanField(default=False)
    mention = models.TextField()
    lang = models.CharField(max_length=2, default="uz")

    class Meta:
        db_table = "user"
        managed = False

    def __str__(self):
        return self.full_name or str(self.user_id)


class BlockedUser(models.Model):
    user = models.ForeignKey(User, related_name="blocked_users", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "blocked_user"
        managed = False

    def __str__(self):
        return f"Blocked: {self.user}"


class Profile(models.Model):
    user = models.OneToOneField(User, related_name="profile", on_delete=models.CASCADE)
    dollar = models.BigIntegerField(default=0)
    diamond = models.BigIntegerField(default=0)
    himoya = models.IntegerField(default=0)
    hujjat = models.IntegerField(default=0)
    qotildan_himoya = models.IntegerField(default=0)
    osishdan_himoya = models.IntegerField(default=0)
    miltiq = models.IntegerField(default=0)
    doridan_himoya = models.IntegerField(default=0)
    maska = models.IntegerField(default=0)
    verbana = models.IntegerField(default=0)
    wins = models.BigIntegerField(default=0)
    slip_himoya = models.IntegerField(default=0)
    geroy_himoya = models.IntegerField(default=0)
    games_count = models.BigIntegerField(default=0)
    on_himoya = models.BooleanField(default=True)
    on_hujjat = models.BooleanField(default=True)
    on_qotildan_himoya = models.BooleanField(default=True)
    on_osishdan_himoya = models.BooleanField(default=True)
    on_miltiq = models.BooleanField(default=True)
    on_verbana = models.BooleanField(default=True)
    on_doridan_himoya = models.BooleanField(default=True)
    on_maska = models.BooleanField(default=True)
    on_slip_himoya = models.BooleanField(default=True)
    on_geroy_himoya = models.BooleanField(default=True)

    class Meta:
        db_table = "profile"
        managed = False

    def __str__(self):
        return f"Profile: {self.user}"


class ActiveRole(models.Model):
    profile = models.ForeignKey(Profile, related_name="active_roles", on_delete=models.CASCADE)
    role = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "activerole"
        managed = False

    def __str__(self):
        return f"{self.role} - {self.profile}"


class Transfer(models.Model):
    id = models.BigAutoField(primary_key=True)
    from_user = models.ForeignKey(User, related_name="transfers_from", on_delete=models.CASCADE)
    to_user = models.ForeignKey(User, related_name="transfers_to", on_delete=models.CASCADE)
    amount = models.BigIntegerField()
    type = models.CharField(max_length=50)  # "diamond", "dollar"
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "transfers"
        managed = False

    def __str__(self):
        return f"{self.from_user} → {self.to_user}: {self.amount} {self.type}"


class VipUser(models.Model):
    user = models.OneToOneField(User, related_name="vip", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "vipuser"
        managed = False

    def __str__(self):
        return f"VIP: {self.user}"


class Para(models.Model):
    user1 = models.ForeignKey(User, related_name="paralar1", on_delete=models.CASCADE)
    user2 = models.ForeignKey(User, related_name="paralar2", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "paralar"
        managed = False

    def __str__(self):
        return f"{self.user1} & {self.user2}"


class Giveaway(models.Model):
    id = models.BigAutoField(primary_key=True)
    creator = models.ForeignKey(User, related_name="giveaways", on_delete=models.CASCADE)
    chat_id = models.BigIntegerField()
    message_id = models.BigIntegerField()
    total_amount = models.BigIntegerField()
    remaining_amount = models.BigIntegerField()
    collected_users = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "giveaway"
        managed = False

    def __str__(self):
        return f"Giveaway #{self.id} by {self.creator}"

    @property
    def distributed_amount(self):
        return self.total_amount - self.remaining_amount

    @property
    def collected_count(self):
        return len(self.collected_users) if self.collected_users else 0


class Chat(models.Model):
    id = models.BigAutoField(primary_key=True)
    chat_id = models.BigIntegerField()
    title = models.CharField(max_length=255)
    type = models.CharField(max_length=50)  # group / supergroup
    lang = models.CharField(max_length=2, default="uz")  # yangilandi: tortoise modelda bor edi
    created_at = models.DateTimeField(auto_now_add=True)
    invite_link = models.CharField(max_length=500, default="")

    class Meta:
        db_table = "chat"
        managed = False

    def __str__(self):
        return self.title


# ── BalanceTransaction ─────────────────────────────────────────────────────────

class BalanceTransaction(models.Model):
    id = models.AutoField(primary_key=True)
    chat_id = models.BigIntegerField()
    amount = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_processed = models.IntegerField(default=0)  # 0 = to'lanmagan, 1 = to'langan

    class Meta:
        db_table = "balance_transactions"
        managed = False

    def __str__(self):
        return f"BalanceTransaction(chat_id={self.chat_id}, amount={self.amount})"

    @classmethod
    def create_transaction(cls, chat_id: int, amount: int):
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(days=7)
        return cls.objects.create(chat_id=chat_id, amount=amount, expires_at=expires_at)

    @classmethod
    def get_expired_transactions(cls):
        now = datetime.now(timezone.utc)
        return cls.objects.filter(expires_at__lte=now, is_processed=0)

    def mark_processed(self):
        self.is_processed = 1
        self.save(update_fields=["is_processed"])


# ── Game ───────────────────────────────────────────────────────────────────────

class Game(models.Model):
    id = models.BigAutoField(primary_key=True)
    chat = models.ForeignKey(Chat, related_name="games", on_delete=models.CASCADE)
    creator = models.ForeignKey(User, related_name="created_games", on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    message_id = models.BigIntegerField()
    phase = models.CharField(max_length=10, default="waiting")  # waiting / night / day / end
    mode = models.CharField(max_length=20, default="classic")
    bot_id = models.BigIntegerField(null=True, blank=True)

    class Meta:
        db_table = "game"
        managed = False

    def __str__(self):
        return f"Game #{self.id}"


class GamePhase(models.Model):
    id = models.BigAutoField(primary_key=True)
    game = models.ForeignKey(Game, related_name="phases", on_delete=models.CASCADE)
    phase_type = models.CharField(max_length=10)  # day / night
    number = models.BigIntegerField()
    started_at = models.DateTimeField(auto_now_add=True)
    is_end = models.BooleanField(default=False)

    class Meta:
        db_table = "gamephase"
        managed = False

    def __str__(self):
        return f"Phase {self.phase_type} #{self.number}"


class GamePlayer(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, related_name="game_players", on_delete=models.CASCADE)
    game = models.ForeignKey(Game, related_name="players", on_delete=models.CASCADE)
    role = models.CharField(max_length=70)
    is_alive = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)
    deaded_at = models.DateTimeField(null=True, blank=True)
    is_sayed_last_word = models.BooleanField(default=False)
    can_heal_self = models.BooleanField(default=True)
    can_protection_self = models.BooleanField(default=True)
    can_document_self = models.BooleanField(default=True)
    can_investigate_self = models.BooleanField(default=True)
    can_osishdan_himoya = models.BooleanField(default=True)
    can_osishdan_himoya_adv = models.BooleanField(default=True)
    can_slip_himoya = models.BooleanField(default=True)
    is_sleep = models.BooleanField(default=False)
    is_osilmas = models.BooleanField(default=False)
    osildi = models.BooleanField(default=False)
    missed_nights = models.BigIntegerField(default=0)
    should_choose_card = models.BooleanField(default=False)
    is_really_winner = models.BooleanField(default=False)
    last_visited_user_id = models.BigIntegerField(null=True, blank=True)
    maxsus_raqam = models.BigIntegerField(null=True, blank=True)
    win = models.BooleanField(default=False)
    gazabdor_targets = models.ManyToManyField(
        "self",
        related_name="picked_by_gazabdor",
        symmetrical=False,
        blank=True,
    )
    is_actioned = models.BooleanField(default=False)
    life = models.IntegerField(default=100)
    team = models.CharField(max_length=20, null=True, blank=True)

    class Meta:
        db_table = "gameplayer"
        managed = False

    def __str__(self):
        return f"Player {self.user} as {self.role}"


class PlayersGameBall(models.Model):
    player = models.ForeignKey(GamePlayer, related_name="player_game_ball", on_delete=models.CASCADE)
    game = models.ForeignKey(Game, related_name="players_ball", on_delete=models.CASCADE)
    ball = models.IntegerField(default=0)

    class Meta:
        db_table = "playersgameball"
        managed = False


class GazabdorPick(models.Model):
    actor = models.ForeignKey(GamePlayer, related_name="gazabdor_actions", on_delete=models.CASCADE)
    target = models.ForeignKey(GamePlayer, related_name="gazabdor_targets_back", on_delete=models.CASCADE)
    phase = models.ForeignKey(GamePhase, related_name="gazabdor_picks", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "gazabdorpick"
        managed = False
        unique_together = (("actor", "target", "phase"),)


class Vote(models.Model):
    id = models.BigAutoField(primary_key=True)
    phase = models.ForeignKey(GamePhase, related_name="votes", on_delete=models.CASCADE)
    voter = models.ForeignKey(GamePlayer, related_name="votes_given", on_delete=models.CASCADE)
    target = models.ForeignKey(GamePlayer, related_name="votes_received", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "vote"
        managed = False


class Action(models.Model):
    id = models.BigAutoField(primary_key=True)
    phase = models.ForeignKey(GamePhase, related_name="actions", on_delete=models.CASCADE)
    actor = models.ForeignKey(GamePlayer, related_name="actions_made", on_delete=models.CASCADE)
    target = models.ForeignKey(GamePlayer, related_name="actions_received", on_delete=models.CASCADE)
    action_type = models.CharField(max_length=20)  # kill, heal, investigate
    result = models.CharField(max_length=100, null=True, blank=True)
    with_miltiq = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "action"
        managed = False


class VoteLike(models.Model):
    id = models.BigAutoField(primary_key=True)
    phase = models.ForeignKey(GamePhase, related_name="vote_likes", on_delete=models.CASCADE)
    target = models.ForeignKey(GamePlayer, related_name="vote_target_likes", on_delete=models.CASCADE)
    voter = models.ForeignKey(GamePlayer, related_name="voted_likes", on_delete=models.CASCADE)
    is_like = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "votelike"
        managed = False


class GiveTopChat(models.Model):
    chat = models.ForeignKey(Chat, related_name="givetops", on_delete=models.CASCADE)
    gived_at = models.DateTimeField(auto_now_add=True)
    give_type = models.CharField(max_length=3)  # 1, 7, 30, 365

    class Meta:
        db_table = "givetopchat"
        managed = False


class Geroys(models.Model):
    user = models.ForeignKey(User, related_name="geroy", on_delete=models.CASCADE)
    name = models.CharField(max_length=70)
    patron = models.IntegerField(default=10)
    level = models.IntegerField(default=1)
    himoya = models.IntegerField(default=0)
    ball = models.IntegerField(default=0)

    class Meta:
        db_table = "geroys"
        managed = False


class GeroyAction(models.Model):
    id = models.BigAutoField(primary_key=True)
    geroy = models.ForeignKey(Geroys, related_name="actions", on_delete=models.CASCADE)
    action_type = models.CharField(max_length=20)  # attack, shield, skip
    target_user = models.ForeignKey(
        User, related_name="geroy_actions", on_delete=models.CASCADE, null=True, blank=True
    )
    phase = models.ForeignKey(GamePhase, related_name="geroy_actions", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "geroyaction"
        managed = False


# ── Settings ───────────────────────────────────────────────────────────────────

class GameSetTime(models.Model):
    id = models.BigAutoField(primary_key=True)
    chat_id = models.BigIntegerField(unique=True)
    day_time = models.BigIntegerField(default=45)
    night_time = models.BigIntegerField(default=45)
    vote_time = models.BigIntegerField(default=30)
    like_time = models.BigIntegerField(default=30)
    word_time = models.BigIntegerField(default=30)
    auto_start_time = models.IntegerField(default=0)  # 0 = Manual, otherwise seconds
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "game_sets_time"
        managed = False

    def __str__(self):
        return f"GameSet(chat_id={self.chat_id})"


class GameModeSet(models.Model):
    chat_id = models.BigIntegerField(unique=True)
    mode_name = models.CharField(max_length=20, default="classic")

    class Meta:
        db_table = "gamemodeset"
        managed = False


class GameSetListRoles(models.Model):
    chat_id = models.BigIntegerField(unique=True)
    blacklist = models.TextField(default="")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "gamesetlistroles"
        managed = False

    def get_blacklist(self):
        return [r for r in self.blacklist.split(",") if r]

    def set_blacklist(self, roles_list):
        self.blacklist = ",".join(sorted(set(roles_list)))

    def ban_role(self, role: str):
        r = set(self.get_blacklist())
        r.add(role)
        self.blacklist = ",".join(sorted(r))

    def unban_role(self, role: str):
        r = set(self.get_blacklist())
        r.discard(role)
        self.blacklist = ",".join(sorted(r))

    def is_banned(self, role: str) -> bool:
        return role in set(self.get_blacklist())


class GameSetPermissions(models.Model):
    chat_id = models.BigIntegerField(unique=True)
    anonim_ovoz_berish = models.BooleanField(default=False)
    leave_qilish = models.BooleanField(default=True)
    last_word_say = models.BooleanField(default=True)
    frendly_fire = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "gamesetpermissions"
        managed = False


class GameSetWeapons(models.Model):
    chat_id = models.BigIntegerField(unique=True)
    himoya = models.BooleanField(default=True)
    hujjat = models.BooleanField(default=True)
    qotildan_himoya = models.BooleanField(default=True)
    ovozdan_himoya = models.BooleanField(default=True)
    miltiq = models.BooleanField(default=True)
    doridan_himoya = models.BooleanField(default=True)
    slip_himoya = models.BooleanField(default=True)
    maska = models.BooleanField(default=True)
    geroy = models.BooleanField(default=True)
    active_role = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "gamesetweapons"
        managed = False


class GroupBalance(models.Model):
    chat_id = models.BigIntegerField(unique=True)
    balance = models.BigIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)
    last_reset_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "groupbalance"
        managed = False


class GroupGiveSet(models.Model):
    chat_id = models.BigIntegerField(unique=True)
    diamond = models.BigIntegerField(default=0)
    dollar = models.BigIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "groupgiveset"
        managed = False


class GroupMoreSet(models.Model):
    chat_id = models.BigIntegerField(unique=True)
    mafning_ovozi = models.BooleanField(default=True)
    adv_view = models.BooleanField(default=True)
    max_players = models.BigIntegerField(default=30)
    rollarni_guruhlash = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "groupmoreset"
        managed = False


class CommandPermissionsChat(models.Model):
    chat_id = models.BigIntegerField(unique=True)
    start_cmd = models.CharField(max_length=10)
    stop_cmd = models.CharField(max_length=10)
    game_cmd = models.CharField(max_length=10)
    top1_cmd = models.CharField(max_length=10)
    top7_cmd = models.CharField(max_length=10)
    top30_cmd = models.CharField(max_length=10)
    gtop1_cmd = models.CharField(max_length=10)
    gtop7_cmd = models.CharField(max_length=10)
    gtop30_cmd = models.CharField(max_length=10)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "commandpermissionschat"
        managed = False


class WriteGroupPermis(models.Model):
    chat_id = models.BigIntegerField(unique=True)
    night = models.CharField(max_length=20, default="alive")
    day = models.CharField(max_length=20, default="alive")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "writegrouppermis"
        managed = False


class GamingOnChat(models.Model):
    chat_id = models.BigIntegerField()
    can_gaming = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)
    bot_id = models.BigIntegerField(null=True, blank=True)

    class Meta:
        db_table = "gamingonchat"
        managed = False
        unique_together = (("chat_id", "bot_id"),)


class BlockGroups(models.Model):
    chat_id = models.BigIntegerField(unique=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "blockgrousp"  # original table name preserved
        managed = False


class NickList(models.Model):
    id = models.BigAutoField(primary_key=True)
    chat_id = models.BigIntegerField(unique=True)
    name = models.CharField(max_length=50)

    class Meta:
        db_table = "nicklist"
        managed = False


class NickModeSet(models.Model):
    id = models.BigAutoField(primary_key=True)
    chat_id = models.BigIntegerField(unique=True)
    selected_nicklist = models.ForeignKey(
        NickList, related_name="used_in_chats", on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        db_table = "nickmodeset"
        managed = False


class NickListItem(models.Model):
    id = models.BigAutoField(primary_key=True)
    nick_list = models.ForeignKey(NickList, related_name="nick_items", on_delete=models.CASCADE)
    nick_name = models.CharField(max_length=30)

    class Meta:
        db_table = "nicklistitem"
        managed = False


class WolfOrFoxSet(models.Model):
    chat_id = models.BigIntegerField(unique=True)
    wolf_or_fox = models.BooleanField(default=True)  # True = Bo'ri, False = Tulki
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "wolfortfoxset"
        managed = False


class TransfersReportsChat(models.Model):
    chat_id = models.BigIntegerField(unique=True)
    report_diamond = models.BooleanField(default=True)
    report_dollar = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "transfersreportschat"
        managed = False


class GameSetRoleConfig(models.Model):
    id = models.BigAutoField(primary_key=True)
    chat_id = models.BigIntegerField()
    player_count = models.IntegerField()  # 4 to 30
    roles_count = models.JSONField(default=dict)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "game_set_role_configs"
        managed = False
        unique_together = (("chat_id", "player_count"),)


class MafiaRolesCountSet(models.Model):
    chat_id = models.BigIntegerField(unique=True)
    maf3 = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "mafia_roles_count_set"
        managed = False


class ChangeDiamondGiveAway(models.Model):
    id = models.BigAutoField(primary_key=True)
    creator = models.ForeignKey(User, related_name="change_giveaways", on_delete=models.CASCADE)
    chat_id = models.BigIntegerField()
    message_id = models.BigIntegerField()
    amount = models.BigIntegerField()
    collected_users = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "changediamondgiveaway"
        managed = False


class OpenSandiqs(models.Model):
    user = models.ForeignKey(User, related_name="open_sandiqs", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    sandiq_type = models.CharField(max_length=20, default="mega")  # mega, super, etc.

    class Meta:
        db_table = "opensandiqs"
        managed = False


class GeroyMarket(models.Model):
    user = models.ForeignKey(User, related_name="geroy_market", on_delete=models.CASCADE)
    geroy = models.ForeignKey(Geroys, related_name="in_geroy_market", on_delete=models.CASCADE)
    price = models.BigIntegerField()
    is_sold = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "geroymarket"
        managed = False


class UserGameScore(models.Model):
    """Har bir o'yinchi uchun yakuniy ball."""
    user      = models.ForeignKey(User, related_name="game_scores", on_delete=models.CASCADE)
    game      = models.ForeignKey(Game, related_name="scores", on_delete=models.CASCADE)
    chat_id   = models.BigIntegerField()
    score     = models.IntegerField(default=0)
    is_win    = models.BooleanField(default=False)
    played_at = models.DateTimeField()

    class Meta:
        db_table = "user_game_score"
        managed = False
        unique_together = (("user", "game"),)


class GameEndStats(models.Model):
    """O'yin tugaganda umumiy statistika."""
    game             = models.OneToOneField(Game, related_name="end_stats", on_delete=models.CASCADE)
    chat_id          = models.BigIntegerField()
    total_players    = models.IntegerField(default=0)
    winners_count    = models.IntegerField(default=0)
    duration_minutes = models.IntegerField(default=0)
    mafia_kills      = models.IntegerField(default=0)
    kom_found        = models.IntegerField(default=0)
    doctor_saves     = models.IntegerField(default=0)
    played_at        = models.DateTimeField()

    class Meta:
        db_table = "game_end_stats"
        managed = False


class PlayerActionStat(models.Model):
    """O'yin ichida har bir o'yinchining action statistikasi."""
    game      = models.ForeignKey(Game, related_name="player_action_stats", on_delete=models.CASCADE)
    user      = models.ForeignKey(User, related_name="action_stats", on_delete=models.CASCADE)
    chat_id   = models.BigIntegerField()
    role      = models.CharField(max_length=70)
    is_win    = models.BooleanField(default=False)
    kills     = models.IntegerField(default=0)
    kom_finds = models.IntegerField(default=0)
    played_at = models.DateTimeField()

    class Meta:
        db_table = "player_action_stat"
        managed = False
        unique_together = (("game", "user"),)


class ChatRoleOrder(models.Model):
    """Guruh uchun rol tartibini saqlaydi — botdagi default tartibni o'zgartirish imkoni."""
    chat_id = models.BigIntegerField(unique=True)
    roles = models.JSONField(default=list)   # ["DON", "KOMISSAR", ...]
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "chat_role_order"
        managed = True
