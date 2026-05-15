from django.urls import path
from . import views
from bot import views as bot_views

urlpatterns = [
    # Landing
    path('', views.landing, name='landing'),

    # Guruh panel (magic-link auth)
    path('auth/login/',  bot_views.magic_login,       name='magic_login'),
    path('auth/error/',  bot_views.magic_login_error, name='magic_login_error'),
    path('group/<uuid:token>/', bot_views.panel_entry,       name='panel_entry'),
    path('group/',              bot_views.group_dashboard,   name='group_dashboard'),
    path('group/roles/',        bot_views.group_role_order,  name='group_role_order'),

    # API
    path('api/group-chart/',   bot_views.group_chart_data,   name='group_chart_data'),
    path('api/generate-link/', bot_views.generate_panel_link, name='generate_panel_link'),

    # Debug (vaqtinchalik)
    path('api/debug-stats/', views.debug_stats, name='debug_stats'),
]
