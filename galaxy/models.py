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

from django.db import models
from django.db.models import Q, Case, F, Value, When
from django.db.models.functions import Concat
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from typing import List, TypedDict

from core.models import User
from club.models import Membership, Club
from sas.models import PeoplePictureRelation, Picture
from subscription.models import Subscription

# TODO : retirer tous les print sauvages et les remplacer par de vrais tests


class GalaxyStar(models.Model):
    """
    This class defines a star (vertex -> user) in the galaxy graph, storing a reference to its owner citizen, and being
    referenced by GalaxyLane.

    Idea: Store an "activity score" here, that would draw stars to the center of the galaxy.
          This could be computed with:
              - Forum posts
              - Picture count
              - Counter consumption
              - Barman time
              - ...
    """

    owner = models.OneToOneField(
        User,
        verbose_name=_("galaxy user"),
        related_name="galaxy_user",
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return str(self.owner)


class GalaxyLane(models.Model):
    """
    This class defines a lane (edge -> link between galaxy citizen)
    in the galaxy map, storing a reference to both its
    ends and the distance it covers.
    Score details between citizen owning the stars is also stored here.
    """

    star1 = models.ForeignKey(
        GalaxyStar,
        verbose_name=_("galaxy lanes 1"),
        related_name="lanes1",
        on_delete=models.CASCADE,
    )
    star2 = models.ForeignKey(
        GalaxyStar,
        verbose_name=_("galaxy lanes 2"),
        related_name="lanes2",
        on_delete=models.CASCADE,
    )
    distance = models.IntegerField(
        _("distance"),
        default=0,
        help_text=_("Distance separating star1 and star2"),
    )
    family = models.IntegerField(
        _("family score"),
        default=0,
    )
    pictures = models.IntegerField(
        _("pictures score"),
        default=0,
    )
    clubs = models.IntegerField(
        _("clubs score"),
        default=0,
    )


class StarDict(TypedDict):
    id: int
    name: str


class GalaxyDict(TypedDict):
    nodes: List[StarDict]
    links: List


class Galaxy:
    GALAXY_SCALE_FACTOR = 2_000
    FAMILY_LINK_POINTS = 366  # Equivalent to a leap year together in a club, because.
    PICTURE_POINTS = 2  # Equivalent to two days as random members of a club.
    CLUBS_POINTS = 1  # One day together as random members in a club is one point.

    @staticmethod
    def as_dict() -> GalaxyDict:
        """
        Compute JSON structure to send to 3d-force-graph: https://github.com/vasturiano/3d-force-graph/
        """
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
        stars = GalaxyStar.objects.annotate(
            owner_name=Case(
                When(owner__nick_name=None, then=without_nickname),
                default=with_nickname,
            )
        )
        lanes = GalaxyLane.objects.annotate(
            star1_owner=F("star1__owner__id"),
            star2_owner=F("star2__owner__id"),
        )
        json = GalaxyDict(
            nodes=[StarDict(id=star.owner_id, name=star.owner_name) for star in stars],
            links=[],
        )
        # Make bidirectional links
        # TODO: see if this impacts performance with a big graph
        for path in lanes:
            json["links"].append(
                {
                    "source": path.star1_owner,
                    "target": path.star2_owner,
                    "value": path.distance,
                }
            )
            json["links"].append(
                {
                    "source": path.star2_owner,
                    "target": path.star1_owner,
                    "value": path.distance,
                }
            )
        return json

    ####################
    # Inter-user score #
    ####################

    @classmethod
    def compute_users_score(cls, user1, user2):
        family = cls.compute_users_family_score(user1, user2)
        pictures = cls.compute_users_pictures_score(user1, user2)
        clubs = cls.compute_users_clubs_score(user1, user2)
        score = family + pictures + clubs
        return score, family, pictures, clubs

    @classmethod
    def compute_users_family_score(cls, user1, user2):
        link_count = User.objects.filter(
            Q(id=user1.id, godfathers=user2) | Q(id=user2.id, godfathers=user1)
        ).count()
        if link_count > 0:
            score = link_count * cls.FAMILY_LINK_POINTS
            print(
                "    - '%s' and '%s' have %s direct family link"
                % (user1, user2, link_count)
            )
            return score
        return 0

    @classmethod
    def compute_users_pictures_score(cls, user1, user2):
        score = (
            Picture.objects.filter(people__user__in=(user1,))
            .filter(people__user__in=(user2,))
            .count()
        )
        for _ in range(score):
            print("    - '%s' was pictured with '%s'" % (user1, user2))
        return score * cls.PICTURE_POINTS

    @classmethod
    def compute_users_clubs_score(cls, user1, user2):
        common_clubs = Club.objects.filter(members__in=user1.memberships.all()).filter(
            members__in=user2.memberships.all()
        )
        user1_memberships = user1.memberships.filter(club__in=common_clubs)
        user2_memberships = user2.memberships.filter(club__in=common_clubs)

        score = 0
        for user1_membership in user1_memberships:
            if user1_membership.end_date is None:
                user1_membership.end_date = timezone.now().date()
            print(
                "\t- Checking range [%s, %s] for club %s"
                % (
                    user1_membership.start_date,
                    user1_membership.end_date,
                    user1_membership.club,
                )
            )
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
                print(
                    "      - '%s' was with '%s' in %s starting on %s until %s (%s days)"
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
    def recompute(cls):
        GalaxyStar.objects.all().delete()
        GalaxyLane.objects.all().delete()
        rulable_users = (
            User.objects.filter(subscriptions__isnull=False)
            .filter(
                Q(godchildren__isnull=False)
                | Q(godfathers__isnull=False)
                | Q(pictures__isnull=False)
                | Q(memberships__isnull=False)
            )
            .distinct()
        )
        # force fetch of the whole query to make sure there won't
        # be any more db hits
        # this is memory expensive but prevents a lot of db hits, therefore
        # is far more time efficient
        rulable_users = list(rulable_users)
        while len(rulable_users) > 0:
            user1 = rulable_users.pop()
            for user2 in rulable_users:
                print(f"\n  > Ruling '{user1}' against '{user2}'")
                star1, _ = GalaxyStar.objects.get_or_create(owner=user1)
                star2, _ = GalaxyStar.objects.get_or_create(owner=user2)
                users_score, family, pictures, clubs = cls.compute_users_score(
                    user1, user2
                )
                if users_score > 0:
                    GalaxyLane(
                        star1=star1,
                        star2=star2,
                        distance=cls.scale_distance(users_score),
                        family=family,
                        pictures=pictures,
                        clubs=clubs,
                    ).save()

    @classmethod
    def scale_distance(cls, value):
        # TODO: this will need adjustements with the real, typical data on Taiste

        print("    > Score:", value)
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
        print("    > Scaled distance:", value)
        return int(value)
