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

import sass
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """
    Compiles scss in static folder for production
    """

    help = "Compile scss files from static folder"

    def compile(self, filename):
        args = {"filename": filename, "include_paths": settings.STATIC_ROOT}
        if settings.SASS_PRECISION:
            args["precision"] = settings.SASS_PRECISION
        return sass.compile(**args)

    def is_compilable(self, file, ext_list):
        path, ext = os.path.splitext(file)
        return ext in ext_list

    def exec_on_folder(self, folder, func):
        to_exec = []
        for file in os.listdir(folder):
            file = os.path.join(folder, file)
            if os.path.isdir(file):
                self.exec_on_folder(file, func)
            elif self.is_compilable(file, [".scss"]):
                to_exec.append(file)

        for file in to_exec:
            func(file)

    def compilescss(self, file):
        print("compiling %s" % file)
        with open(file.replace(".scss", ".css"), "w") as newfile:
            newfile.write(self.compile(file))

    def removescss(self, file):
        print("removing %s" % file)
        os.remove(file)

    def handle(self, *args, **options):
        if os.path.isdir(settings.STATIC_ROOT):
            print("---- Compiling scss files ---")
            self.exec_on_folder(settings.STATIC_ROOT, self.compilescss)
            print("---- Removing scss files ----")
            self.exec_on_folder(settings.STATIC_ROOT, self.removescss)
        else:
            print(
                "No static folder avalaible, please use collectstatic before compiling scss"
            )
