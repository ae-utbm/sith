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

from django.db.models.signals import pre_delete
from django.dispatch import receiver

from core.middleware import get_signal_request
from core.models import OperationLog
from counter.models import Counter, Refilling, Selling


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
