# -*- coding:utf-8 -*
#
# Copyright 2023
# - Skia <skia@hya.sk>
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

from django.core.management.base import BaseCommand

from galaxy.models import Galaxy


class Command(BaseCommand):
    help = (
        "Reset the whole galaxy and compute once again all the relation scores of all users. "
        "As the sith's users are rather numerous, this command might be quite expensive in memory "
        "as well as in CPU time. Please remind this fact and never call this command more than once "
        "a day outside of a test environment."
    )

    def handle(self, *args, **options):
        print("The Galaxy is being ruled by the Sith")

        Galaxy.recompute()
