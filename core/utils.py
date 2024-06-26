# -*- coding:utf-8 -*
#
# Copyright 2023 © AE UTBM
# ae@utbm.fr / ae.info@utbm.fr
#
# This file is part of the website of the UTBM Student Association (AE UTBM),
# https://ae.utbm.fr.
#
# You can find the source code of the website at https://github.com/ae-utbm/sith3
#
# LICENSED UNDER THE GNU GENERAL PUBLIC LICENSE VERSION 3 (GPLv3)
# SEE : https://raw.githubusercontent.com/ae-utbm/sith3/master/LICENSE
# OR WITHIN THE LOCAL FILE "LICENSE"
#
#

import os
import re
import subprocess
from datetime import date

# Image utils
from io import BytesIO
from typing import Optional

import PIL
from django.conf import settings
from django.core.files.base import ContentFile
from django.utils import timezone
from PIL import ExifTags
from PIL.Image import Resampling


def get_git_revision_short_hash() -> str:
    """
    Return the short hash of the current commit
    """
    try:
        output = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"])
        if isinstance(output, bytes):
            return output.decode("ascii").strip()
        return output.strip()
    except subprocess.CalledProcessError:
        return ""


def get_start_of_semester(today: Optional[date] = None) -> date:
    """
    Return the date of the start of the semester of the given date.
    If no date is given, return the start date of the current semester.

    The current semester is computed as follows:

    - If the date is between 15/08 and 31/12  => Autumn semester.
    - If the date is between 01/01 and 15/02  => Autumn semester of the previous year.
    - If the date is between 15/02 and 15/08  => Spring semester

    :param today: the date to use to compute the semester. If None, use today's date.
    :return: the date of the start of the semester
    """
    if today is None:
        today = timezone.now().date()

    autumn = date(today.year, *settings.SITH_SEMESTER_START_AUTUMN)
    spring = date(today.year, *settings.SITH_SEMESTER_START_SPRING)

    if today >= autumn:  # between 15/08 (included) and 31/12 -> autumn semester
        return autumn
    if today >= spring:  # between 15/02 (included) and 15/08 -> spring semester
        return spring
    # between 01/01 and 15/02 -> autumn semester of the previous year
    return autumn.replace(year=autumn.year - 1)


def get_semester_code(d: Optional[date] = None) -> str:
    """
    Return the semester code of the given date.
    If no date is given, return the semester code of the current semester.

    The semester code is an upper letter (A for autumn, P for spring),
    followed by the last two digits of the year.
    For example, the autumn semester of 2018 is "A18".

    :param d: the date to use to compute the semester. If None, use today's date.
    :return: the semester code corresponding to the given date
    """
    if d is None:
        d = timezone.now().date()

    start = get_start_of_semester(d)

    if (start.month, start.day) == settings.SITH_SEMESTER_START_AUTUMN:
        return "A" + str(start.year)[-2:]
    return "P" + str(start.year)[-2:]


def file_exist(path):
    return os.path.exists(path)


def scale_dimension(width, height, long_edge):
    if width > height:
        ratio = long_edge * 1.0 / width
    else:
        ratio = long_edge * 1.0 / height
    return int(width * ratio), int(height * ratio)


def resize_image(im, edge, format):
    (w, h) = im.size
    (width, height) = scale_dimension(w, h, long_edge=edge)
    content = BytesIO()
    # use the lanczos filter for antialiasing
    im = im.resize((width, height), Resampling.LANCZOS)
    try:
        im.save(
            fp=content,
            format=format.upper(),
            quality=90,
            optimize=True,
            progressive=True,
        )
    except IOError:
        PIL.ImageFile.MAXBLOCK = im.size[0] * im.size[1]
        im.save(
            fp=content,
            format=format.upper(),
            quality=90,
            optimize=True,
            progressive=True,
        )
    return ContentFile(content.getvalue())


def exif_auto_rotate(image):
    for orientation in ExifTags.TAGS.keys():
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


def doku_to_markdown(text):
    """This is a quite correct doku translator"""
    text = re.sub(
        r"([^:]|^)\/\/(.*?)\/\/", r"*\2*", text
    )  # Italic (prevents protocol:// conflict)
    text = re.sub(
        r"<del>(.*?)<\/del>", r"~~\1~~", text, flags=re.DOTALL
    )  # Strike (may be multiline)
    text = re.sub(
        r"<sup>(.*?)<\/sup>", r"^\1^", text
    )  # Superscript (multiline not supported, because almost never used)
    text = re.sub(r"<sub>(.*?)<\/sub>", r"_\1_", text)  # Subscript (idem)

    text = re.sub(r"^======(.*?)======", r"#\1", text, flags=re.MULTILINE)  # Titles
    text = re.sub(r"^=====(.*?)=====", r"##\1", text, flags=re.MULTILINE)
    text = re.sub(r"^====(.*?)====", r"###\1", text, flags=re.MULTILINE)
    text = re.sub(r"^===(.*?)===", r"####\1", text, flags=re.MULTILINE)
    text = re.sub(r"^==(.*?)==", r"#####\1", text, flags=re.MULTILINE)
    text = re.sub(r"^=(.*?)=", r"######\1", text, flags=re.MULTILINE)

    text = re.sub(r"<nowiki>", r"<nosyntax>", text)
    text = re.sub(r"</nowiki>", r"</nosyntax>", text)
    text = re.sub(r"<code>", r"```\n", text)
    text = re.sub(r"</code>", r"\n```", text)
    text = re.sub(r"article://", r"page://", text)
    text = re.sub(r"dfile://", r"file://", text)

    i = 1
    for fn in re.findall(r"\(\((.*?)\)\)", text):  # Footnotes
        text = re.sub(r"\(\((.*?)\)\)", r"[^%s]" % i, text, count=1)
        text += "\n[^%s]: %s\n" % (i, fn)
        i += 1

    text = re.sub(r"\\{2,}[\s]", r"   \n", text)  # Carriage return

    text = re.sub(r"\[\[(.*?)\|(.*?)\]\]", r"[\2](\1)", text)  # Links
    text = re.sub(r"\[\[(.*?)\]\]", r"[\1](\1)", text)  # Links 2
    text = re.sub(r"{{(.*?)\|(.*?)}}", r'![\2](\1 "\2")', text)  # Images
    text = re.sub(r"{{(.*?)(\|(.*?))?}}", r'![\1](\1 "\1")', text)  # Images 2
    text = re.sub(
        r"{\[(.*?)(\|(.*?))?\]}", r"[\1](\1)", text
    )  # Video (transform to classic links, since we can't integrate them)

    text = re.sub(r"###(\d*?)###", r"[[[\1]]]", text)  # Progress bar

    text = re.sub(
        r"(\n +[^* -][^\n]*(\n +[^* -][^\n]*)*)", r"```\1\n```", text, flags=re.DOTALL
    )  # Block code without lists

    text = re.sub(r"( +)-(.*)", r"1.\2", text)  # Ordered lists

    new_text = []
    quote_level = 0
    for line in text.splitlines():  # Tables and quotes
        enter = re.finditer(r"\[quote(=(.+?))?\]", line)
        quit = re.finditer(r"\[/quote\]", line)
        if re.search(r"\A\s*\^(([^\^]*?)\^)*", line):  # Table part
            line = line.replace("^", "|")
            new_text.append("> " * quote_level + line)
            new_text.append(
                "> " * quote_level + "|---|"
            )  # Don't keep the text alignement in tables it's really too complex for what it's worth
        elif enter or quit:  # Quote part
            for quote in enter:  # Enter quotes (support multiple at a time)
                quote_level += 1
                try:
                    new_text.append("> " * quote_level + "##### " + quote.group(2))
                except:
                    new_text.append("> " * quote_level)
                line = line.replace(quote.group(0), "")
            final_quote_level = quote_level  # Store quote_level to use at the end, since it will be modified during quit iteration
            final_newline = False
            for quote in quit:  # Quit quotes (support multiple at a time)
                line = line.replace(quote.group(0), "")
                quote_level -= 1
                final_newline = True
            new_text.append("> " * final_quote_level + line)  # Finally append the line
            if final_newline:
                new_text.append(
                    "\n"
                )  # Add a new line to ensure the separation between the quote and the following text
        else:
            new_text.append(line)

    return "\n".join(new_text)


def bbcode_to_markdown(text):
    """This is a very basic BBcode translator"""
    text = re.sub(r"\[b\](.*?)\[\/b\]", r"**\1**", text, flags=re.DOTALL)  # Bold
    text = re.sub(r"\[i\](.*?)\[\/i\]", r"*\1*", text, flags=re.DOTALL)  # Italic
    text = re.sub(r"\[u\](.*?)\[\/u\]", r"__\1__", text, flags=re.DOTALL)  # Underline
    text = re.sub(
        r"\[s\](.*?)\[\/s\]", r"~~\1~~", text, flags=re.DOTALL
    )  # Strike (may be multiline)
    text = re.sub(
        r"\[strike\](.*?)\[\/strike\]", r"~~\1~~", text, flags=re.DOTALL
    )  # Strike 2

    text = re.sub(r"article://", r"page://", text)
    text = re.sub(r"dfile://", r"file://", text)

    text = re.sub(r"\[url=(.*?)\](.*)\[\/url\]", r"[\2](\1)", text)  # Links
    text = re.sub(r"\[url\](.*)\[\/url\]", r"\1", text)  # Links 2
    text = re.sub(r"\[img\](.*)\[\/img\]", r'![\1](\1 "\1")', text)  # Images

    new_text = []
    quote_level = 0
    for line in text.splitlines():  # Tables and quotes
        enter = re.finditer(r"\[quote(=(.+?))?\]", line)
        quit = re.finditer(r"\[/quote\]", line)
        if enter or quit:  # Quote part
            for quote in enter:  # Enter quotes (support multiple at a time)
                quote_level += 1
                try:
                    new_text.append("> " * quote_level + "##### " + quote.group(2))
                except:
                    new_text.append("> " * quote_level)
                line = line.replace(quote.group(0), "")
            final_quote_level = quote_level  # Store quote_level to use at the end, since it will be modified during quit iteration
            final_newline = False
            for quote in quit:  # Quit quotes (support multiple at a time)
                line = line.replace(quote.group(0), "")
                quote_level -= 1
                final_newline = True
            new_text.append("> " * final_quote_level + line)  # Finally append the line
            if final_newline:
                new_text.append(
                    "\n"
                )  # Add a new line to ensure the separation between the quote and the following text
        else:
            new_text.append(line)

    return "\n".join(new_text)
