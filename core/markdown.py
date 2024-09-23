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
from __future__ import annotations

import re
from typing import TYPE_CHECKING

import mistune
from django.urls import reverse
from mistune import HTMLRenderer, Markdown

if TYPE_CHECKING:
    from mistune import InlineParser, InlineState

# match __text__, without linebreak in the text, nor backslash prepending an underscore
# Examples :
#   - "__text__" : OK
#   - "__te xt__" : OK
#   - "__te_xt__" : nope (underscore in the middle)
#   - "__te\_xt__" : Ok (the middle underscore is escaped)
#   - "__te\nxt__" : nope (there is a linebreak in the text)
#   - "\__text__" : nope (one of the underscores have a backslash prepended)
#   - "\\__text__" : Ok (the backslash is ignored, because there is another backslash before)
UNDERLINED_RE = (
    r"(?<!\\)(?:\\{2})*"  # ignore if there is an odd number of backslashes before
    r"_{2}"  # two underscores
    r"(?P<underlined>([^\\_]|\\.)+)"  # the actual text
    r"_{2}"  # closing underscores
)

SITH_LINK_RE = (
    r"\[(?P<page_name>[\w\s]+)\]"  #  [nom du lien]
    r"\(page:\/\/"  #  (page://
    r"(?P<page_slug>[a-zA-Z0-9][a-zA-Z0-9.-]*[a-zA-Z0-9])"  # actual page name
    r"\)"  # )
)

CUSTOM_DIMENSIONS_IMAGE_RE = (
    r"\[(?P<img_name>[\w\s]+)\]"  # [nom du lien]
    r"\(img:\/\/"  # (img://
    r"(?P<img_slug>[a-zA-Z0-9][a-zA-Z0-9.-]*[a-zA-Z0-9])"  # actual page name
    r"\)"  # )
)


def parse_underline(_inline: InlineParser, m: re.Match, state: InlineState):
    state.append_token({"type": "underline", "raw": m.group("underlined")})
    return m.end()


def underline(md_instance: Markdown):
    md_instance.inline.register(
        "underline",
        UNDERLINED_RE,
        parse_underline,
        before="emphasis",
    )
    md_instance.renderer.register("underline", lambda _, text: f"<u>{text}</u>")


def parse_sith_link(_inline: InlineParser, m: re.Match, state: InlineState):
    page_name = m.group("page_name")
    page_slug = m.group("page_slug")
    state.append_token(
        {
            "type": "link",
            "children": [{"type": "text", "raw": page_name}],
            "attrs": {"url": reverse("core:page", kwargs={"page_name": page_slug})},
        }
    )
    return m.end()


def sith_link(md_instance: Markdown):
    md_instance.inline.register(
        "sith_link",
        SITH_LINK_RE,
        parse_sith_link,
        before="emphasis",
    )
    # no custom renderer here.
    # we just add another parsing rule, but render it as if it was
    # a regular markdown link


class SithRenderer(HTMLRenderer):
    def image(self, text: str, url: str, title=None) -> str:
        if "?" not in url:
            return super().image(text, url, title)

        new_url, params = url.rsplit("?", maxsplit=1)
        m = re.match(r"^(?P<width>\d+(%|px)?)(x(?P<height>\d+(%|px)?))?$", params)
        if not m:
            return super().image(text, url, title)

        width, height = m.group("width"), m.group("height")
        if not width.endswith(("%", "px")):
            width += "px"
        style = f"width:{width};"
        if height is not None:
            if not height.endswith(("%", "px")):
                height += "px"
            style += f"height:{height};"
        return super().image(text, new_url, title).replace("/>", f'style="{style}" />')


markdown = mistune.create_markdown(
    renderer=SithRenderer(escape=True),
    plugins=[
        underline,
        sith_link,
        "strikethrough",
        "footnotes",
        "table",
        "spoiler",
        "subscript",
        "superscript",
        "url",
    ],
)
