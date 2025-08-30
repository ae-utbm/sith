#
# Copyright 2023 © AE UTBM
# ae@utbm.fr / ae.info@utbm.fr
#
# This file is part of the website of the UTBM Student Association (AE UTBM),
# https://ae.utbm.fr.
#
# You can find the source code of the website at https://github.com/ae-utbm/sith
#
# LICENSED UNDER THE GNU GENERAL PUBLIC LICENSE VERSION 3 (GPLv3)
# SEE : https://raw.githubusercontent.com/ae-utbm/sith/master/LICENSE
# OR WITHIN THE LOCAL FILE "LICENSE"
#
#
from dataclasses import dataclass
from datetime import date, timedelta

# Image utils
from io import BytesIO
from typing import Any, Final, Unpack

import PIL
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import UploadedFile
from django.db import models
from django.forms import BaseForm
from django.http import Http404, HttpRequest
from django.shortcuts import get_list_or_404
from django.template.loader import render_to_string
from django.utils.safestring import SafeString
from django.utils.timezone import localdate
from PIL import ExifTags
from PIL.Image import Image, Resampling

RED_PIXEL_PNG: Final[bytes] = (
    b"\x89\x50\x4e\x47\x0d\x0a\x1a\x0a\x00\x00\x00\x0d\x49\x48\x44\x52"
    b"\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90\x77\x53"
    b"\xde\x00\x00\x00\x0c\x49\x44\x41\x54\x08\xd7\x63\xf8\xcf\xc0\x00"
    b"\x00\x03\x01\x01\x00\x18\xdd\x8d\xb0\x00\x00\x00\x00\x49\x45\x4e"
    b"\x44\xae\x42\x60\x82"
)
"""A single red pixel, in PNG format.

Can be used in tests and in dev, when there is a need
to generate a dummy image that is considered valid nonetheless
"""


@dataclass
class FormFragmentTemplateData[T: BaseForm]:
    """Dataclass used to pre-render form fragments"""

    form: T
    template: str
    context: dict[str, Any]

    def render(self, request: HttpRequest) -> SafeString:
        # Request is needed for csrf_tokens
        return render_to_string(
            self.template, context={"form": self.form, **self.context}, request=request
        )


def get_start_of_semester(today: date | None = None) -> date:
    """Return the date of the start of the semester of the given date.
    If no date is given, return the start date of the current semester.

    The current semester is computed as follows:

    - If the date is between 15/08 and 31/12  => Autumn semester.
    - If the date is between 01/01 and 15/02  => Autumn semester of the previous year.
    - If the date is between 15/02 and 15/08  => Spring semester

    Args:
        today: the date to use to compute the semester. If None, use today's date.

    Returns:
        the date of the start of the semester
    """
    if today is None:
        today = localdate()

    autumn = date(today.year, *settings.SITH_SEMESTER_START_AUTUMN)
    spring = date(today.year, *settings.SITH_SEMESTER_START_SPRING)

    if today >= autumn:  # between 15/08 (included) and 31/12 -> autumn semester
        return autumn
    if today >= spring:  # between 15/02 (included) and 15/08 -> spring semester
        return spring
    # between 01/01 and 15/02 -> autumn semester of the previous year
    return autumn.replace(year=autumn.year - 1)


def get_end_of_semester(today: date | None = None):
    """Return the date of the end of the semester of the given date.
    If no date is given, return the end date of the current semester.
    """
    # the algorithm is simple, albeit somewhat imprecise :
    # 1. get the start of the next semester
    # 2. Remove a month and a half for the autumn semester (summer holidays)
    #    and 28 days for spring semester (february holidays)
    if today is None:
        today = localdate()
    semester_start = get_start_of_semester(today + timedelta(days=365 // 2))
    if semester_start.month == settings.SITH_SEMESTER_START_AUTUMN[0]:
        return semester_start - timedelta(days=45)
    return semester_start - timedelta(days=28)


def get_semester_code(d: date | None = None) -> str:
    """Return the semester code of the given date.
    If no date is given, return the semester code of the current semester.

    The semester code is an upper letter (A for autumn, P for spring),
    followed by the last two digits of the year.
    For example, the autumn semester of 2018 is "A18".

    Args:
        d: the date to use to compute the semester. If None, use today's date.

    Returns:
        the semester code corresponding to the given date
    """
    if d is None:
        d = localdate()

    start = get_start_of_semester(d)

    if (start.month, start.day) == settings.SITH_SEMESTER_START_AUTUMN:
        return "A" + str(start.year)[-2:]
    return "P" + str(start.year)[-2:]


def is_image(file: UploadedFile):
    try:
        im = PIL.Image.open(file.file)
        im.verify()
        # go back to the start of the file, without closing it.
        # Otherwise, further checks on django side will fail
        file.seek(0)
    except PIL.UnidentifiedImageError:
        return False
    return True


def resize_image(
    im: Image, edge: int, img_format: str, *, optimize: bool = True
) -> ContentFile:
    """Resize an image to fit the given edge length and format.

    Args:
        im: the image to resize
        edge: the length that the greater side of the resized image should have
        img_format: the target format of the image ("JPEG", "PNG", "WEBP"...)
        optimize: Should the resized image be optimized ?
    """
    (w, h) = im.size
    ratio = edge / max(w, h)
    (width, height) = int(w * ratio), int(h * ratio)
    return resize_image_explicit(im, (width, height), img_format, optimize=optimize)


def resize_image_explicit(
    im: Image, size: tuple[int, int], img_format: str, *, optimize: bool = True
) -> ContentFile:
    """Resize an image to the given size and format.

    Args:
        im: the image to resize
        size: the target dimension, as a [width, height] tuple
        img_format: the target format of the image ("JPEG", "PNG", "WEBP"...)
        optimize: Should the resized image be optimized ?
    """
    img_format = img_format.upper()
    content = BytesIO()
    # use the lanczos filter for antialiasing and discard the alpha channel
    if size != im.size:
        im = im.resize((size[0], size[1]), Resampling.LANCZOS)
    if img_format == "JPEG":
        # converting an image with an alpha channel to jpeg would cause a crash
        im = im.convert("RGB")
    try:
        im.save(fp=content, format=img_format, optimize=optimize)
    except IOError:
        PIL.ImageFile.MAXBLOCK = im.size[0] * im.size[1]
        im.save(fp=content, format=img_format, optimize=optimize)
    return ContentFile(content.getvalue())


def exif_auto_rotate(image):
    for orientation in ExifTags.TAGS:
        if ExifTags.TAGS[orientation] == "Orientation":
            break
    exif = dict(image._getexif().items())

    if exif[orientation] == 3:
        image = image.rotate(180, expand=True)
    elif exif[orientation] == 6:
        image = image.rotate(270, expand=True)
    elif exif[orientation] == 8:
        image = image.rotate(90, expand=True)

    return image


def get_client_ip(request: HttpRequest) -> str | None:
    headers = (
        "X_FORWARDED_FOR",  # Common header for proixes
        "FORWARDED",  # Standard header defined by RFC 7239.
        "REMOTE_ADDR",  # Default IP Address (direct connection)
    )
    for header in headers:
        if (ip := request.META.get(header)) is not None:
            return ip

    return None


Filterable = models.Model | models.QuerySet | models.Manager
ListFilter = dict[str, list | tuple | set]


def get_list_exact_or_404(klass: Filterable, **kwargs: Unpack[ListFilter]) -> list:
    """Use filter() to return a list of objects from a list of unique keys (like ids)
    or raises Http404 if the list has not the same length as the given one.

    Work like `get_object_or_404()` but for lists of objects, with some caveats :

    - The filter must be a list, a tuple or a set.
    - There can't be more than exactly one filter.
    - There must be no duplicate in the filter.
    - The filter should consist in unique keys (like ids), or it could fail randomly.

    klass may be a Model, Manager, or QuerySet object. All other passed
    arguments and keyword arguments are used in the filter() query.

    Raises:
        Http404: If the list is empty or doesn't have as many elements as the keys list.
        ValueError: If the first argument is not a Model, Manager, or QuerySet object.
        ValueError: If more than one filter is passed.
        TypeError: If the given filter is not a list, a tuple or a set.

    Examples:
        Get all the products with ids 1, 2, 3: ::

            products = get_list_exact_or_404(Product, id__in=[1, 2, 3])

        Don't work with duplicate ids: ::

            products = get_list_exact_or_404(Product, id__in=[1, 2, 3, 3])
            # Raises Http404: "The list of keys must contain no duplicates."
    """
    if len(kwargs) > 1:
        raise ValueError("get_list_exact_or_404() only accepts one filter.")
    key, list_filter = next(iter(kwargs.items()))
    if not isinstance(list_filter, (list, tuple, set)):
        raise TypeError(
            f"The given filter must be a list, a tuple or a set, not {type(list_filter)}"
        )
    if len(list_filter) != len(set(list_filter)):
        raise ValueError("The list of keys must contain no duplicates.")
    kwargs = {key: list_filter}
    obj_list = get_list_or_404(klass, **kwargs)
    if len(obj_list) != len(list_filter):
        raise Http404(
            "The given list of keys doesn't match the number of objects found."
            f"Expected {len(list_filter)} items, got {len(obj_list)}."
        )
    return obj_list
