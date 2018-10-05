# -*- coding:utf-8 -*
#
# Copyright 2016,2017
# - Skia <skia@libskia.so>
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

import re

# Image utils

from io import BytesIO
from datetime import date

from PIL import ExifTags

# from exceptions import IOError
import PIL

from django.conf import settings
from django.core.files.base import ContentFile


def get_start_of_semester(d=date.today()):
    """
    This function computes the start date of the semester with respect to the given date (default is today),
    and the start date given in settings.SITH_START_DATE.
    It takes the nearest past start date.
    Exemples: with SITH_START_DATE = (8, 15)
        Today      -> Start date
        2015-03-17 -> 2015-02-15
        2015-01-11 -> 2014-08-15
    """
    today = d
    year = today.year
    start = date(year, settings.SITH_START_DATE[0], settings.SITH_START_DATE[1])
    start2 = start.replace(month=(start.month + 6) % 12)
    if start > start2:
        start, start2 = start2, start
    if today < start:
        return start2.replace(year=year - 1)
    elif today < start2:
        return start
    else:
        return start2


def get_semester(d=date.today()):
    start = get_start_of_semester(d)
    if start.month <= 6:
        return "P" + str(start.year)[-2:]
    else:
        return "A" + str(start.year)[-2:]


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
    im = im.resize((width, height), PIL.Image.ANTIALIAS)
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
            final_quote_level = (
                quote_level
            )  # Store quote_level to use at the end, since it will be modified during quit iteration
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
            final_quote_level = (
                quote_level
            )  # Store quote_level to use at the end, since it will be modified during quit iteration
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
