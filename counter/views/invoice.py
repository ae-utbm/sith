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
from counter.models import Club, InvoiceCall, Refilling, Selling
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

        # une query pour tous les clubs qu'on met dans un dico dont la clé est le nom du club
        club_names = [i["club__name"] for i in kwargs["sums"]]
        clubs = Club.objects.filter(name__in=club_names)

        # et une query pour les factures
        invoice_calls = InvoiceCall.objects.filter(
            month=start_date.month, year=start_date.year, club__in=clubs
        )

        invoice_statuses = {ic.club.name: ic.validated for ic in invoice_calls}

        kwargs["validated"] = invoice_statuses
        return kwargs

    def post(self, request, *args, **kwargs):
        if request.POST["month"]:
            start_date = datetime.strptime(request.POST["month"], "%Y-%m")

        year = start_date.year
        month = start_date.month

        club_names = list(
            Selling.objects.filter(date__year=year, date__month=month)
            .values_list("club__name", flat=True)
            .distinct()
        )

        clubs = Club.objects.filter(name__in=club_names)
        club_map = {club.name: club for club in clubs}

        invoice_calls = InvoiceCall.objects.filter(
            year=year, month=month, club__in=clubs
        )
        invoice_statuses = {ic.club.name: ic for ic in invoice_calls}

        for club_name in club_names:
            is_checked = f"validate_{club_name}" in request.POST
            invoice_call = invoice_statuses[club_name]

            if invoice_call:
                if invoice_call.validated != is_checked:
                    invoice_call.validated = is_checked
                    invoice_call.save()
            else:
                InvoiceCall.objects.create(
                    year=year,
                    month=month,
                    club=club_map[club_name],
                    validated=is_checked,
                )

        from django.shortcuts import redirect

        return redirect(f"{request.path}?month={request.POST.get('month', '')}")
