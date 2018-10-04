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

import os
import re
from mistune import Renderer, InlineGrammar, InlineLexer, Markdown, escape, escape_link
from django.core.urlresolvers import reverse


class SithRenderer(Renderer):
    def file_link(self, id, suffix):
        return reverse("core:file_detail", kwargs={"file_id": id}) + suffix

    def exposant(self, text):
        return """<sup>%s</sup>""" % text

    def indice(self, text):
        return """<sub>%s</sub>""" % text

    def underline(self, text):
        return """<u>%s</u>""" % text

    def image(self, original_src, title, text):
        """Rendering a image with title and text.
        :param src: source link of the image.
        :param title: title text of the image.
        :param text: alt text of the image.
        """
        style = None
        if "?" in original_src:
            src, params = original_src.rsplit("?", maxsplit=1)
            m = re.search(r"(\d+%?)(x(\d+%?))?", params)
            if not m:
                src = original_src
            else:
                width = m.group(1)
                if not width.endswith("%"):
                    width += "px"
                style = "width: %s; " % width
                try:
                    height = m.group(3)
                    if not height.endswith("%"):
                        height += "px"
                    style += "height: %s; " % height
                except:
                    pass
        else:
            params = None
            src = original_src
        src = escape_link(src)
        text = escape(text, quote=True)
        if title:
            title = escape(title, quote=True)
            html = '<img src="%s" alt="%s" title="%s"' % (src, text, title)
        else:
            html = '<img src="%s" alt="%s"' % (src, text)
        if style:
            html = '%s style="%s"' % (html, style)
        if self.options.get("use_xhtml"):
            return "%s />" % html
        return "%s>" % html


class SithInlineGrammar(InlineGrammar):
    double_emphasis = re.compile(r"^\*{2}([\s\S]+?)\*{2}(?!\*)")  # **word**
    emphasis = re.compile(r"^\*((?:\*\*|[^\*])+?)\*(?!\*)")  # *word*
    underline = re.compile(r"^_{2}([\s\S]+?)_{2}(?!_)")  # __word__
    exposant = re.compile(r"^<sup>([\s\S]+?)</sup>")  # <sup>text</sup>
    indice = re.compile(r"^<sub>([\s\S]+?)</sub>")  # <sub>text</sub>


class SithInlineLexer(InlineLexer):
    grammar_class = SithInlineGrammar

    default_rules = [
        "escape",
        # 'inline_html',
        "autolink",
        "url",
        "footnote",
        "link",
        "reflink",
        "nolink",
        "exposant",
        "double_emphasis",
        "emphasis",
        "underline",
        "indice",
        "code",
        "linebreak",
        "strikethrough",
        "text",
    ]
    inline_html_rules = [
        "escape",
        "autolink",
        "url",
        "link",
        "reflink",
        "nolink",
        "exposant",
        "double_emphasis",
        "emphasis",
        "underline",
        "indice",
        "code",
        "linebreak",
        "strikethrough",
        "text",
    ]

    def output_underline(self, m):
        text = m.group(1)
        return self.renderer.underline(text)

    def output_exposant(self, m):
        text = m.group(1)
        return self.renderer.exposant(text)

    def output_indice(self, m):
        text = m.group(1)
        return self.renderer.indice(text)

    # Double emphasis rule changed
    def output_double_emphasis(self, m):
        text = m.group(1)
        text = self.output(text)
        return self.renderer.double_emphasis(text)

    # Emphasis rule changed
    def output_emphasis(self, m):
        text = m.group(1)
        text = self.output(text)
        return self.renderer.emphasis(text)

    def _process_link(self, m, link, title=None):
        try:  # Add page:// support for links
            page = re.compile(r"^page://(\S*)")  # page://nom_de_ma_page
            match = page.search(link)
            page = match.group(1) or ""
            link = reverse("core:page", kwargs={"page_name": page})
        except:
            pass
        try:  # Add file:// support for links
            file_link = re.compile(r"^file://(\d*)/?(\S*)?")  # file://4000/download
            match = file_link.search(link)
            id = match.group(1)
            suffix = match.group(2) or ""
            link = reverse("core:file_detail", kwargs={"file_id": id}) + suffix
        except:
            pass
        return super(SithInlineLexer, self)._process_link(m, link, title)


renderer = SithRenderer(escape=True)
inline = SithInlineLexer(renderer)

markdown = Markdown(renderer, inline=inline)

if __name__ == "__main__":
    root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(root_path) + "/doc/SYNTAX.md", "r") as md:
        result = markdown(md.read())
    print(result, end="")
