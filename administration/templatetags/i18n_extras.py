from django import template
from django.utils.translation import gettext as _

register = template.Library()

@register.filter(name='t')
def translate_db_value(value):
    """Dynamic translation filter for database model values, status badges, and lookup text."""
    if value is None or value == "":
        return ""
    val_str = str(value).strip()
    return _(val_str)
