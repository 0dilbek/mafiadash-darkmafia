from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),

    # Admin panel autentifikatsiya
    path('panel/login/',  auth_views.LoginView.as_view(template_name='bot/login.html'), name='login'),
    path('panel/logout/', auth_views.LogoutView.as_view(next_page='login'),             name='logout'),

    # Admin panel (login talab qilinadi)
    path('panel/', include('bot.urls')),

    # Ochiq qism: landing + guruh panel + API
    path('', include('main.urls')),
]
