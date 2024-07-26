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
from pathlib import Path

import phonenumbers
from django import template
from django.template import TemplateSyntaxError
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe
from django.utils.translation import ngettext

from core.markdown import markdown as md
from core.scss.processor import process_scss_path

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
    except phonenumbers.NumberParseException as e:
        return value


@register.filter(name="truncate_time")
def truncate_time(value, time_unit):
    """Remove everything in the time format lower than the specified unit.

    Args:
        value: the value to truncate
        time_unit: the lowest unit to display
    """
    value = str(value)
    return {
        "millis": lambda: value.split(".")[0],
        "seconds": lambda: value.rsplit(":", maxsplit=1)[0],
        "minutes": lambda: value.split(":", maxsplit=1)[0],
        "hours": lambda: value.rsplit(" ")[0],
    }[time_unit]()


@register.filter(name="format_timedelta")
def format_timedelta(value: datetime.timedelta) -> str:
    days = value.days
    if days == 0:
        return str(value)
    remainder = value - datetime.timedelta(days=days)
    return ngettext(
        "%(nb_days)d day, %(remainder)s", "%(nb_days)d days, %(remainder)s", days
    ) % {"nb_days": days, "remainder": str(remainder)}


@register.simple_tag()
def scss(path):
    """Return path of the corresponding css file after compilation."""
    path = Path(path)
    if path.suffix != ".scss":
        raise TemplateSyntaxError("`scss` tag has been called with a non-scss file")
    return process_scss_path(path)
