#!/usr/bin/env python3
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

import os
from urllib.parse import urljoin

import sass
from django.conf import settings
from django.core.files.base import ContentFile
from django.templatetags.static import static
from django.utils.encoding import force_bytes, iri_to_uri

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
