#!/usr/bin/env python3
# -*- coding:utf-8 -*
#
# Copyright 2017
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

import os
import sass
from django.utils.encoding import force_bytes, iri_to_uri
from django.core.files.base import ContentFile
from django.utils.six.moves.urllib.parse import urljoin
from django.templatetags.static import static
from django.conf import settings
from core.scss.storage import ScssFileStorage, find_file


class ScssProcessor(object):
    """
        If DEBUG mode enabled : compile the scss file
        Else : give the path of the corresponding css supposed to already be compiled
        Don't forget to use compilestatics to compile scss for production
    """

    prefix = iri_to_uri(getattr(settings, "STATIC_URL", "/static/"))
    storage = ScssFileStorage()
    scss_extensions = [".scss"]

    def __init__(self, path=None):
        self.path = path

    def _convert_scss(self):
        basename, ext = os.path.splitext(self.path)
        css_filename = self.path.replace(".scss", ".css")
        url = urljoin(self.prefix, css_filename)

        if not settings.DEBUG:
            return url

        if ext not in self.scss_extensions:
            return static(self.path)

        # Compilation on the fly
        compile_args = {
            "filename": find_file(self.path),
            "include_paths": settings.SASS_INCLUDE_FOLDERS,
        }
        if settings.SASS_PRECISION:
            compile_args["precision"] = settings.SASS_PRECISION
        content = sass.compile(**compile_args)
        content = force_bytes(content)

        if self.storage.exists(css_filename):
            self.storage.delete(css_filename)
        self.storage.save(css_filename, ContentFile(content))

        return url

    def get_converted_scss(self):
        if self.path:
            return self._convert_scss()
        else:
            return ""
