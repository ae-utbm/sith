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
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.safestring import SafeString
from django.utils.translation import gettext as _
from django.views.generic.edit import DeleteView, FormView

from core.auth.mixins import can_edit
from core.views.mixins import FragmentMixin
from counter.forms import StudentCardForm
from counter.models import Customer, StudentCard
from counter.utils import is_logged_in_counter


class StudentCardDeleteView(DeleteView):
    """View used to delete a card from a user. This is a fragment view !"""

    model = StudentCard
    template_name = "counter/fragments/delete_student_card.jinja"

    def dispatch(self, request: HttpRequest, *args, **kwargs):
        self.customer = get_object_or_404(Customer, pk=kwargs["customer_id"])
        if not is_logged_in_counter(request) and not can_edit(
            self.get_object(), request.user
        ):
            raise PermissionDenied()
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["action"] = self.request.path
        context["action_cancel"] = self.get_success_url()
        return context

    def get_object(self, queryset=None):
        if not hasattr(self.customer, "student_card"):
            raise Http404(
                _("%(name)s has no registered student card")
                % {"name": self.customer.user.get_full_name()}
            )
        return self.customer.student_card

    def get_success_url(self, **kwargs):
        return reverse(
            "counter:add_student_card", kwargs={"customer_id": self.customer.pk}
        )


class StudentCardFormFragment(FragmentMixin, FormView):
    """Add a new student card."""

    form_class = StudentCardForm
    template_name = "counter/fragments/create_student_card.jinja"

    def dispatch(self, request: HttpRequest, *args, **kwargs):
        self.customer = get_object_or_404(
            Customer.objects.select_related("student_card"), pk=kwargs["customer_id"]
        )

        if not is_logged_in_counter(request) and not StudentCard.can_create(
            self.customer, request.user
        ):
            raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)

    def render_fragment(self, request, **kwargs) -> SafeString:
        self.customer = kwargs.pop("customer")
        return super().render_fragment(request, **kwargs)

    def form_valid(self, form: StudentCardForm) -> HttpResponse:
        data = form.clean()
        StudentCard.objects.update_or_create(
            customer=self.customer, defaults={"uid": data["uid"]}
        )
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs) | {
            "action": reverse(
                "counter:add_student_card", kwargs={"customer_id": self.customer.pk}
            ),
            "customer": self.customer,
        }

    def get_success_url(self, **kwargs):
        return self.request.path
