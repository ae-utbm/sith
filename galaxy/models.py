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
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from core.models import User
from club.models import Membership


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
    This class defines a lane (edge -> link between galaxy citizen) in the galaxy map, storing a reference to both its
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


class Galaxy:
    GALAXY_SCALE_FACTOR = 2_000
    FAMILY_LINK_POINTS = 366  # Equivalent to a leap year together in a club, because.
    PICTURE_POINTS = 2  # Equivalent to two days as random members of a club.
    CLUBS_POINTS = 1  # One day together as random members in a club is one point.

    def as_dict(self):
        """
        Compute JSON structure to send to 3d-force-graph: https://github.com/vasturiano/3d-force-graph/
        """
        json = {
            "nodes": [
                {"id": star.owner.id, "name": star.owner.get_display_name()}
                for star in GalaxyStar.objects.all()
            ],
            "links": [],
        }

        # Make bidirectional links
        # TODO: see if this impacts performance with a big graph
        for path in GalaxyLane.objects.all():
            json["links"].append(
                {
                    "source": path.star1.owner.id,
                    "target": path.star2.owner.id,
                    "value": path.distance,
                }
            )
            json["links"].append(
                {
                    "source": path.star2.owner.id,
                    "target": path.star1.owner.id,
                    "value": path.distance,
                }
            )
        return json

    ###################
    # User self score #
    ###################

    def compute_user_score(self, user):
        user_score = 0
        user_score += self.compute_user_family_score(user)
        user_score += self.compute_user_pictures_score(user)
        user_score += self.compute_user_clubs_score(user)
        return user_score

    def compute_user_family_score(self, user):
        user_family_score = (
            user.godfathers.count() + user.godchildren.count()
        ) * self.FAMILY_LINK_POINTS
        return user_family_score

    def compute_user_pictures_score(self, user):
        user_pictures_score = user.pictures.count() * self.PICTURE_POINTS
        return user_pictures_score

    def compute_user_clubs_score(self, user):
        user_clubs_score = user.memberships.count() * self.CLUBS_POINTS
        return user_clubs_score

    ####################
    # Inter-user score #
    ####################

    def compute_users_score(self, user1, user2):
        family = self.compute_users_family_score(user1, user2)
        pictures = self.compute_users_pictures_score(user1, user2)
        clubs = self.compute_users_clubs_score(user1, user2)
        score = family + pictures + clubs
        return score, family, pictures, clubs

    def compute_users_family_score(self, user1, user2):
        score = 0
        link_count = User.objects.filter(
            Q(id=user1.id, godfathers=user2) | Q(id=user2.id, godfathers=user1)
        ).count()
        if link_count > 0:
            score += link_count * self.FAMILY_LINK_POINTS
            print(
                "    - '%s' and '%s' have %s direct family link"
                % (user1, user2, link_count)
            )
        return score

    def compute_users_pictures_score(self, user1, user2):
        score = 0
        for picture_relation in user1.pictures.all():
            try:
                picture_relation.picture.people.get(user=user2)
                print("    - '%s' was pictured with '%s'" % (user1, user2))
                score += self.PICTURE_POINTS
            except picture_relation.__class__.DoesNotExist:
                pass
        return score

    def compute_users_clubs_score(self, user1, user2):
        score = 0
        common_clubs = user1.memberships.values("club").distinct()
        user1_memberships = Membership.objects.filter(
            club__in=common_clubs, user=user1
        ).distinct()
        user2_memberships = Membership.objects.filter(
            club__in=common_clubs, user=user2
        ).distinct()

        for user1_membership in user1_memberships:
            if user1_membership.end_date is None:
                user1_membership.end_date = timezone.now().date()
            print(
                "    - Checking range [%s, %s] for club %s"
                % (
                    user1_membership.start_date,
                    user1_membership.end_date,
                    user1_membership.club,
                )
            )
            query = Q(  # Memberships where the range contains s1
                start_date__lte=user1_membership.start_date,
                end_date__gte=user1_membership.start_date,
            )
            query |= Q(  # Memberships starting before s1 and still unfinished
                start_date__lte=user1_membership.start_date, end_date=None
            )
            query |= Q(  # Memberships starting in [s1, e1]
                start_date__gte=user1_membership.start_date,
                start_date__lte=user1_membership.end_date,
            )
            for user2_membership in user2_memberships.filter(
                query, club=user1_membership.club
            ).all():
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
                score += self.CLUBS_POINTS * (earliest_end - latest_start).days
        return score

    ###################
    # Rule the galaxy #
    ###################

    def is_user_rulable(self, user):
        """
        Computing simple incomplete self scores is useless for now, but avoids ruling too many citizen against each other
        """
        return self.compute_user_score(user) > 0

    def rule(self):
        GalaxyStar.objects.all().delete()
        GalaxyLane.objects.all().delete()
        ruled_users = []
        for user1 in User.objects.all():
            ruled_users.append(user1.id)
            if self.is_user_rulable(user1):
                for user2 in User.objects.exclude(id__in=ruled_users):
                    if not self.is_user_rulable(user2):
                        ruled_users.append(user2.id)  # Ban citizen from further ruling
                    else:
                        print("\n  > Ruling '{}' against '{}'".format(user1, user2))
                        star1, _ = GalaxyStar.objects.get_or_create(owner=user1)
                        star2, _ = GalaxyStar.objects.get_or_create(owner=user2)
                        users_score, family, pictures, clubs = self.compute_users_score(
                            user1, user2
                        )
                        if users_score > 0:
                            GalaxyLane(
                                star1=star1,
                                star2=star2,
                                distance=self.scale_distance(users_score),
                                family=family,
                                pictures=pictures,
                                clubs=clubs,
                            ).save()

    def scale_distance(self, value):
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
            # Citizen that have met once or twice have only have a couple of pictures together typically score about XXX
            self.GALAXY_SCALE_FACTOR
        )
        print("    > Scaled distance:", value)
        return int(value)
