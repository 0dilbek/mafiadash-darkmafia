from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('api/chart-data/', views.dashboard_chart_data, name='chart_data'),

    path('users/', views.users_list, name='users'),
    path('users/<int:user_id>/', views.user_detail, name='user_detail'),

    path('transfers/', views.transfers_list, name='transfers'),
    path('vip/', views.vip_list, name='vip'),
    path('top/', views.top_players, name='top'),

    path('blocked/', views.blocked_list, name='blocked'),
    path('blocked/block/', views.block_user, name='block_user'),
    path('blocked/unblock/<int:blocked_id>/', views.unblock_user, name='unblock_user'),

    path('giveaways/', views.giveaways_list, name='giveaways'),

    path('chats/', views.chats_list, name='chats'),
    path('chats/<int:pk>/toggle-block/', views.chat_toggle_block, name='chat_toggle_block'),
    path('chats/<int:pk>/clear-balance/', views.chat_clear_balance, name='chat_clear_balance'),

    path('games/', views.active_games, name='active_games'),
    path('games/<int:pk>/', views.game_detail, name='game_detail'),

    path('auth/login/', views.magic_login, name='magic_login'),
    path('auth/error/', views.magic_login_error, name='magic_login_error'),

    path('group/<uuid:token>/', views.panel_entry, name='panel_entry'),
    path('group/', views.group_dashboard, name='group_dashboard'),
    path('group/roles/', views.group_role_order, name='group_role_order'),
    path('api/group-chart/', views.group_chart_data, name='group_chart_data'),

    path('api/generate-link/', views.generate_panel_link, name='generate_panel_link'),
]
