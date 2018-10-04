# -*- coding:utf-8 -*
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

import phonenumbers

from django import template
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe
from core.scss.processor import ScssProcessor

from core.markdown import markdown as md

register = template.Library()


@register.filter(is_safe=False)
@stringfilter
def markdown(text):
    return mark_safe('<div class="markdown">%s</div>' % md(text))


@register.filter(name="phonenumber")
def phonenumber(value, country="FR", format=phonenumbers.PhoneNumberFormat.NATIONAL):
    """
    This filter is kindly borrowed from https://github.com/foundertherapy/django-phonenumber-filter
    """
    value = str(value)
    try:
        parsed = phonenumbers.parse(value, country)
        return phonenumbers.format_number(parsed, format)
    except phonenumbers.NumberParseException as e:
        return value


@register.filter()
@stringfilter
def datetime_format_python_to_PHP(python_format_string):
    """
    Given a python datetime format string, attempts to convert it to the nearest PHP datetime format string possible.
    """
    python2PHP = {
        "%a": "D",
        "%a": "D",
        "%A": "l",
        "%b": "M",
        "%B": "F",
        "%c": "",
        "%d": "d",
        "%H": "H",
        "%I": "h",
        "%j": "z",
        "%m": "m",
        "%M": "i",
        "%p": "A",
        "%S": "s",
        "%U": "",
        "%w": "w",
        "%W": "W",
        "%x": "",
        "%X": "",
        "%y": "y",
        "%Y": "Y",
        "%Z": "e",
    }

    php_format_string = python_format_string
    for py, php in python2PHP.items():
        php_format_string = php_format_string.replace(py, php)
    return php_format_string


@register.simple_tag()
def scss(path):
    """
        Return path of the corresponding css file after compilation
    """
    processor = ScssProcessor(path)
    return processor.get_converted_scss()
