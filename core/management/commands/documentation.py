#!/usr/bin/env python3
# -*- coding:utf-8 -*
#
# Copyright 2019
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
import sys

from http.server import test, CGIHTTPRequestHandler

from django.core.management.base import BaseCommand

# TODO Django 2.2 : implement autoreload following
# https://stackoverflow.com/questions/42907285/django-autoreload-add-watched-file


class Command(BaseCommand):
    help = "Generate Sphinx documentation and launch basic server"

    default_addr = "127.0.0.1"
    default_port = "8080"

    def add_arguments(self, parser):
        parser.add_argument(
            "addrport", nargs="?", help="Optional port number, or ipaddr:port"
        )

    def handle(self, *args, **kwargs):
        os.chdir("doc")
        err = os.system("make html")

        if err != 0:
            self.stdout.write("A build error occured, exiting")
            sys.exit(err)

        os.chdir("_build/html")
        addr = self.default_addr
        port = self.default_port
        if kwargs["addrport"]:
            addrport = kwargs["addrport"].split(":")

            addr = addrport[0]

            if len(addrport) > 1:
                port = addrport[1]

            if not port.isnumeric():
                self.stdout.write("%s is not a valid port" % (port,))
                sys.exit(0)

        test(HandlerClass=CGIHTTPRequestHandler, port=int(port), bind=addr)
