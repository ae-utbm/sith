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

from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic.edit import DeleteView, FormView

from core.views import CanEditMixin
from counter.forms import StudentCardForm
from counter.models import Customer, StudentCard


class StudentCardDeleteView(DeleteView, CanEditMixin):
    """View used to delete a card from a user."""

    model = StudentCard
    template_name = "core/delete_confirm.jinja"
    pk_url_kwarg = "card_id"

    def dispatch(self, request, *args, **kwargs):
        self.customer = get_object_or_404(Customer, pk=kwargs["customer_id"])
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self, **kwargs):
        return reverse_lazy(
            "core:user_prefs", kwargs={"user_id": self.customer.user.pk}
        )


class StudentCardFormView(FormView):
    """Add a new student card."""

    form_class = StudentCardForm
    template_name = "core/create.jinja"

    def dispatch(self, request, *args, **kwargs):
        self.customer = get_object_or_404(Customer, pk=kwargs["customer_id"])
        if not StudentCard.can_create(self.customer, request.user):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        data = form.clean()
        res = super(FormView, self).form_valid(form)
        StudentCard(customer=self.customer, uid=data["uid"]).save()
        return res

    def get_success_url(self, **kwargs):
        return reverse_lazy(
            "core:user_prefs", kwargs={"user_id": self.customer.user.pk}
        )
