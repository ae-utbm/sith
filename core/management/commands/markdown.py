#
# Copyright 2017
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


from django.conf import settings
from django.core.management.base import BaseCommand

from core.markdown import markdown


class Command(BaseCommand):
    help = "Output the fully rendered SYNTAX.md file"

    def handle(self, *args, **options):
        root_path = settings.BASE_DIR
        with open(root_path / "core/fixtures/SYNTAX.md", "r") as md:
            result = markdown(md.read())
        print(result, end="")
