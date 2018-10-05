# -*- coding:utf-8 -*
#
# Copyright 2018
# - Skia <skia@libskia.so>
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
from django.core.management.base import BaseCommand
from django.core.management import call_command

from core.models import SithFile


class Command(BaseCommand):
    help = "Recursively check the file system with respect to the DB"

    def add_arguments(self, parser):
        parser.add_argument(
            "ids", metavar="ID", type=int, nargs="+", help="The file IDs to process"
        )

    def handle(self, *args, **options):
        root_path = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        )
        files = SithFile.objects.filter(id__in=options["ids"]).all()
        for f in files:
            f._check_fs()
