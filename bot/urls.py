from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    path('api/chart-data/', views.dashboard_chart_data, name='chart_data'),

    # Foydalanuvchilar
    path('users/', views.users_list, name='users'),
    path('users/<int:user_id>/', views.user_detail, name='user_detail'),

    # Moliya
    path('transfers/', views.transfers_list, name='transfers'),
    path('vip/', views.vip_list, name='vip'),
    path('top/', views.top_players, name='top'),

    # Bloklash
    path('blocked/', views.blocked_list, name='blocked'),
    path('blocked/block/', views.block_user, name='block_user'),
    path('blocked/unblock/<int:blocked_id>/', views.unblock_user, name='unblock_user'),

    # Giveaway
    path('giveaways/', views.giveaways_list, name='giveaways'),

    # Chatlar
    path('chats/', views.chats_list, name='chats'),
    path('chats/<int:pk>/toggle-block/', views.chat_toggle_block, name='chat_toggle_block'),
    path('chats/<int:pk>/clear-balance/', views.chat_clear_balance, name='chat_clear_balance'),

    # O'yinlar
    path('games/', views.active_games, name='active_games'),
    path('games/<int:pk>/', views.game_detail, name='game_detail'),
]
