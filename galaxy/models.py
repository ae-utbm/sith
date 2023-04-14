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

import math
import logging
import time

from typing import List, Tuple, TypedDict

from django.db import models
from django.db.models import Q, Case, F, Value, When, Count
from django.db.models.functions import Concat
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from core.models import User
from club.models import Club
from sas.models import Picture


class GalaxyStar(models.Model):
    """
    This class defines a star (vertex -> user) in the galaxy graph, storing a reference to its owner citizen, and being
    referenced by GalaxyLane.

    It also stores the individual mass of this star, used to push it towards the center of the galaxy.
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
def current_star(self):
    return self.stars.filter(galaxy__state__isnull=False).order_by("galaxy").last()


# Adding a shortcut to User class for getting its star belonging to the latest ruled Galaxy
setattr(User, "current_star", current_star)


class GalaxyLane(models.Model):
    """
    This class defines a lane (edge -> link between galaxy citizen) in the galaxy map, storing a reference to both its
    ends and the distance it covers.
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
    family = models.PositiveIntegerField(
        _("family score"),
        default=0,
    )
    pictures = models.PositiveIntegerField(
        _("pictures score"),
        default=0,
    )
    clubs = models.PositiveIntegerField(
        _("clubs score"),
        default=0,
    )


class StarDict(TypedDict):
    id: int
    name: str
    mass: int


class GalaxyDict(TypedDict):
    nodes: List[StarDict]
    links: List


class Galaxy(models.Model):
    logger = logging.getLogger("main")

    GALAXY_SCALE_FACTOR = 2_000
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
            s += "CHS"  # CHAOS
        else:
            s += "RLD"  # RULED
        return s

    ###################
    # User self score #
    ###################

    @classmethod
    def compute_user_score(cls, user) -> int:
        """
        This compute an individual score for each citizen. It will later be used by the graph algorithm to push
        higher scores towards the center of the galaxy.

        Idea: This could be added to the computation:
              - Forum posts
              - Picture count
              - Counter consumption
              - Barman time
              - ...
        """
        user_score = 1
        user_score += cls.query_user_score(user)

        # TODO:
        # Scale that value with some magic number to accommodate to typical data
        # Really active galaxy citizen after 5 years typically have a score of about XXX
        # Citizen that were seen regularly without taking much part in organizations typically have a score of about XXX
        # Citizen that only went to a few events typically score about XXX
        user_score = int(math.log2(user_score))

        return user_score

    @classmethod
    def query_user_score(cls, user) -> int:
        score_query = (
            User.objects.filter(id=user.id)
            .annotate(
                godchildren_count=Count("godchildren", distinct=True)
                * cls.FAMILY_LINK_POINTS,
                godfathers_count=Count("godfathers", distinct=True)
                * cls.FAMILY_LINK_POINTS,
                pictures_score=Count("pictures", distinct=True) * cls.PICTURE_POINTS,
                clubs_score=Count("memberships", distinct=True) * cls.CLUBS_POINTS,
            )
            .aggregate(
                score=models.Sum(
                    F("godchildren_count")
                    + F("godfathers_count")
                    + F("pictures_score")
                    + F("clubs_score")
                )
            )
        )
        return score_query.get("score")

    ####################
    # Inter-user score #
    ####################

    @classmethod
    def compute_users_score(cls, user1, user2) -> Tuple[int, int, int, int]:
        family = cls.compute_users_family_score(user1, user2)
        pictures = cls.compute_users_pictures_score(user1, user2)
        clubs = cls.compute_users_clubs_score(user1, user2)
        score = family + pictures + clubs
        return score, family, pictures, clubs

    @classmethod
    def compute_users_family_score(cls, user1, user2) -> int:
        link_count = User.objects.filter(
            Q(id=user1.id, godfathers=user2) | Q(id=user2.id, godfathers=user1)
        ).count()
        if link_count:
            cls.logger.debug(
                f"\t\t- '{user1}' and '{user2}' have {link_count} direct family link"
            )
        return link_count * cls.FAMILY_LINK_POINTS

    @classmethod
    def compute_users_pictures_score(cls, user1, user2) -> int:
        picture_count = (
            Picture.objects.filter(people__user__in=(user1,))
            .filter(people__user__in=(user2,))
            .count()
        )
        if picture_count:
            cls.logger.debug(
                f"\t\t- '{user1}' was pictured with '{user2}' {picture_count} times"
            )
        return picture_count * cls.PICTURE_POINTS

    @classmethod
    def compute_users_clubs_score(cls, user1, user2) -> int:
        common_clubs = Club.objects.filter(members__in=user1.memberships.all()).filter(
            members__in=user2.memberships.all()
        )
        user1_memberships = user1.memberships.filter(club__in=common_clubs)
        user2_memberships = user2.memberships.filter(club__in=common_clubs)

        score = 0
        for user1_membership in user1_memberships:
            if user1_membership.end_date is None:
                user1_membership.end_date = timezone.now().date()
            query = Q(  # start2 <= start1 <= end2
                start_date__lte=user1_membership.start_date,
                end_date__gte=user1_membership.start_date,
            )
            query |= Q(  # start2 <= start1 <= now
                start_date__lte=user1_membership.start_date, end_date=None
            )
            query |= Q(  # start1 <= start2 <= end2
                start_date__gte=user1_membership.start_date,
                start_date__lte=user1_membership.end_date,
            )
            for user2_membership in user2_memberships.filter(
                query, club=user1_membership.club
            ):
                if user2_membership.end_date is None:
                    user2_membership.end_date = timezone.now().date()
                latest_start = max(
                    user1_membership.start_date, user2_membership.start_date
                )
                earliest_end = min(user1_membership.end_date, user2_membership.end_date)
                cls.logger.debug(
                    "\t\t- '%s' was with '%s' in %s starting on %s until %s (%s days)"
                    % (
                        user1,
                        user2,
                        user2_membership.club,
                        latest_start,
                        earliest_end,
                        (earliest_end - latest_start).days,
                    )
                )
                score += cls.CLUBS_POINTS * (earliest_end - latest_start).days
        return score

    ###################
    # Rule the galaxy #
    ###################

    @classmethod
    def scale_distance(cls, value) -> int:
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

    def rule(self, picture_count_threshold=10) -> None:
        """
        This is the main function of the Galaxy.
        It iterates over all the rulable users to promote them to citizen, which is a user that has a corresponding star in the Galaxy.
        It also builds up the lanes, which are the links between the different citizen.

        Rulable users are defined with the `picture_count_threshold`: any user that doesn't match that limit won't be
        considered to be promoted to citizen. This very effectively limits the quantity of computing to do, and only includes
        users that have had a minimum of activity.
        """
        total_time = time.time()
        self.logger.info("Listing rulable citizen.")
        rulable_users = (
            User.objects.filter(subscriptions__isnull=False)
            .annotate(pictures_count=Count("pictures"))
            .filter(pictures_count__gt=picture_count_threshold)
            .distinct()
        )

        # force fetch of the whole query to make sure there won't
        # be any more db hits
        # this is memory expensive but prevents a lot of db hits, therefore
        # is far more time efficient

        rulable_users = list(rulable_users)
        rulable_users_count = len(rulable_users)
        user1_count = 0
        self.logger.info(
            f"{rulable_users_count} citizen have been listed. Starting to rule."
        )

        stars = GalaxyStar.objects.filter(galaxy=self)

        # Display current speed every $speed_count_frequency users
        speed_count_frequency = max(rulable_users_count // 10, 1)  # ten time at most
        global_avg_speed_accumulator = 0
        global_avg_speed_count = 0
        t_global_start = time.time()
        while len(rulable_users) > 0:
            user1 = rulable_users.pop()
            user1_count += 1
            rulable_users_count2 = len(rulable_users)

            star1, created = stars.get_or_create(owner=user1)

            if created:
                star1.galaxy = self
                star1.save()

            if star1.mass == 0:
                star1.mass = self.compute_user_score(user1)
                star1.save()

            user_avg_speed = 0
            user_avg_speed_count = 0

            tstart = time.time()
            for user2_count, user2 in enumerate(rulable_users, start=1):
                self.logger.debug("")
                self.logger.debug(
                    f"\t> Examining '{user1}' ({user1_count}/{rulable_users_count}) with '{user2}' ({user2_count}/{rulable_users_count2})"
                )
                star2, created = stars.get_or_create(owner=user2)

                if created:
                    star2.galaxy = self
                    star2.save()

                users_score, family, pictures, clubs = Galaxy.compute_users_score(
                    user1, user2
                )
                distance = self.scale_distance(users_score)
                if distance < 30:  # TODO: this needs tuning with real-world data
                    GalaxyLane(
                        star1=star1,
                        star2=star2,
                        distance=distance,
                        family=family,
                        pictures=pictures,
                        clubs=clubs,
                    ).save()

                if user2_count % speed_count_frequency == 0:
                    tend = time.time()
                    delta = tend - tstart
                    speed = float(speed_count_frequency) / delta
                    user_avg_speed += speed
                    user_avg_speed_count += 1
                    self.logger.debug(
                        f"\tSpeed: {speed:.2f} users per second (time for last {speed_count_frequency} citizens: {delta:.2f} second)"
                    )
                    tstart = time.time()

            self.logger.info("")

            t_global_end = time.time()
            global_delta = t_global_end - t_global_start
            speed = 1.0 / global_delta
            global_avg_speed_accumulator += speed
            global_avg_speed_count += 1
            global_avg_speed = global_avg_speed_accumulator / global_avg_speed_count

            self.logger.info(f" Ruling of {self} ".center(60, "#"))
            self.logger.info(
                f"Progression: {user1_count}/{rulable_users_count} citizen -- {rulable_users_count - user1_count} remaining"
            )
            self.logger.info(f"Speed: {60.0*global_avg_speed:.2f} citizen per minute")

            # We can divide the computed ETA by 2 because each loop, there is one citizen less to check, and maths tell
            # us that this averages to a division by two
            eta = rulable_users_count2 / global_avg_speed / 2
            eta_hours = int(eta // 3600)
            eta_minutes = int(eta // 60 % 60)
            self.logger.info(
                f"ETA: {eta_hours} hours {eta_minutes} minutes ({eta / 3600 / 24:.2f} days)"
            )
            self.logger.info("#" * 60)
            t_global_start = time.time()

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
        total_time_hours = int(total_time // 3600)
        total_time_minutes = int(total_time // 60 % 60)
        total_time_seconds = int(total_time % 60)
        self.logger.info(
            f"{self} ruled in {total_time:.2f} seconds ({total_time_hours} hours, {total_time_minutes} minutes, {total_time_seconds} seconds)"
        )

    def make_state(self) -> None:
        """
        Compute JSON structure to send to 3d-force-graph: https://github.com/vasturiano/3d-force-graph/
        """
        self.logger.info(
            "Caching current Galaxy state for a quicker display of the Empire's power."
        )

        without_nickname = Concat(
            F("owner__first_name"), Value(" "), F("owner__last_name")
        )
        with_nickname = Concat(
            F("owner__first_name"),
            Value(" "),
            F("owner__last_name"),
            Value(" ("),
            F("owner__nick_name"),
            Value(")"),
        )
        stars = GalaxyStar.objects.filter(galaxy=self).annotate(
            owner_name=Case(
                When(owner__nick_name=None, then=without_nickname),
                default=with_nickname,
            )
        )
        lanes = GalaxyLane.objects.filter(star1__galaxy=self).annotate(
            star1_owner=F("star1__owner__id"),
            star2_owner=F("star2__owner__id"),
        )
        json = GalaxyDict(
            nodes=[
                StarDict(
                    id=star.owner_id,
                    name=star.owner_name,
                    mass=star.mass,
                )
                for star in stars
            ],
            links=[],
        )
        for path in lanes:
            json["links"].append(
                {
                    "source": path.star1_owner,
                    "target": path.star2_owner,
                    "value": path.distance,
                }
            )
        self.state = json
        self.save()
        self.logger.info(f"{self} is now ready!")
