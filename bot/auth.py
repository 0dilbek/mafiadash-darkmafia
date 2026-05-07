"""
Ikki xil autentifikatsiya dekoratori:

  @admin_required    — eski Django auth (username/password) tekshiradi
                       Mavjud admin dashboard viewlari uchun.

  @tg_login_required — magic-link token bilan ochilgan session tekshiradi
                       Kelajakdagi user-facing viewlar uchun.
"""
from functools import wraps
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required as _django_login_required


# Admin panel uchun — Django auth sistemasi (o'zgarishsiz)
admin_required = _django_login_required


def tg_login_required(view_func):
    """
    Magic-link orqali kirgan foydalanuvchilar uchun decorator.
    Session'da 'tg_authenticated' bo'lmasa magic_error sahifasiga yo'naltiradi.
    Django auth.User bilan hech qanday aloqasi yo'q.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get('tg_authenticated'):
            return redirect('magic_login_error')
        return view_func(request, *args, **kwargs)
    return wrapper
