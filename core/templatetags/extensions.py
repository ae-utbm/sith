#
# Copyright 2024
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
# this program; if not, write to the Free Software Foundation, Inc., 59 Temple
# Place - Suite 330, Boston, MA 02111-1307, USA.
#
#
from typing import Callable

import honeypot.templatetags.honeypot as honeypot_filters
from django.template.loader import render_to_string
from jinja2 import Environment, nodes
from jinja2.ext import Extension
from jinja2.parser import Parser


class HoneypotExtension(Extension):
    """
    Wrapper around the honeypot extension tag
    Known limitation: doesn't support arguments

    Usage: {% render_honeypot_field %}
    """

    tags = {"render_honeypot_field"}

    def __init__(self, environment: Environment) -> None:
        environment.globals["render_honeypot_field"] = (
            honeypot_filters.render_honeypot_field
        )
        self.environment = environment

    def parse(self, parser: Parser) -> nodes.Output:
        lineno = parser.stream.expect("name:render_honeypot_field").lineno
        call = self.call_method(
            "_render",
            [nodes.Name("render_honeypot_field", "load", lineno=lineno)],
            lineno=lineno,
        )
        return nodes.Output([nodes.MarkSafe(call)])

    def _render(self, render_honeypot_field: Callable[[str | None], str]):
        return render_to_string("honeypot/honeypot_field.html", render_honeypot_field())
