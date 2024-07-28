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

import sys

import sass
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Compiles scss in static folder for production."""

    help = "Compile scss files from static folder"

    def compile(self, filename: str):
        args = {
            "filename": filename,
            "include_paths": settings.STATIC_ROOT.name,
            "output_style": "compressed",
        }
        if settings.SASS_PRECISION:
            args["precision"] = settings.SASS_PRECISION
        return sass.compile(**args)

    def handle(self, *args, **options):
        if not settings.STATIC_ROOT.is_dir():
            raise Exception(
                "No static folder availaible, please use collectstatic before compiling scss"
            )
        to_exec = list(settings.STATIC_ROOT.rglob("*.scss"))
        if len(to_exec) == 0:
            self.stdout.write("Nothing to compile.")
            sys.exit(0)
        self.stdout.write("---- Compiling scss files ---")
        for file in to_exec:
            # remove existing css files that will be replaced
            # keeping them while compiling the scss would break
            # import statements resolution
            css_file = file.with_suffix(".css")
            if css_file.exists():
                css_file.unlink()
        compiled_files = {file: self.compile(str(file.resolve())) for file in to_exec}
        for file, scss in compiled_files.items():
            file.replace(file.with_suffix(".css")).write_text(scss)
        self.stdout.write(
            "Files compiled : \n" + "\n- ".join(str(f) for f in compiled_files)
        )
