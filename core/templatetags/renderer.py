from django import template
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe
from django.utils.html import escape

from core.markdown import markdown as md

register = template.Library()

@register.filter(is_safe=False)
@stringfilter
def markdown(text):
    return mark_safe(md(escape(text)))

@register.filter()
@stringfilter
def datetime_format_python_to_PHP(python_format_string):
    """
    Given a python datetime format string, attempts to convert it to the nearest PHP datetime format string possible.
    """
    python2PHP = {"%a": "D", "%a": "D", "%A": "l", "%b": "M", "%B": "F", "%c": "", "%d": "d", "%H": "H", "%I": "h", "%j": "z", "%m": "m", "%M": "i", "%p": "A", "%S": "s", "%U": "", "%w": "w", "%W": "W", "%x": "", "%X": "", "%y": "y", "%Y": "Y", "%Z": "e" }

    php_format_string = python_format_string
    for py, php in python2PHP.items():
        php_format_string = php_format_string.replace(py, php)
    return php_format_string


