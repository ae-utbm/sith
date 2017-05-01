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
    help = "Compile scss files from static folder"

    def is_compilable(self, file, ext_list):
        path, ext = os.path.splitext(file)
        return ext in ext_list

    def exec_on_folder(self, folder, func):
        to_exec = []
        for file in os.listdir(folder):
            file = os.path.join(folder, file)
            if os.path.isdir(file):
                self.exec_on_folder(file, func)
            elif self.is_compilable(file, ['.scss']):
                to_exec.append(file)

        for file in to_exec:
            func(file)

    def compilescss(self, file):
        print("compiling %s" % file)
        with open(file, "r") as oldfile:
            with open(file.replace('.scss', '.css'), "w") as newfile:
                newfile.write(sass.compile(string=oldfile.read()))

    def removescss(self, file):
        print("removing %s" % file)
        os.remove(file)

    def handle(self, *args, **options):

        if 'static' in os.listdir():
            print("---- Compiling scss files ---")
            self.exec_on_folder('static', self.compilescss)
            print("---- Removing scss files ----")
            self.exec_on_folder('static', self.removescss)
        else:
            print("No static folder avalaible, please use collectstatic before compiling scss")