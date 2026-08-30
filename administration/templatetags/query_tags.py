from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def param_replace(context, **kwargs):
    """
    Template tag to preserve current GET search parameters while updating pagination page numbers.
    Usage: href="?{% param_replace page=2 %}"
    """
    d = context['request'].GET.copy()
    for k, v in kwargs.items():
        d[k] = v
    for k in list(d.keys()):
        if not d[k]:
            del d[k]
    return d.urlencode()
