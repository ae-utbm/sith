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
from datetime import date, datetime, timedelta
from datetime import timezone as tz

from django.db.models import Exists, F, OuterRef
from django.shortcuts import redirect
from django.utils import timezone
from django.views.generic import TemplateView

from counter.fields import CurrencyField
from counter.forms import InvoiceCallForm
from counter.models import Club, InvoiceCall, Refilling, Selling
from counter.views.mixins import CounterAdminMixin, CounterAdminTabsMixin


class InvoiceCallView(CounterAdminTabsMixin, CounterAdminMixin, TemplateView):
    template_name = "counter/invoices_call.jinja"
    current_tab = "invoices_call"

    def dispatch(self, request, *args, **kwargs):
        previous_month = (date.today().replace(day=1) - timedelta(days=1)).strftime(
            "%Y-%m"
        )

        if request.method == "GET" and "month" not in request.GET:
            request.GET = request.GET.copy()
            request.GET["month"] = previous_month

        if request.method == "POST" and "month" not in request.POST:
            request.POST = request.POST.copy()
            request.POST["month"] = previous_month

        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        month_str = request.GET.get("month")

        try:
            start_date = datetime.strptime(month_str, "%Y-%m").date()
            today = timezone.now().date().replace(day=1)
            if start_date > today:
                return redirect("counter:invoices_call")
        except ValueError:
            return redirect("counter:invoices_call")
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """Add sums to the context."""
        kwargs = super().get_context_data(**kwargs)

        months_with_sellings = list(
            Selling.objects.datetimes("date", "month", order="DESC")
        )

        first_month = months_with_sellings[-1].replace(day=1).date()
        last_month = (date.today().replace(day=1) - timedelta(days=1)).replace(day=1)
        current = last_month
        months = []

        while current >= first_month:
            months.append(current)
            current = (current.replace(day=1) - timedelta(days=1)).replace(day=1)

        kwargs["months"] = months

        month_str = self.request.GET.get("month")

        try:
            start_date = datetime.strptime(self.request.GET["month"], "%Y-%m")
        except ValueError:
            return redirect("counter:invoices_call")

        start_date = start_date.replace(tzinfo=tz.utc)
        end_date = (start_date + timedelta(days=32)).replace(
            day=1, hour=0, minute=0, microsecond=0
        )
        from django.db.models import Case, Sum, When

        kwargs["sum_cb"] = Refilling.objects.filter(
            payment_method="CARD",
            is_validated=True,
            date__gte=start_date,
            date__lte=end_date,
        ).aggregate(amount=Sum(F("amount"), default=0))["amount"]

        kwargs["sum_cb"] += Selling.objects.filter(
            payment_method="CARD",
            is_validated=True,
            date__gte=start_date,
            date__lte=end_date,
        ).aggregate(amount=Sum(F("quantity") * F("unit_price"), default=0))["amount"]

        kwargs["start_date"] = start_date

        kwargs["sums"] = list(
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

        club_names = [i["club__name"] for i in kwargs["sums"]]
        clubs = Club.objects.filter(name__in=club_names)

        invoice_calls = InvoiceCall.objects.filter(month=month_str, club__in=clubs)
        invoice_statuses = {ic.club.name: ic.is_validated for ic in invoice_calls}

        kwargs["form"] = InvoiceCallForm(clubs=clubs, month=month_str)

        kwargs["club_data"] = []
        for club in clubs:
            selling_sum = next(
                (
                    item["selling_sum"]
                    for item in kwargs["sums"]
                    if item["club__name"] == club.name
                ),
                0,
            )
            kwargs["club_data"].append(
                {
                    "club": club,
                    "sum": selling_sum,
                    "validated": invoice_statuses.get(club.name, False),
                }
            )

        return kwargs

    def post(self, request, *args, **kwargs):
        month_str = request.POST.get("month")

        try:
            start_date = datetime.strptime(month_str, "%Y-%m")
            start_date = date(start_date.year, start_date.month, 1)
        except ValueError:
            return redirect(request.path)

        selling_subquery = Selling.objects.filter(
            club=OuterRef("pk"),
            date__year=start_date.year,
            date__month=start_date.month,
        )

        clubs = Club.objects.filter(Exists(selling_subquery))

        form = InvoiceCallForm(request.POST, clubs=clubs, month=month_str)

        if form.is_valid():
            form.save()

        return redirect(f"{request.path}?month={request.POST.get('month', '')}")
