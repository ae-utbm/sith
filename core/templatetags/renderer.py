import mistune
from django import template
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe
from django.utils.html import escape


register = template.Library()

@register.filter(is_safe=False)
@stringfilter
def markdown(text):
    md = mistune.Markdown()
    return mark_safe(md(escape(text)))



