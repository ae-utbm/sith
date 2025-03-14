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
from datetime import datetime, timedelta
from datetime import timezone as tz

from django.db.models import F
from django.utils import timezone
from django.views.generic import TemplateView

from counter.fields import CurrencyField
from counter.models import Refilling, Selling
from counter.views.mixins import CounterAdminMixin, CounterAdminTabsMixin


class InvoiceCallView(CounterAdminTabsMixin, CounterAdminMixin, TemplateView):
    template_name = "counter/invoices_call.jinja"
    current_tab = "invoices_call"

    def get_context_data(self, **kwargs):
        """Add sums to the context."""
        kwargs = super().get_context_data(**kwargs)
        kwargs["months"] = Selling.objects.datetimes("date", "month", order="DESC")
        if "month" in self.request.GET:
            start_date = datetime.strptime(self.request.GET["month"], "%Y-%m")
        else:
            start_date = datetime(
                year=timezone.now().year,
                month=(timezone.now().month + 10) % 12 + 1,
                day=1,
            )
        start_date = start_date.replace(tzinfo=tz.utc)
        end_date = (start_date + timedelta(days=32)).replace(
            day=1, hour=0, minute=0, microsecond=0
        )
        from django.db.models import Case, Sum, When

        kwargs["sum_cb"] = sum(
            [
                r.amount
                for r in Refilling.objects.filter(
                    payment_method="CARD",
                    is_validated=True,
                    date__gte=start_date,
                    date__lte=end_date,
                )
            ]
        )
        kwargs["sum_cb"] += sum(
            [
                s.quantity * s.unit_price
                for s in Selling.objects.filter(
                    payment_method="CARD",
                    is_validated=True,
                    date__gte=start_date,
                    date__lte=end_date,
                )
            ]
        )
        kwargs["start_date"] = start_date
        kwargs["sums"] = (
            Selling.objects.values("club__name")
            .annotate(
                selling_sum=Sum(
                    Case(
                        When(
                            date__gte=start_date,
                            date__lt=end_date,
                            then=F("unit_price") * F("quantity"),
                        ),
                        output_field=CurrencyField(),
                    )
                )
            )
            .exclude(selling_sum=None)
            .order_by("-selling_sum")
        )
        return kwargs
