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

from __future__ import annotations

import logging
import math
import time
from typing import List, NamedTuple, Optional, TypedDict, Union

from django.db import models
from django.db.models import Case, Count, F, Q, Value, When
from django.db.models.functions import Concat
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from club.models import Club
from core.models import User
from sas.models import Picture


class GalaxyStar(models.Model):
    """
    Define a star (vertex -> user) in the galaxy graph,
    storing a reference to its owner citizen.

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
def current_star(self) -> Optional[GalaxyStar]:
    """
    The star of this user in the :class:`Galaxy`.
    Only take into account the most recent active galaxy.

    :return: The star of this user if there is an active Galaxy
             and this user is a citizen of it, else ``None``
    """
    return self.stars.filter(galaxy=Galaxy.get_current_galaxy()).last()


# Adding a shortcut to User class for getting its star belonging to the latest ruled Galaxy
setattr(User, "current_star", current_star)


class GalaxyLane(models.Model):
    """
    Define a lane (edge -> link between galaxy citizen)
    in the galaxy map, storing a reference to both its
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


class RelationScore(NamedTuple):
    family: int
    pictures: int
    clubs: int


class Galaxy(models.Model):
    """
    The Galaxy, a graph linking the active users between each others.
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

    @classmethod
    def get_current_galaxy(
        cls,
    ) -> Galaxy:  # __future__.annotations is required for this
        return Galaxy.objects.filter(state__isnull=False).last()

    ###################
    # User self score #
    ###################

    @classmethod
    def compute_user_score(cls, user: User) -> int:
        """
        Compute an individual score for each citizen.
        It will later be used by the graph algorithm to push
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
    def query_user_score(cls, user: User) -> int:
        """
        Perform the db query to get the  individual score
        of the given user in the galaxy.
        """
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
    def compute_users_score(cls, user1: User, user2: User) -> RelationScore:
        """
        Compute the relationship scores of the two given users
        in the following fields :

        - family: if they have some godfather/godchild relation
        - pictures: in how many pictures are both tagged
        - clubs: during how many days they were members of the same clubs
        """
        family = cls.compute_users_family_score(user1, user2)
        pictures = cls.compute_users_pictures_score(user1, user2)
        clubs = cls.compute_users_clubs_score(user1, user2)
        return RelationScore(family=family, pictures=pictures, clubs=clubs)

    @classmethod
    def compute_users_family_score(cls, user1: User, user2: User) -> int:
        """
        Compute the family score of the relation between the given users.
        This takes into account mutual godfathers.

        :return: 366 if user1 is the godfather of user2 (or vice versa) else 0
        """
        link_count = User.objects.filter(
            Q(id=user1.id, godfathers=user2) | Q(id=user2.id, godfathers=user1)
        ).count()
        if link_count > 0:
            cls.logger.debug(
                f"\t\t- '{user1}' and '{user2}' have {link_count} direct family link"
            )
        return link_count * cls.FAMILY_LINK_POINTS

    @classmethod
    def compute_users_pictures_score(cls, user1: User, user2: User) -> int:
        """
        Compute the pictures score of the relation between the given users.

        The pictures score is obtained by counting the number
        of :class:`Picture` in which they have been both identified.
        This score is then multiplied by 2.

        :return: The number of pictures both users have in common, times 2
        """
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
    def compute_users_clubs_score(cls, user1: User, user2: User) -> int:
        """
        Compute the clubs score of the relation between the given users.

        The club score is obtained by counting the number of days
        during which the memberships (see :class:`club.models.Membership`)
        of both users overlapped.

        For example, if user1 was a member of Unitec from 01/01/2020 to 31/12/2021
        (two years) and user2 was a member of the same club from 01/01/2021 to
        31/12/2022 (also two years, but with an offset of one year), then their
        club score is 365.

        :return: the number of days during which both users were in the same club
        """
        common_clubs = Club.objects.filter(members__in=user1.memberships.all()).filter(
            members__in=user2.memberships.all()
        )
        user1_memberships = user1.memberships.filter(club__in=common_clubs)
        user2_memberships = user2.memberships.filter(club__in=common_clubs)

        score = 0
        for user1_membership in user1_memberships:
            if user1_membership.end_date is None:
                # user1_membership.save() is not called in this function, hence this is safe
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
    def scale_distance(cls, value: Union[int, float]) -> int:
        """
        Given a numeric value, return a scaled value which can
        be used in the Galaxy's graphical interface to set the distance
        between two stars

        :return: the scaled value usable in the Galaxy's 3d graph
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

    def rule(self, picture_count_threshold=10) -> None:
        """
        Main function of the Galaxy.
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

        stars = []
        self.logger.info("Creating stars for all citizen")
        for user in rulable_users:
            star = GalaxyStar(
                owner=user, galaxy=self, mass=self.compute_user_score(user)
            )
            stars.append(star)
        GalaxyStar.objects.bulk_create(stars)

        stars = {}
        for star in GalaxyStar.objects.filter(galaxy=self):
            stars[star.owner.id] = star

        self.logger.info("Creating lanes between stars")
        # Display current speed every $speed_count_frequency users
        speed_count_frequency = max(rulable_users_count // 10, 1)  # ten time at most
        global_avg_speed_accumulator = 0
        global_avg_speed_count = 0
        t_global_start = time.time()
        while len(rulable_users) > 0:
            user1 = rulable_users.pop()
            user1_count += 1
            rulable_users_count2 = len(rulable_users)

            star1 = stars[user1.id]

            user_avg_speed = 0
            user_avg_speed_count = 0

            tstart = time.time()
            lanes = []
            for user2_count, user2 in enumerate(rulable_users, start=1):
                self.logger.debug("")
                self.logger.debug(
                    f"\t> Examining '{user1}' ({user1_count}/{rulable_users_count}) with '{user2}' ({user2_count}/{rulable_users_count2})"
                )

                star2 = stars[user2.id]

                score = Galaxy.compute_users_score(user1, user2)
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

            GalaxyLane.objects.bulk_create(lanes)

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
        stars = (
            GalaxyStar.objects.filter(galaxy=self)
            .order_by(
                "owner"
            )  # This helps determinism for the tests and doesn't cost much
            .annotate(
                owner_name=Case(
                    When(owner__nick_name=None, then=without_nickname),
                    default=with_nickname,
                )
            )
        )
        lanes = (
            GalaxyLane.objects.filter(star1__galaxy=self)
            .order_by(
                "star1"
            )  # This helps determinism for the tests and doesn't cost much
            .annotate(
                star1_owner=F("star1__owner__id"),
                star2_owner=F("star2__owner__id"),
            )
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
