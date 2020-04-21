from django.template.exceptions import TemplateSyntaxError
from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()


# arg should be of the form "|foo|bar" where the first character is the
# separator between old and new in value.replace(old, new)
@register.filter
@stringfilter
def replace(value, arg):
    # s.replace('', '') == s so len(arg) == 2 is fine
    if len(arg) < 2:
        raise TemplateSyntaxError("badly formatted argument")

    arg = arg.split(arg[0])

    if len(arg) != 3:
        raise TemplateSyntaxError("badly formatted argument")

    return value.replace(arg[1], arg[2])
