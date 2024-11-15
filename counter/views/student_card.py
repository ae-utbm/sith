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
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic.edit import DeleteView, FormView

from core.utils import FormFragmentTemplateData
from core.views import CanEditMixin
from counter.forms import StudentCardForm
from counter.models import Customer, StudentCard
from counter.utils import is_logged_in_counter


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
    """Add a new student card. This is a fragment view !"""

    form_class = StudentCardForm
    template_name = "counter/fragments/create_student_card.jinja"

    @classmethod
    def get_template_data(
        cls, customer: Customer
    ) -> FormFragmentTemplateData[form_class]:
        """Get necessary data to pre-render the fragment"""
        return FormFragmentTemplateData[cls.form_class](
            form=cls.form_class(),
            template=cls.template_name,
            context={
                "action": reverse_lazy(
                    "counter:add_student_card", kwargs={"customer_id": customer.pk}
                ),
                "customer": customer,
                "student_cards": customer.student_cards.all(),
            },
        )

    def dispatch(self, request: HttpRequest, *args, **kwargs):
        self.customer = get_object_or_404(
            Customer.objects.prefetch_related("student_cards"), pk=kwargs["customer_id"]
        )

        if not is_logged_in_counter(request) and not StudentCard.can_create(
            self.customer, request.user
        ):
            raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        data = form.clean()
        res = super(FormView, self).form_valid(form)
        StudentCard(customer=self.customer, uid=data["uid"]).save()
        return res

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        data = self.get_template_data(self.customer)
        context.update(data.context)
        return context

    def get_success_url(self, **kwargs):
        return self.request.path