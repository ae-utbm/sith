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


from django import forms
from django.conf import settings
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db import transaction
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic.edit import FormView

from core.models import User
from core.views.widgets.ajax_select import AutoCompleteSelectUser
from counter.models import Counter, Product, Selling

# Main accounting view


class CloseCustomerAccountForm(forms.Form):
    user = forms.ModelChoiceField(
        label=_("Refound this account"),
        help_text=None,
        required=True,
        widget=AutoCompleteSelectUser,
        queryset=User.objects.all(),
    )


class RefoundAccountView(UserPassesTestMixin, FormView):
    """Create a selling with the same amount than the current user money."""

    template_name = "accounting/refound_account.jinja"
    form_class = CloseCustomerAccountForm

    def test_func(self):
        return self.request.user.is_root or self.request.user.is_in_group(
            pk=settings.SITH_GROUP_ACCOUNTING_ADMIN_ID
        )

    def form_valid(self, form):
        self.customer = form.cleaned_data["user"]
        self.create_selling()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("accounting:refound_account")

    def create_selling(self):
        with transaction.atomic():
            uprice = self.customer.customer.amount
            refound_club_counter = Counter.objects.get(
                id=settings.SITH_COUNTER_REFOUND_ID
            )
            refound_club = refound_club_counter.club
            s = Selling(
                label=_("Refound account"),
                unit_price=uprice,
                quantity=1,
                seller=self.request.user,
                customer=self.customer.customer,
                club=refound_club,
                counter=refound_club_counter,
                product=Product.objects.get(id=settings.SITH_PRODUCT_REFOUND_ID),
            )
            s.save()
