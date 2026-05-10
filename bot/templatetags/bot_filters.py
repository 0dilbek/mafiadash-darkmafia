from django import template
from datetime import timedelta

register = template.Library()

@register.filter
def tz5(value):
    """Vaqtinchalik: UTC vaqtga +5 soat qo'shadi (Asia/Tashkent)."""
    if value is None:
        return value
    try:
        return value + timedelta(hours=5)
    except (TypeError, AttributeError):
        return value
