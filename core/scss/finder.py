#!/usr/bin/env python3
# -*- coding:utf-8 -*
#
# Copyright 2016,2017
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
