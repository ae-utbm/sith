#
# Copyright 2023 © AE UTBM
# ae@utbm.fr / ae.info@utbm.fr
#
# This file is part of the website of the UTBM Student Association (AE UTBM),
# https://ae.utbm.fr.
#
# You can find the source code of the website at https://github.com/ae-utbm/sith
#
# LICENSED UNDER THE GNU GENERAL PUBLIC LICENSE VERSION 3 (GPLv3)
# SEE : https://raw.githubusercontent.com/ae-utbm/sith/master/LICENSE
# OR WITHIN THE LOCAL FILE "LICENSE"
#
#

from django.db.models import F
from django.http import HttpRequest, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.http import require_POST

from core.views.forms import LoginForm
from counter.models import Counter, Permanency


@require_POST
def counter_login(request: HttpRequest, counter_id: int) -> HttpResponseRedirect:
    """Log a user in a counter.

    A successful login will result in the beginning of a counter duty
    for the user.
    """
    counter = get_object_or_404(Counter, pk=counter_id)
    form = LoginForm(request, data=request.POST)
    if not form.is_valid():
        return redirect(counter.get_absolute_url() + "?credentials")
    user = form.get_user()
    if not counter.sellers.contains(user) or user in counter.barmen_list:
        return redirect(counter.get_absolute_url() + "?sellers")
    if len(counter.barmen_list) == 0:
        counter.gen_token()
    request.session["counter_token"] = counter.token
    counter.permanencies.create(user=user, start=timezone.now())
    return redirect(counter)


@require_POST
def counter_logout(request: HttpRequest, counter_id: int) -> HttpResponseRedirect:
    """End the permanency of a user in this counter."""
    Permanency.objects.filter(counter=counter_id, user=request.POST["user_id"]).update(
        end=F("activity")
    )
    return redirect("counter:details", counter_id=counter_id)
