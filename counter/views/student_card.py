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

from core.views import AllowFragment, CanEditMixin
from counter.forms import StudentCardForm
from counter.models import Counter, Customer, StudentCard


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


class StudentCardFormView(AllowFragment, FormView):
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


class StudentCardFormFragmentView(FormView):
    """
    Add a new student card from a counter
    This is a fragment only view which integrates with counter_click.jinja
    """

    form_class = StudentCardForm
    template_name = "counter/add_student_card_fragment.jinja"

    def dispatch(self, request, *args, **kwargs):
        self.counter = get_object_or_404(
            Counter.objects.annotate_is_open(), pk=kwargs["counter_id"]
        )
        self.customer = get_object_or_404(
            Customer.objects.prefetch_related("student_cards"), pk=kwargs["customer_id"]
        )
        if not (
            self.counter.type == "BAR"
            and "counter_token" in request.session
            and request.session["counter_token"] == self.counter.token
            and self.counter.is_open
        ):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        data = form.clean()
        res = super().form_valid(form)
        StudentCard(customer=self.customer, uid=data["uid"]).save()
        return res

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["counter"] = self.counter
        context["customer"] = self.customer
        context["action"] = self.request.path
        context["student_cards"] = self.customer.student_cards.all()
        return context

    def get_success_url(self, **kwargs):
        return reverse_lazy(
            "counter:add_student_card_fragment",
            kwargs={
                "customer_id": self.customer.pk,
                "counter_id": self.counter.id,
            },
        )
