#
# Copyright 2016,2017
# - Skia <skia@libskia.so>
# - Sli <antoine@bartuccio.fr>
#
# Ce fichier fait partie du site de l'Association des Étudiants de l'UTBM,
# http://ae.utbm.fr.
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License a published by the Free Software
# Foundation; either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Sofware Foundation, Inc., 59 Temple
# Place - Suite 330, Boston, MA 02111-1307, USA.
#
#

import datetime

import phonenumbers
from django import template
from django.forms import BoundField
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe
from django.utils.translation import ngettext

from core.markdown import markdown as md

register = template.Library()


@register.filter(is_safe=False)
@stringfilter
def markdown(text):
    return mark_safe('<div class="markdown">%s</div>' % md(text))


@register.filter(name="phonenumber")
def phonenumber(
    value, country="FR", number_format=phonenumbers.PhoneNumberFormat.NATIONAL
):
    # collectivised from https://github.com/foundertherapy/django-phonenumber-filter.
    value = str(value)
    try:
        parsed = phonenumbers.parse(value, country)
        return phonenumbers.format_number(parsed, number_format)
    except phonenumbers.NumberParseException:
        return value


@register.filter(name="format_timedelta")
def format_timedelta(value: datetime.timedelta) -> str:
    value = value - datetime.timedelta(microseconds=value.microseconds)
    days = value.days
    if days == 0:
        return str(value)
    remainder = value - datetime.timedelta(days=days)
    return ngettext(
        "%(nb_days)d day, %(remainder)s",
        "%(nb_days)d days, %(remainder)s",
        days,
    ) % {"nb_days": days, "remainder": str(remainder)}


@register.filter(name="add_attr")
def add_attr(field: BoundField, attr: str):
    """Add attributes to a form field directly in the template.

    Attributes are `key=value` pairs, separated by commas.

    Example:
        ```jinja
        <form x-data="{alpineField: null}">
            {{ form.field|add_attr("x-model=alpineField") }}
        </form>
        ```

        will render :
        ```html
        <form x-data="{alpineField: null}">
            <input type="..." x-model="alpineField">
        </form>
        ```

    Notes:
        Doing this gives the same result as setting the attribute
        directly in the python code.
        However, sometimes there are attributes that are tightly
        coupled to the frontend logic (like Alpine variables)
        and that shouldn't be declared outside of it.
    """
    attrs = {}
    definition = attr.split(",")

    for d in definition:
        if "=" not in d:
            attrs["class"] = d
        else:
            key, val = d.split("=")
            attrs[key] = val

    return field.as_widget(attrs=attrs)
