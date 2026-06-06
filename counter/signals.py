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
import random

from django.db.models.signals import pre_delete
from django.dispatch import receiver

from core.middleware import get_signal_request
from core.models import OperationLog
from counter.models import Refilling, Selling


def write_log(instance: Selling | Refilling, operation_type):
    def get_user():
        request = get_signal_request()

        if not request:
            return None

        if request.barmen:
            return random.choice(list(request.barmen))

        # Get the current logged user if not from a counter
        if request.user.is_authenticated:
            return request.user

        return None

    OperationLog(
        label=str(instance), operator=get_user(), operation_type=operation_type
    ).save()


@receiver(pre_delete, sender=Refilling, dispatch_uid="write_log_refilling_deletion")
def write_log_refilling_deletion(sender, instance, **kwargs):
    write_log(instance, "REFILLING_DELETION")


@receiver(pre_delete, sender=Selling, dispatch_uid="write_log_refilling_deletion")
def write_log_selling_deletion(sender, instance, **kwargs):
    write_log(instance, "SELLING_DELETION")
