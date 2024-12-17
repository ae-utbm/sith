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
from datetime import timedelta
from typing import Final, Optional

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils import timezone

from club.models import Club, Membership
from core.models import Group, Page, SithFile, User
from sas.models import Album, PeoplePictureRelation, Picture
from subscription.models import Subscription

RED_PIXEL_PNG: Final[bytes] = (
    b"\x89\x50\x4e\x47\x0d\x0a\x1a\x0a\x00\x00\x00\x0d\x49\x48\x44\x52"
    b"\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90\x77\x53"
    b"\xde\x00\x00\x00\x0c\x49\x44\x41\x54\x08\xd7\x63\xf8\xcf\xc0\x00"
    b"\x00\x03\x01\x01\x00\x18\xdd\x8d\xb0\x00\x00\x00\x00\x49\x45\x4e"
    b"\x44\xae\x42\x60\x82"
)

USER_PACK_SIZE: Final[int] = 1000


class Command(BaseCommand):
    help = "Procedurally generate representative data for developing the Galaxy"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.now = timezone.now().replace(hour=12)

        self.users: Optional[list[User]] = None
        self.clubs: Optional[list[Club]] = None
        self.picts: Optional[list[Picture]] = None
        self.pictures_tags: Optional[list[PeoplePictureRelation]] = None

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
        if not 0 <= options["verbosity"] <= 2:
            warnings.warn(
                "verbosity level should be between 0 and 2 included", stacklevel=2
            )

        if options["verbosity"] == 2:
            self.logger.setLevel(logging.DEBUG)
        elif options["verbosity"] == 1:
            self.logger.setLevel(logging.INFO)
        else:
            self.logger.setLevel(logging.ERROR)

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
        """Create all the clubs [club.models.Club][].

        After creation, the clubs are stored in `self.clubs` for fast access later.
        Don't create the pages of the clubs ([core.models.Page][]).
        """
        # dummy groups.
        # the galaxy doesn't care about the club groups,
        # but it's necessary to add them nonetheless in order
        # not to break the integrity constraints
        self.clubs = Club.objects.bulk_create(
            [
                Club(
                    unix_name=f"galaxy-club-{i}",
                    name=f"club-{i}",
                    board_group=Group.objects.create(name=f"board {i}"),
                    members_group=Group.objects.create(name=f"members {i}"),
                )
                for i in range(self.NB_CLUBS)
            ]
        )

    def make_users(self):
        """Create all the users and store them in `self.users` for fast access later.

        Also create a subscription for all the generated users.
        """
        self.users = []
        for i in range(self.NB_USERS):
            u = User(
                username=f"galaxy-user-{i}",
                email=f"{i}@galaxy.test",
                first_name="Citizen",
                last_name=f"n°{i}",
            )
            self.logger.info(f"Creating {u}")
            self.users.append(u)
        User.objects.bulk_create(self.users)
        self.users = list(User.objects.filter(username__startswith="galaxy-").all())

        # now that users are created, create their subscription
        subs = []
        end = Subscription.compute_end(duration=2)
        for i, user in enumerate(self.users):
            self.logger.info(f"Registering {user}")
            subs.append(
                Subscription(
                    member=user,
                    subscription_start=Subscription.compute_start(
                        self.now - timedelta(days=self.NB_USERS - i)
                    ),
                    subscription_end=end,
                )
            )
        Subscription.objects.bulk_create(subs)

    def make_families(self):
        """Generate the godfather/godchild relations for the users contained in :attr:`self.users`.

        The :meth:`make_users` method must have been called beforehand.

        This will iterate on all citizen after the 200th.
        Then it will take 14 other citizen among the previous 200
        (godfathers are usually older), and apply another
        heuristic to determine whether they should have a family link
        It will result in approximately 40% of users having at least one godchild
        and 70% having at least one godfather.
        """
        if self.users is None:
            raise RuntimeError(
                "The `make_users()` method must be called before `make_families()`"
            )
        godfathers = []
        for i in range(200, self.NB_USERS):
            for j in range(i - 200, i, 14):  # this will loop 14 times (14² = 196)
                if (i // 10) % 10 == (i + j) % 10:
                    u1 = self.users[i]
                    u2 = self.users[j]
                    godfathers.append(User.godfathers.through(from_user=u1, to_user=u2))
                    self.logger.info(f"Making {u2} the godfather of {u1}")
        User.godfathers.through.objects.bulk_create(godfathers)

    def make_club_memberships(self):
        """Assign users to clubs and give them a role in a pseudo-random way.

        The :meth:`make_users` and :meth:`make_clubs` methods
        must have been called beforehand.

        Work by making multiples passes on all users to affect
        them some pseudo-random roles in some clubs.
        The multiple passes are useful to get some variations over who goes where.
        Each pass for each user has a chance to affect her to two different clubs,
        increasing a bit more the created chaos, while remaining purely deterministic.
        """
        if self.users is None:
            raise RuntimeError(
                "The `make_users()` method must be called before `make_club_memberships()`"
            )
        if self.clubs is None:
            raise RuntimeError(
                "The `make_clubs()` method must be called before `make_club_memberships()`"
            )
        memberships = []
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
                self.logger.debug(
                    f"Making {user} a member of club {club} from {start} to {end}"
                )
                memberships.append(
                    Membership(
                        user=user,
                        club=club,
                        role=(uid + i) % 10 + 1,  # spread the different roles
                        start_date=start,
                        end_date=end,
                    )
                )

            for uid in range(
                10 + i * 2, self.NB_USERS, 10 + i * 2
            ):  # Make a second affectation that will skip most users, to make a few citizen more important
                user = self.users[uid]
                club = self.clubs[(uid + i**3) % self.NB_CLUBS]

                start = self.now - timedelta(
                    days=(((self.NB_USERS - uid) * i) // 100)
                )  # older users were in clubs before newer users
                end = start + timedelta(days=180)  # about one semester
                self.logger.debug(
                    f"Making {user} a member of club {club} from {start} to {end}"
                )
                memberships.append(
                    Membership(
                        user=user,
                        club=club,
                        role=((uid // 10) + i) % 10 + 1,  # spread the different roles
                        start_date=start,
                        end_date=end,
                    )
                )
        Membership.objects.bulk_create(memberships)

    def make_pictures(self):
        """Create pictures for users to be tagged on later.

        The :meth:`make_users` method must have been called beforehand.
        """
        if self.users is None:
            raise RuntimeError(
                "The `make_users()` method must be called before `make_families()`"
            )
        self.picts = []
        # Create twice as many pictures as users
        for i in range(self.NB_USERS * 2):
            u = self.users[i % self.NB_USERS]
            self.logger.info(f"Making Picture {i // self.NB_USERS} for {u}")
            self.picts.append(
                Picture(
                    owner=u,
                    name=f"galaxy-picture {u} {i // self.NB_USERS}",
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
            )
            self.picts[i].file.name = self.picts[i].name
            self.picts[i].compressed.name = self.picts[i].name
            self.picts[i].thumbnail.name = self.picts[i].name
        Picture.objects.bulk_create(self.picts)
        self.picts = list(Picture.objects.filter(name__startswith="galaxy-").all())

    def make_pictures_memberships(self):
        """Assign users to pictures and make enough of them for our
        created users to be eligible for promotion as citizen.

        See `galaxy.models.Galaxy.rule` for details on promotion to citizen.
        """
        self.pictures_tags = []

        # We don't want to handle limits, users in the middle will be far enough
        def _tag_neighbors(uid, neighbor_dist, pict_offset, pict_dist):
            u2 = self.users[uid - neighbor_dist]
            u3 = self.users[uid + neighbor_dist]
            self.pictures_tags += [
                PeoplePictureRelation(user=u2, picture=self.picts[uid + pict_offset]),
                PeoplePictureRelation(user=u3, picture=self.picts[uid + pict_offset]),
                PeoplePictureRelation(user=u2, picture=self.picts[uid - pict_dist]),
                PeoplePictureRelation(user=u3, picture=self.picts[uid - pict_dist]),
                PeoplePictureRelation(user=u2, picture=self.picts[uid + pict_dist]),
                PeoplePictureRelation(user=u3, picture=self.picts[uid + pict_dist]),
            ]

        for uid in range(200, self.NB_USERS - 200):
            u1 = self.users[uid]
            self.logger.info(f"Pictures of {u1}")
            self.pictures_tags += [
                PeoplePictureRelation(user=u1, picture=self.picts[uid]),
                PeoplePictureRelation(user=u1, picture=self.picts[uid - 14]),
                PeoplePictureRelation(user=u1, picture=self.picts[uid + 14]),
                PeoplePictureRelation(user=u1, picture=self.picts[uid - 20]),
                PeoplePictureRelation(user=u1, picture=self.picts[uid + 20]),
                PeoplePictureRelation(user=u1, picture=self.picts[uid - 21]),
                PeoplePictureRelation(user=u1, picture=self.picts[uid + 21]),
                PeoplePictureRelation(user=u1, picture=self.picts[uid - 22]),
                PeoplePictureRelation(user=u1, picture=self.picts[uid + 22]),
                PeoplePictureRelation(user=u1, picture=self.picts[uid - 30]),
                PeoplePictureRelation(user=u1, picture=self.picts[uid + 30]),
                PeoplePictureRelation(user=u1, picture=self.picts[uid - 31]),
                PeoplePictureRelation(user=u1, picture=self.picts[uid + 31]),
                PeoplePictureRelation(user=u1, picture=self.picts[uid - 32]),
                PeoplePictureRelation(user=u1, picture=self.picts[uid + 32]),
            ]

            if uid % 3 == 0:
                _tag_neighbors(uid, 1, 0, 40)
            if uid % 5 == 0:
                _tag_neighbors(uid, 2, 0, 50)
            if uid % 10 == 0:
                _tag_neighbors(uid, 3, 0, 60)
            if uid % 20 == 0:
                _tag_neighbors(uid, 5, 0, 70)
            if uid % 25 == 0:
                _tag_neighbors(uid, 10, 0, 80)

            if uid % 2 == 1:
                _tag_neighbors(uid, 1, self.NB_USERS, 90)
            if uid % 15 == 0:
                _tag_neighbors(uid, 5, self.NB_USERS, 100)
            if uid % 30 == 0:
                _tag_neighbors(uid, 4, self.NB_USERS, 110)
        PeoplePictureRelation.objects.bulk_create(self.pictures_tags)

    def make_important_citizen(self, uid: int):
        """Make the user whose uid is given in parameter a more important citizen.

        This will trigger many more connections to others (lanes)
        and dragging him towards the center of the Galaxy.

        This promotion is obtained by adding more family links
        and by tagging the user in more pictures.

        The users chosen to be added to this user's family shall
        also be tagged in more pictures, thus making them also
        more important.

        Args:
            uid: the id of the user to make more important
        """
        u1 = self.users[uid]
        u2 = self.users[uid - 100]
        u3 = self.users[uid + 100]
        User.godfathers.through.objects.bulk_create(
            [
                User.godfathers.through(from_user=u1, to_user=u2),
                User.godfathers.through(from_user=u3, to_user=u2),
            ],
            ignore_conflicts=True,  # in case a relationship has already been created
        )
        self.logger.info(f"{u1} will be important and close to {u2} and {u3}")
        pictures_tags = []
        for p in range(uid - 400, uid - 200):
            # Mix them with other citizen for more chaos
            pictures_tags += [
                PeoplePictureRelation(user=u1, picture=self.picts[p]),
                PeoplePictureRelation(user=u2, picture=self.picts[p]),
                PeoplePictureRelation(user=u1, picture=self.picts[p + self.NB_USERS]),
                PeoplePictureRelation(user=u2, picture=self.picts[p + self.NB_USERS]),
            ]
        # users may already be on the pictures.
        # In this case the conflict will just be ignored
        # and nothing will happen for this entry
        PeoplePictureRelation.objects.bulk_create(pictures_tags, ignore_conflicts=True)
