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

from __future__ import annotations

import itertools
import logging
import math
import time
from collections import defaultdict
from typing import NamedTuple, TypedDict

from django.db import models
from django.db.models import Count, Exists, F, OuterRef, Q, QuerySet
from django.utils.timezone import localdate, now
from django.utils.translation import gettext_lazy as _

from club.models import Membership
from core.models import User
from sas.models import PeoplePictureRelation, Picture
from subscription.models import Subscription


class GalaxyStar(models.Model):
    """Define a star (vertex -> user) in the galaxy graph.

    Store a reference to its owner citizen.

    Stars are linked to each others through the :class:`GalaxyLane` model.

    Each GalaxyStar has a mass which push it towards the center of the galaxy.
    This mass is proportional to the number of pictures the owner of the star
    is tagged on.
    """

    owner = models.ForeignKey(
        User,
        verbose_name=_("star owner"),
        related_name="stars",
        on_delete=models.CASCADE,
    )
    mass = models.PositiveIntegerField(
        _("star mass"),
        default=0,
    )
    galaxy = models.ForeignKey(
        "Galaxy",
        verbose_name=_("the galaxy this star belongs to"),
        related_name="stars",
        on_delete=models.CASCADE,
        null=True,
    )

    def __str__(self):
        return str(self.owner)


@property
def current_star(self) -> GalaxyStar | None:
    """The star of this user in the :class:`Galaxy`.

    Only take into account the most recent active galaxy.

    Returns:
        The star of this user if there is an active Galaxy
        and this user is a citizen of it, else `None`
    """
    return self.stars.filter(galaxy=Galaxy.get_current_galaxy()).last()


# Adding a shortcut to User class for getting its star belonging to the latest ruled Galaxy
User.current_star = current_star


class GalaxyLane(models.Model):
    """Define a lane (edge -> link between galaxy citizen) in the galaxy map.

    Store a reference to both its ends and the distance it covers.
    Score details between citizen owning the stars is also stored here.
    """

    star1 = models.ForeignKey(
        GalaxyStar,
        verbose_name=_("galaxy star 1"),
        related_name="lanes1",
        on_delete=models.CASCADE,
    )
    star2 = models.ForeignKey(
        GalaxyStar,
        verbose_name=_("galaxy star 2"),
        related_name="lanes2",
        on_delete=models.CASCADE,
    )
    distance = models.PositiveIntegerField(
        _("distance"),
        default=0,
        help_text=_("Distance separating star1 and star2"),
    )
    family = models.PositiveIntegerField(_("family score"), default=0)
    pictures = models.PositiveIntegerField(_("pictures score"), default=0)
    clubs = models.PositiveIntegerField(_("clubs score"), default=0)

    def __str__(self):
        return f"{self.star1} -> {self.star2} ({self.distance})"


class StarDict(TypedDict):
    id: int
    name: str
    mass: int


class GalaxyDict(TypedDict):
    nodes: list[StarDict]
    links: list


class RelationScore(NamedTuple):
    family: int
    pictures: int
    clubs: int


class Galaxy(models.Model):
    """The Galaxy, a graph linking the active users between each others.

    The distance between two users is given by a relation score which takes
    into account a few parameter like the number of pictures they are both tagged on,
    the time during which they were in the same clubs and whether they are
    in the same family.

    The citizens of the Galaxy are represented by :class:`GalaxyStar`
    and their relations by :class:`GalaxyLane`.

    Several galaxies can coexist. In this case, only the most recent active one
    shall usually be taken into account.
    This is useful to keep the current galaxy while generating a new one
    and swapping them only at the very end.

    Please take into account that generating the galaxy is a very expensive
    operation. For this reason, try not to call the :meth:`rule` method more
    than once a day in production.

    To quickly access to the state of a galaxy, use the :attr:`state` attribute.
    """

    logger = logging.getLogger("main")

    GALAXY_SCALE_FACTOR = 2_000
    DEFAULT_PICTURE_COUNT_THRESHOLD = 10
    FAMILY_LINK_POINTS = 366  # Equivalent to a leap year together in a club, because.
    PICTURE_POINTS = 2  # Equivalent to two days as random members of a club.
    CLUBS_POINTS = 1  # One day together as random members in a club is one point.

    state = models.JSONField(_("The galaxy current state"), null=True)

    class Meta:
        ordering = ["pk"]

    def __str__(self):
        stars_count = self.stars.count()
        s = f"GLX-ID{self.pk}-SC{stars_count}-"
        if self.state is None:
            s += "CHAOS"
        else:
            s += "RULED"
        return s

    @classmethod
    def get_current_galaxy(cls) -> Galaxy:
        return Galaxy.objects.filter(state__isnull=False).last()

    ###################
    # User self score #
    ###################

    @classmethod
    def get_rulable_users(
        cls, picture_count_threshold: int = DEFAULT_PICTURE_COUNT_THRESHOLD
    ) -> QuerySet[User]:
        return (
            User.objects.filter(is_viewable=True)
            .exclude(subscriptions=None)
            .annotate(
                pictures_count=Count("pictures"),
                is_active_in_galaxy=Exists(
                    Subscription.objects.filter(
                        member=OuterRef("id"), subscription_end__gt=now()
                    )
                ),
            )
            .filter(pictures_count__gt=picture_count_threshold)
            .distinct()
        )

    @classmethod
    def compute_individual_scores(cls) -> dict[int, int]:
        """Compute an individual score for each citizen.

        It will later be used by the graph algorithm to push
        higher scores towards the center of the galaxy.

        Idea: This could be added to the computation:

        - Picture count
        - Counter consumption
        - Barman time
        - ...
        """
        users = (
            User.objects.annotate(
                score=(
                    Count("godchildren", distinct=True) * cls.FAMILY_LINK_POINTS
                    + Count("godfathers", distinct=True) * cls.FAMILY_LINK_POINTS
                    + Count("pictures", distinct=True) * cls.PICTURE_POINTS
                    + Count("memberships", distinct=True) * cls.CLUBS_POINTS
                )
            )
            .filter(score__gt=0)
            .values("id", "score")
        )
        # TODO:
        # Scale that value with some magic number to accommodate to typical data
        # Really active galaxy citizen after 5 years typically have a score of about XXX
        # Citizen that were seen regularly without taking much part in organizations typically have a score of about XXX
        # Citizen that only went to a few events typically score about XXX
        res = {u["id"]: int(math.log2(u["score"] + 1)) for u in users}
        return res

    ####################
    # Inter-user score #
    ####################

    @classmethod
    def compute_user_family_score(cls, user: User) -> defaultdict[int, int]:
        """Compute the family score of the relation between the given users.

        This takes into account mutual godfathers.
        """
        godchildren = User.objects.filter(godchildren=user).values_list("id", flat=True)
        godfathers = User.objects.filter(godfathers=user).values_list("id", flat=True)
        result = defaultdict(int)
        for parent in itertools.chain(godchildren, godfathers):
            result[parent] += cls.FAMILY_LINK_POINTS
        return result

    @classmethod
    def compute_user_pictures_score(cls, user: User) -> defaultdict[int, int]:
        """Compute the pictures score of the relation between the given users.

        The pictures score is obtained by counting the number
        of :class:`Picture` in which they have been both identified.
        This score is then multiplied by 2.

        Returns:
             The number of pictures both users have in common, times 2
        """
        common_photos = (
            PeoplePictureRelation.objects.filter(
                picture__in=Picture.objects.filter(people__user=user)
            )
            .values("user")
            .annotate(count=Count("user"))
        )
        return defaultdict(
            int, {p["user"]: p["count"] * cls.PICTURE_POINTS for p in common_photos}
        )

    @classmethod
    def compute_user_clubs_score(cls, user: User) -> defaultdict[int, int]:
        """Compute the clubs score of the relation between the given users.

        The club score is obtained by counting the number of days
        during which the memberships (see :class:`club.models.Membership`)
        of both users overlapped.

        For example, if user1 was a member of Unitec from 01/01/2020 to 31/12/2021
        (two years) and user2 was a member of the same club from 01/01/2021 to
        31/12/2022 (also two years, but with an offset of one year), then their
        club score is 365.
        """
        memberships = user.memberships.values("start_date", "end_date", "club_id")
        result = defaultdict(int)
        today = localdate()
        for membership in memberships:
            # This is a N+1 query, but 92% of galaxy users have less than 10 memberships.
            # Only 5 users have more than 30 memberships.
            common_memberships = (
                Membership.objects.exclude(user=user)
                .filter(
                    Q(  # start2 <= start1 <= end2
                        start_date__lte=membership["start_date"],
                        end_date__gte=membership["start_date"],
                    )
                    | Q(  # start2 <= start1 <= today
                        start_date__lte=membership["start_date"], end_date=None
                    )
                    | Q(  # start1 <= start2 <= end2
                        start_date__gte=membership["start_date"],
                        start_date__lte=membership["end_date"] or today,
                    ),
                    club_id=membership["club_id"],
                )
                .only("start_date", "end_date", "user_id")
            )
            for other in common_memberships:
                start = max(membership["start_date"], other.start_date)
                end = min(membership["end_date"] or today, other.end_date or today)
                result[other.user_id] += (end - start).days * cls.CLUBS_POINTS
        return result

    ###################
    # Rule the galaxy #
    ###################

    @classmethod
    def scale_distance(cls, value: int | float) -> int:
        """Given a numeric value, return a scaled value which can
        be used in the Galaxy's graphical interface to set the distance
        between two stars.

        Returns:
            the scaled value usable in the Galaxy's 3d graph
        """
        # TODO: this will need adjustements with the real, typical data on Taiste
        if value == 0:
            return 4000  # Following calculus would give us +∞, we cap it to 4000

        cls.logger.debug(f"\t\t> Score: {value}")
        # Invert score to draw close users together
        value = 1 / value  # Cannot be 0
        value += 2  # We use log2 just below and need to stay above 1
        value = (  # Let's get something in the range ]0; log2(3)-1≈0.58[ that we can multiply later
            math.log2(value) - 1
        )
        value *= (  # Scale that value with a magic number to accommodate to typical data
            # Really close galaxy citizen after 5 years typically have a score of about XXX
            # Citizen that were in the same year without being really friends typically have a score of about XXX
            # Citizen that have met once or twice only have a couple of pictures together typically score about XXX
            cls.GALAXY_SCALE_FACTOR
        )
        cls.logger.debug(f"\t\t> Scaled distance: {value}")
        return int(value)

    def rule(
        self, picture_count_threshold: int = DEFAULT_PICTURE_COUNT_THRESHOLD
    ) -> None:
        """Main function of the Galaxy.

        Iterate over all the rulable users to promote them to citizens.
        A citizen is a user who has a corresponding star in the Galaxy.
        Also build up the lanes, which are the links between the different citizen.

        Users who can be ruled are defined with the `picture_count_threshold`:
        all users who are identified in a strictly lower number of pictures
        won't be promoted to citizens.
        This does very effectively limit the quantity of computing to do
        and only includes users who have had a minimum of activity.

        This method still remains very expensive, so think thoroughly before
        you call it, especially in production.

        :param picture_count_threshold: the minimum number of picture to have to be
                                        included in the galaxy
        """
        total_time = time.time()
        self.logger.info("Listing rulable citizen.")

        # force fetch of the whole query to make sure there won't
        # be any more db hits
        # this is memory expensive but prevents a lot of db hits, therefore
        # is far more time efficient

        rulable_users_qs = self.get_rulable_users(picture_count_threshold)
        active_users_count = rulable_users_qs.filter(is_active_in_galaxy=True).count()
        rulable_users = list(rulable_users_qs)
        user1_count = 0
        self.logger.info(
            f" {len(rulable_users)} citizens (with {active_users_count} active ones) "
            f"have been listed. Starting to rule."
        )

        self.logger.info("Creating stars for all citizen")
        individual_scores = self.compute_individual_scores()
        GalaxyStar.objects.bulk_create(
            [
                GalaxyStar(
                    owner_id=user.id, galaxy=self, mass=individual_scores[user.id]
                )
                for user in rulable_users
            ]
        )
        stars = {star.owner_id: star for star in self.stars.all()}

        self.logger.info("Creating lanes between stars")
        global_avg_speed_accumulator = 0
        global_avg_speed_count = 0
        t_global_start = time.time()
        while len(rulable_users) > 0:
            user1 = rulable_users.pop()
            if not user1.is_active_in_galaxy:
                continue
            user1_count += 1
            star1 = stars[user1.id]

            lanes = []
            family_scores = self.compute_user_family_score(user1)
            picture_scores = self.compute_user_pictures_score(user1)
            club_scores = self.compute_user_clubs_score(user1)

            for user2 in rulable_users:
                star2 = stars[user2.id]

                score = RelationScore(
                    family=family_scores.get(user2.id, 0),
                    pictures=picture_scores.get(user2.id, 0),
                    clubs=club_scores.get(user2.id, 0),
                )
                distance = self.scale_distance(sum(score))
                if distance < 30:  # TODO: this needs tuning with real-world data
                    lanes.append(
                        GalaxyLane(
                            star1=star1,
                            star2=star2,
                            distance=distance,
                            family=score.family,
                            pictures=score.pictures,
                            clubs=score.clubs,
                        )
                    )
            GalaxyLane.objects.bulk_create(lanes)

            t_global_end = time.time()
            global_delta = t_global_end - t_global_start
            speed = 1.0 / global_delta
            global_avg_speed_accumulator += speed
            global_avg_speed_count += 1
            global_avg_speed = global_avg_speed_accumulator / global_avg_speed_count

            if user1_count % 50 == 0:
                self.logger.info("")
                self.logger.info(f" Ruling of {self} ".center(60, "#"))
                self.logger.info(
                    f"Progression: {user1_count}/{active_users_count} "
                    f"citizen -- {active_users_count - user1_count} remaining"
                )
                self.logger.info(f"Speed: {global_avg_speed:.2f} citizen per second")
                eta = len(rulable_users) // global_avg_speed
                self.logger.info(
                    f"ETA: {int(eta // 60 % 60)} minutes {int(eta % 60)} seconds"
                )
                self.logger.info("#" * 60)
            t_global_start = time.time()

        count, _ = self.stars.filter(Q(lanes1=None) & Q(lanes2=None)).delete()
        self.logger.info(f"{count} orphan stars have been trimmed.")

        # Here, we get the IDs of the old galaxies that we'll need to delete. In normal operation, only one galaxy
        # should be returned, and we can't delete it yet, as it's the one still displayed by the Sith.
        old_galaxies_pks = list(
            Galaxy.objects.filter(state__isnull=False).values_list("pk", flat=True)
        )
        self.logger.info(
            f"These old galaxies will be deleted once the new one is ready: {old_galaxies_pks}"
        )

        # Making the state sets this new galaxy as being ready. From now on, the Sith will show us to the world.
        self.make_state()

        # Avoid accident if there is nothing to delete
        if len(old_galaxies_pks) > 0:
            # Former galaxies can now be deleted.
            Galaxy.objects.filter(pk__in=old_galaxies_pks).delete()

        total_time = time.time() - total_time
        total_time_minutes = int(total_time // 60 % 60)
        total_time_seconds = int(total_time % 60)
        self.logger.info(
            f"{self} ruled in {total_time_minutes} minutes, {total_time_seconds} seconds"
        )

    def make_state(self) -> None:
        """Compute JSON structure to send to 3d-force-graph: https://github.com/vasturiano/3d-force-graph/."""
        self.logger.info(
            "Caching current Galaxy state for a quicker display of the Empire's power."
        )
        stars = (
            GalaxyStar.objects.filter(galaxy=self)
            .order_by("owner_id")
            .select_related("owner")
        )
        lanes = (
            GalaxyLane.objects.filter(star1__galaxy=self)
            .order_by("star1")
            .annotate(
                star1_owner=F("star1__owner_id"), star2_owner=F("star2__owner_id")
            )
        )
        json = GalaxyDict(
            nodes=[
                StarDict(
                    id=star.owner_id, name=star.owner.get_display_name(), mass=star.mass
                )
                for star in stars
            ],
            links=[
                {
                    "source": path.star1_owner,
                    "target": path.star2_owner,
                    "value": path.distance,
                }
                for path in lanes
            ],
        )
        self.state = json
        self.save()
        self.logger.info(f"{self} is now ready!")
