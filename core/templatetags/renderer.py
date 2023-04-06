# -*- coding:utf-8 -*-
#
# Copyright 2023 © AE UTBM
# ae@utbm.fr / ae.info@utbm.fr
# All contributors are listed in the CONTRIBUTORS file.
#
# This file is part of the website of the UTBM Student Association (AE UTBM),
# https://ae.utbm.fr.
#
# You can find the whole source code at https://github.com/ae-utbm/sith3
#
# LICENSED UNDER THE GNU GENERAL PUBLIC LICENSE VERSION 3 (GPLv3)
# SEE : https://raw.githubusercontent.com/ae-utbm/sith3/master/LICENSE
# OR WITHIN THE LOCAL FILE "LICENSE"
#
# PREVIOUSLY LICENSED UNDER THE MIT LICENSE,
# SEE : https://raw.githubusercontent.com/ae-utbm/sith3/master/LICENSE.old
# OR WITHIN THE LOCAL FILE "LICENSE.old"
#

import datetime

import phonenumbers
from django import template
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe
from django.utils.translation import ngettext

from core.markdown import markdown as md
from core.scss.processor import ScssProcessor

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


@register.filter(name="truncate_time")
def truncate_time(value, time_unit):
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
    """
    Return path of the corresponding css file after compilation
    """
    processor = ScssProcessor(path)
    return processor.get_converted_scss()
