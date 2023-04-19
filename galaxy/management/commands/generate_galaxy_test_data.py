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

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils import timezone

from datetime import timedelta

import logging

from club.models import Club, Membership
from core.models import User, Group, Page, SithFile
from subscription.models import Subscription
from sas.models import Album, Picture, PeoplePictureRelation


RED_PIXEL_PNG = b"\x89\x50\x4e\x47\x0d\x0a\x1a\x0a\x00\x00\x00\x0d\x49\x48\x44\x52"
RED_PIXEL_PNG += b"\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90\x77\x53"
RED_PIXEL_PNG += b"\xde\x00\x00\x00\x0c\x49\x44\x41\x54\x08\xd7\x63\xf8\xcf\xc0\x00"
RED_PIXEL_PNG += b"\x00\x03\x01\x01\x00\x18\xdd\x8d\xb0\x00\x00\x00\x00\x49\x45\x4e"
RED_PIXEL_PNG += b"\x44\xae\x42\x60\x82"

USER_PACK_SIZE = 1000


class Command(BaseCommand):
    help = "Procedurally generate representative data for developing the Galaxy"

    def add_arguments(self, parser):
        parser.add_argument(
            "--user-pack-count",
            help=f"Number of packs of {USER_PACK_SIZE} users to create",
            type=int,
            default=1,
        )
        parser.add_argument(
            "--club-count", help="Number of clubs to create", type=int, default=50
        )

    def handle(self, *args, **options):
        self.logger = logging.getLogger("main")
        if options["verbosity"] > 1:
            self.logger.setLevel(logging.DEBUG)
        elif options["verbosity"] > 0:
            self.logger.setLevel(logging.INFO)
        else:
            self.logger.setLevel(logging.NOTSET)

        self.logger.info("The Galaxy is being populated by the Sith.")

        self.logger.info("Cleaning old Galaxy population")
        Club.objects.filter(unix_name__startswith="galaxy-").delete()
        Group.objects.filter(name__startswith="galaxy-").delete()
        Page.objects.filter(name__startswith="galaxy-").delete()
        User.objects.filter(username__startswith="galaxy-").delete()
        Picture.objects.filter(name__startswith="galaxy-").delete()
        Album.objects.filter(name__startswith="galaxy-").delete()
        self.logger.info("Done. Populating a new Galaxy")

        self.NB_USERS = options["user_pack_count"] * USER_PACK_SIZE
        self.NB_CLUBS = options["club_count"]

        self.now = timezone.now().replace(hour=12)
        root = User.objects.filter(username="root").first()
        sas = SithFile.objects.get(id=settings.SITH_SAS_ROOT_DIR_ID)
        self.galaxy_album = Album.objects.create(
            name="galaxy-register-file",
            owner=root,
            is_moderated=True,
            is_in_sas=True,
            parent=sas,
        )

        self.make_clubs()
        self.make_users()
        self.make_families()
        self.make_club_memberships()
        self.make_pictures()
        self.make_pictures_memberships()
        half_pack = USER_PACK_SIZE // 2
        for u in range(half_pack, self.NB_USERS, half_pack):
            self.make_important_citizen(u)

    def make_clubs(self):
        """This will create all the clubs and store them in self.clubs for fast access later"""
        self.clubs = {}
        for i in range(self.NB_CLUBS):
            self.clubs[i] = Club.objects.create(
                unix_name=f"galaxy-club-{i}", name=f"club-{i}"
            )

    def make_users(self):
        """This will create all the users and store them in self.users for fast access later"""
        self.users = {}
        for i in range(self.NB_USERS):
            u = User.objects.create_user(
                username=f"galaxy-user-{i}",
                email=f"{i}@galaxy.test",
                first_name="Citizen",
                last_name=f"n°{i}",
            )
            self.users[i] = u

            self.logger.info(f"Registering {u}")
            Subscription.objects.create(
                member=u,
                subscription_start=Subscription.compute_start(
                    self.now - timedelta(days=self.NB_USERS - i)
                ),
                subscription_end=Subscription.compute_end(duration=2),
            )

    def make_families(self):
        """
        This will iterate on all citizen after the 200th.
        Then it will take 14 other citizen among the 200 preceding (godfathers are usually older), and apply another
        heuristic to determine if they should have a family link
        """
        for i in range(200, self.NB_USERS):
            for j in range(i - 200, i, 14):  # this will loop 14 times (14² = 196)
                if (i / 10) % 10 == (i + j) % 10:
                    u1 = self.users[i]
                    u2 = self.users[j]
                    self.logger.info(f"Making {u2} the godfather of {u1}")
                    u1.godfathers.add(u2)

    def make_club_memberships(self):
        """
        This function makes multiple passes on all users to affect them some pseudo-random roles in some clubs.
        The multiple passes are useful to get some variations over who goes where.
        Each pass for each user has a chance to affect her to two different clubs, increasing a bit more the created
        chaos, while remaining purely deterministic.
        """
        for i in range(1, 11):  # users can be in up to 20 clubs
            self.logger.info(f"Club membership, pass {i}")
            for uid in range(
                i, self.NB_USERS, i
            ):  # Pass #1 will make sure every user is at least in one club
                user = self.users[uid]
                club = self.clubs[(uid + i**2) % self.NB_CLUBS]

                start = self.now - timedelta(
                    days=(((self.NB_USERS - uid) * i) // 110)
                )  # older users were in clubs before newer users
                end = start + timedelta(days=180)  # about one semester
                self.logger.info(
                    f"Making {user} a member of club {club} from {start} to {end}"
                )
                Membership(
                    user=user,
                    club=club,
                    role=(uid + i) % 10 + 1,  # spread the different roles
                    start_date=start,
                    end_date=end,
                ).save()

            for uid in range(
                10 + i * 2, self.NB_USERS, 10 + i * 2
            ):  # Make a second affectation that will skip most users, to make a few citizen more important
                user = self.users[uid]
                club = self.clubs[(uid + i**3) % self.NB_CLUBS]

                start = self.now - timedelta(
                    days=(((self.NB_USERS - uid) * i) // 100)
                )  # older users were in clubs before newer users
                end = start + timedelta(days=180)  # about one semester
                self.logger.info(
                    f"Making {user} a member of club {club} from {start} to {end}"
                )
                Membership(
                    user=user,
                    club=club,
                    role=((uid // 10) + i) % 10 + 1,  # spread the different roles
                    start_date=start,
                    end_date=end,
                ).save()

    def make_pictures(self):
        """This function creates pictures for users to be tagged on later"""
        self.picts = {}
        for i in range(self.NB_USERS):
            u = self.users[i]
            # Create twice as many pictures as users
            for j in [i, i**2]:
                self.picts[j] = Picture.objects.create(
                    owner=self.users[i],
                    name=f"galaxy-picture {u} {j}",
                    is_moderated=True,
                    is_folder=False,
                    parent=self.galaxy_album,
                    is_in_sas=True,
                    file=ContentFile(RED_PIXEL_PNG),
                    compressed=ContentFile(RED_PIXEL_PNG),
                    thumbnail=ContentFile(RED_PIXEL_PNG),
                    mime_type="image/png",
                    size=len(RED_PIXEL_PNG),
                )
                self.picts[j].file.name = self.picts[j].name
                self.picts[j].compressed.name = self.picts[j].name
                self.picts[j].thumbnail.name = self.picts[j].name
                self.picts[j].save()

    def make_pictures_memberships(self):
        """
        This assigns users to pictures, and makes enough of them for our created users to be eligible for promotion as citizen.
        See galaxy.models.Galaxy.rule for details on promotion to citizen.
        """

        # We don't want to handle limits, users in the middle will be far enough
        def _tag_neighbors(uid, neighbor_dist, pict_power, pict_dist):
            u2 = self.users[uid - neighbor_dist]
            u3 = self.users[uid + neighbor_dist]
            PeoplePictureRelation(user=u2, picture=self.picts[uid**pict_power]).save()
            PeoplePictureRelation(user=u3, picture=self.picts[uid**pict_power]).save()
            PeoplePictureRelation(user=u2, picture=self.picts[uid - pict_dist]).save()
            PeoplePictureRelation(user=u3, picture=self.picts[uid - pict_dist]).save()
            PeoplePictureRelation(user=u2, picture=self.picts[uid + pict_dist]).save()
            PeoplePictureRelation(user=u3, picture=self.picts[uid + pict_dist]).save()

        for uid in range(200, self.NB_USERS - 200):
            u1 = self.users[uid]
            self.logger.info(f"Pictures of {u1}")
            PeoplePictureRelation(user=u1, picture=self.picts[uid]).save()
            PeoplePictureRelation(user=u1, picture=self.picts[uid - 14]).save()
            PeoplePictureRelation(user=u1, picture=self.picts[uid + 14]).save()
            PeoplePictureRelation(user=u1, picture=self.picts[uid - 20]).save()
            PeoplePictureRelation(user=u1, picture=self.picts[uid + 20]).save()
            PeoplePictureRelation(user=u1, picture=self.picts[uid - 21]).save()
            PeoplePictureRelation(user=u1, picture=self.picts[uid + 21]).save()
            PeoplePictureRelation(user=u1, picture=self.picts[uid - 22]).save()
            PeoplePictureRelation(user=u1, picture=self.picts[uid + 22]).save()
            PeoplePictureRelation(user=u1, picture=self.picts[uid - 30]).save()
            PeoplePictureRelation(user=u1, picture=self.picts[uid + 30]).save()
            PeoplePictureRelation(user=u1, picture=self.picts[uid - 31]).save()
            PeoplePictureRelation(user=u1, picture=self.picts[uid + 31]).save()
            PeoplePictureRelation(user=u1, picture=self.picts[uid - 32]).save()
            PeoplePictureRelation(user=u1, picture=self.picts[uid + 32]).save()

            if uid % 3 == 0:
                _tag_neighbors(uid, 1, 1, 40)
            if uid % 5 == 0:
                _tag_neighbors(uid, 2, 1, 50)
            if uid % 10 == 0:
                _tag_neighbors(uid, 3, 1, 60)
            if uid % 20 == 0:
                _tag_neighbors(uid, 5, 1, 70)
            if uid % 25 == 0:
                _tag_neighbors(uid, 10, 1, 80)

            if uid % 2 == 1:
                _tag_neighbors(uid, 1, 2, 90)
            if uid % 15 == 0:
                _tag_neighbors(uid, 5, 2, 100)
            if uid % 30 == 0:
                _tag_neighbors(uid, 4, 2, 110)

    def make_important_citizen(self, uid):
        """
        This will make the user passed in `uid` a more important citizen, that will thus trigger many more connections
        to other (lanes) and be dragged towards the center of the Galaxy.
        """
        u1 = self.users[uid]
        u2 = self.users[uid - 100]
        u3 = self.users[uid + 100]
        u1.godfathers.add(u3)
        u1.godchildren.add(u2)
        self.logger.info(f"{u1} will be important and close to {u2} and {u3}")
        for p in range(  # Mix them with other citizen for more chaos
            uid - 400, uid - 200
        ):
            # users may already be on the pictures
            if not self.picts[p].people.filter(user=u1).exists():
                PeoplePictureRelation(user=u1, picture=self.picts[p]).save()
            if not self.picts[p].people.filter(user=u2).exists():
                PeoplePictureRelation(user=u2, picture=self.picts[p]).save()
            if not self.picts[p**2].people.filter(user=u1).exists():
                PeoplePictureRelation(user=u1, picture=self.picts[p**2]).save()
            if not self.picts[p**2].people.filter(user=u2).exists():
                PeoplePictureRelation(user=u2, picture=self.picts[p**2]).save()
