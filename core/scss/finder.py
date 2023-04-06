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
from collections import OrderedDict

from django.conf import settings
from django.contrib.staticfiles.finders import FileSystemFinder
from django.core.files.storage import FileSystemStorage


class ScssFinder(FileSystemFinder):
    """
    Find static *.css files compiled on the fly
    """

    locations = []

    def __init__(self, apps=None, *args, **kwargs):
        location = settings.STATIC_ROOT
        if not os.path.isdir(location):
            return
        self.locations = [("", location)]
        self.storages = OrderedDict()
        filesystem_storage = FileSystemStorage(location=location)
        filesystem_storage.prefix = self.locations[0][0]
        self.storages[location] = filesystem_storage

    def find(self, path, all=False):
        if path.endswith(".css"):
            return super(ScssFinder, self).find(path, all)
        return []
