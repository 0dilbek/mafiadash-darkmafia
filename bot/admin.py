from django.contrib import admin
from .models import User, BlockedUser, Profile, ActiveRole, Transfer, VipUser, Para, Chat, AdminLoginToken


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_id', 'full_name', 'mention', 'is_bot')
    search_fields = ('user_id', 'full_name', 'mention')
    list_filter = ('is_bot',)


@admin.register(BlockedUser)
class BlockedUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'created_at')
    search_fields = ('user__full_name', 'user__user_id')


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'dollar', 'diamond', 'wins', 'games_count')
    search_fields = ('user__full_name', 'user__user_id')
    list_filter = ('on_himoya', 'on_miltiq', 'on_maska')


@admin.register(ActiveRole)
class ActiveRoleAdmin(admin.ModelAdmin):
    list_display = ('id', 'profile', 'role', 'is_active', 'created_at')
    list_filter = ('role', 'is_active')


@admin.register(Transfer)
class TransferAdmin(admin.ModelAdmin):
    list_display = ('id', 'from_user', 'to_user', 'amount', 'type', 'created_at')
    search_fields = ('from_user__full_name', 'to_user__full_name')
    list_filter = ('type',)


@admin.register(VipUser)
class VipUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'created_at', 'updated_at')
    search_fields = ('user__full_name', 'user__user_id')


@admin.register(Para)
class ParaAdmin(admin.ModelAdmin):
    list_display = ('id', 'user1', 'user2', 'created_at')


@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ('id', 'chat_id', 'title', 'type', 'created_at')
    search_fields = ('title', 'chat_id')
    list_filter = ('type',)


@admin.register(AdminLoginToken)
class AdminLoginTokenAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_id', 'token', 'created_at', 'expires_at', 'is_valid')
    search_fields = ('user_id',)
    readonly_fields = ('token', 'created_at')

    def is_valid(self, obj):
        return obj.is_valid()
    is_valid.boolean = True
    is_valid.short_description = 'Amal qiladi'
