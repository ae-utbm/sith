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
from datetime import datetime, timezone
from urllib.parse import urlencode

from dateutil.relativedelta import relativedelta
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import F, Sum
from django.utils.timezone import localdate, make_aware
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView

from counter.forms import InvoiceCallForm
from counter.models import Refilling, Selling
from counter.views.mixins import CounterAdminTabsMixin


class InvoiceCallView(
    CounterAdminTabsMixin, PermissionRequiredMixin, SuccessMessageMixin, FormView
):
    template_name = "counter/invoices_call.jinja"
    current_tab = "invoices_call"
    permission_required = ["counter.view_invoicecall", "counter.change_invoicecall"]
    form_class = InvoiceCallForm
    success_message = _("Invoice calls status has been updated.")

    def get_month(self):
        kwargs = self.request.GET or self.request.POST
        if "month" in kwargs:
            return make_aware(datetime.strptime(kwargs["month"], "%Y-%m"))
        return localdate().replace(day=1) - relativedelta(months=1)

    def get_form_kwargs(self):
        return super().get_form_kwargs() | {"month": self.get_month()}

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

    def get_success_url(self):
        # redirect to the month from which the request is originated
        url = self.request.path
        kwargs = self.request.GET or self.request.POST
        if "month" in kwargs:
            query = urlencode({"month": kwargs["month"]})
            url += f"?{query}"
        return url

    def get_context_data(self, **kwargs):
        """Add sums to the context."""
        kwargs = super().get_context_data(**kwargs)
        kwargs["months"] = Selling.objects.datetimes("date", "month", order="DESC")
        month = self.get_month()
        start_date = datetime(month.year, month.month, month.day, tzinfo=timezone.utc)
        end_date = start_date + relativedelta(months=1)

        kwargs["sum_cb"] = Refilling.objects.filter(
            payment_method="CARD",
            is_validated=True,
            date__gte=start_date,
            date__lte=end_date,
        ).aggregate(res=Sum("amount", default=0))["res"]
        kwargs["sum_cb"] += (
            Selling.objects.filter(
                payment_method="CARD",
                is_validated=True,
                date__gte=start_date,
                date__lte=end_date,
            )
            .annotate(amount=F("unit_price") * F("quantity"))
            .aggregate(res=Sum("amount", default=0))["res"]
        )
        kwargs["start_date"] = start_date
        kwargs["invoices"] = (
            Selling.objects.filter(date__gte=start_date, date__lt=end_date)
            .values("club_id", "club__name")
            .annotate(selling_sum=Sum(F("unit_price") * F("quantity")))
            .exclude(selling_sum=None)
            .order_by("-selling_sum")
        )
        return kwargs
