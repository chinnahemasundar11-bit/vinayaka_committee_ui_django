from django import template
from accounts.permissions import has_module_action_right

register = template.Library()

@register.simple_tag(takes_context=True)
def has_right(context, module_code, right_code):
    """
    Template tag checking if current user has the specified action right for a module.
    Usage:
    {% load permission_tags %}
    {% has_right 'FUNDS_RECEIVED' 'add' as can_add %}
    {% if can_add %} ... {% endif %}
    """
    request = context.get("request")
    if not request or not hasattr(request, "user"):
        return False
    return has_module_action_right(request.user, module_code, right_code)


@register.simple_tag(takes_context=True)
def has_module_access_tag(context, module_code):
    """
    Template tag checking if current user has access to the specified module.
    Usage:
    {% load permission_tags %}
    {% has_module_access_tag 'EXPENSES' as has_expenses_access %}
    """
    from accounts.permissions import has_module_access
    request = context.get("request")
    if not request or not hasattr(request, "user"):
        return False
    return has_module_access(request.user, module_code)

