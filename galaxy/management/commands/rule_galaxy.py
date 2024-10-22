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
import logging
import warnings

from django.core.management.base import BaseCommand
from django.db import connection

from galaxy.models import Galaxy


class Command(BaseCommand):
    help = (
        "Rule the Galaxy! "
        "Reset the whole galaxy and compute once again all the relation scores of all users. "
        "As the sith's users are rather numerous, this command might be quite expensive in memory "
        "and CPU time. Please keep this fact in mind when scheduling calls to this command in a production "
        "environment."
    )

    def handle(self, *args, **options):
        logger = logging.getLogger("main")
        if not 0 <= options["verbosity"] <= 2:
            warnings.warn(
                "verbosity level should be between 0 and 2 included", stacklevel=2
            )

        if options["verbosity"] == 2:
            logger.setLevel(logging.DEBUG)
        elif options["verbosity"] == 1:
            logger.setLevel(logging.INFO)
        else:
            logger.setLevel(logging.ERROR)

        logger.info("The Galaxy is being ruled by the Sith.")
        galaxy = Galaxy.objects.create()
        galaxy.rule()
        logger.info("Sending old galaxies' remains to garbage.")
        Galaxy.objects.filter(state__isnull=True).delete()

        logger.info("Ruled the galaxy in {} queries.".format(len(connection.queries)))
        if options["verbosity"] > 2:
            for q in connection.queries:
                logger.debug(q)
