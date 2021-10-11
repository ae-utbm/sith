# -*- coding:utf-8 -*
#
# Copyright 2019
# - Sli <antoine@bartuccio.fr>
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

from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.conf import settings

from core.middleware import get_signal_request
from core.models import OperationLog

from counter.models import Selling, Refilling, Counter


def write_log(instance, operation_type):
    def get_user():
        request = get_signal_request()

        if not request:
            return None

        # Get a random barmen if deletion is from a counter
        session = getattr(request, "session", {})
        session_token = session.get("counter_token", None)
        if session_token:
            counter = Counter.objects.filter(token=session_token).first()
            if counter and len(counter.get_barmen_list()) > 0:
                return counter.get_random_barman()

        # Get the current logged user if not from a counter
        if request.user and not request.user.is_anonymous:
            return request.user

        # Return None by default
        return None

    log = OperationLog(
        label=str(instance),
        operator=get_user(),
        operation_type=operation_type,
    ).save()


@receiver(pre_delete, sender=Refilling, dispatch_uid="write_log_refilling_deletion")
def write_log_refilling_deletion(sender, instance, **kwargs):
    write_log(instance, "REFILLING_DELETION")


@receiver(pre_delete, sender=Selling, dispatch_uid="write_log_refilling_deletion")
def write_log_selling_deletion(sender, instance, **kwargs):
    write_log(instance, "SELLING_DELETION")
