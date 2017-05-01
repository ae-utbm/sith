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
import sass
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = "Comile scss files from static folder"

    def compilescss(self, folder):
        to_compile = []
        for file in os.listdir(folder):
            file = os.path.join(folder, file)
            if os.path.isdir(file):
                self.compilescss(file)
            else:
                path, ext = os.path.splitext(file)
                if ext == ".scss":
                    to_compile.append(file)

        for f in to_compile:
            print("compilling %s" % f)
            with open(f, "r") as oldfile:
                with open(f.replace('.scss', '.css'), "w") as newfile:
                    newfile.write(sass.compile(string=oldfile.read()))

    def removescss(self, folder):
        to_remove = []
        for file in os.listdir(folder):
            file = os.path.join(folder, file)
            if os.path.isdir(file):
                self.removescss(file)
            else:
                path, ext = os.path.splitext(file)
                if ext == ".scss":
                    to_remove.append(file)
        for f in to_remove:
            print("removing %s" % f)
            os.remove(f)

    def handle(self, *args, **options):

        if 'static' in os.listdir():
            print("---- Compilling scss files ---")
            self.compilescss('static')
            print("---- Removing scss files ----")
            self.removescss('static')
        else:
            print("No static folder avaliable, please use collectstatic before compilling scss")