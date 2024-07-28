#!/usr/bin/env python3
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
import functools
from pathlib import Path

import sass
from django.conf import settings
from django.core.files.base import ContentFile
from django.templatetags.static import static
from django_jinja.builtins.filters import static

from core.scss.storage import ScssFileStorage, find_file


@functools.cache
def _scss_storage():
    return ScssFileStorage()


def process_scss_path(path: Path):
    css_path = path.with_suffix(".css")
    if settings.DEBUG:
        compile_args = {
            "filename": find_file(path),
            "include_paths": settings.SASS_INCLUDE_FOLDERS,
        }
        if settings.SASS_PRECISION:
            compile_args["precision"] = settings.SASS_PRECISION
        content = sass.compile(**compile_args)
        storage = _scss_storage()
        if storage.exists(css_path):
            storage.delete(css_path)
        storage.save(css_path, ContentFile(content))
    return static(css_path)
