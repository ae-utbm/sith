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
from datetime import datetime
from datetime import timezone as tz

from django import forms
from django.conf import settings
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, ListView
from django.views.generic.edit import UpdateView

from core.auth.mixins import CanViewMixin
from counter.forms import CashSummaryFormBase
from counter.models import (
    CashRegisterSummary,
    CashRegisterSummaryItem,
    Counter,
    Refilling,
)
from counter.utils import is_logged_in_counter
from counter.views.mixins import (
    CounterAdminMixin,
    CounterAdminTabsMixin,
    CounterTabsMixin,
)


class CashRegisterSummaryForm(forms.Form):
    """Provide the cash summary form."""

    ten_cents = forms.IntegerField(label=_("10 cents"), required=False, min_value=0)
    twenty_cents = forms.IntegerField(label=_("20 cents"), required=False, min_value=0)
    fifty_cents = forms.IntegerField(label=_("50 cents"), required=False, min_value=0)
    one_euro = forms.IntegerField(label=_("1 euro"), required=False, min_value=0)
    two_euros = forms.IntegerField(label=_("2 euros"), required=False, min_value=0)
    five_euros = forms.IntegerField(label=_("5 euros"), required=False, min_value=0)
    ten_euros = forms.IntegerField(label=_("10 euros"), required=False, min_value=0)
    twenty_euros = forms.IntegerField(label=_("20 euros"), required=False, min_value=0)
    fifty_euros = forms.IntegerField(label=_("50 euros"), required=False, min_value=0)
    hundred_euros = forms.IntegerField(
        label=_("100 euros"), required=False, min_value=0
    )
    check_1_value = forms.DecimalField(
        label=_("Check amount"), required=False, min_value=0
    )
    check_1_quantity = forms.IntegerField(
        label=_("Check quantity"), required=False, min_value=0
    )
    check_2_value = forms.DecimalField(
        label=_("Check amount"), required=False, min_value=0
    )
    check_2_quantity = forms.IntegerField(
        label=_("Check quantity"), required=False, min_value=0
    )
    check_3_value = forms.DecimalField(
        label=_("Check amount"), required=False, min_value=0
    )
    check_3_quantity = forms.IntegerField(
        label=_("Check quantity"), required=False, min_value=0
    )
    check_4_value = forms.DecimalField(
        label=_("Check amount"), required=False, min_value=0
    )
    check_4_quantity = forms.IntegerField(
        label=_("Check quantity"), required=False, min_value=0
    )
    check_5_value = forms.DecimalField(
        label=_("Check amount"), required=False, min_value=0
    )
    check_5_quantity = forms.IntegerField(
        label=_("Check quantity"), required=False, min_value=0
    )
    comment = forms.CharField(label=_("Comment"), required=False)
    emptied = forms.BooleanField(label=_("Emptied"), required=False)

    def __init__(self, *args, **kwargs):
        instance = kwargs.pop("instance", None)
        super().__init__(*args, **kwargs)
        if instance:
            self.fields["ten_cents"].initial = (
                instance.ten_cents.quantity if instance.ten_cents else 0
            )
            self.fields["twenty_cents"].initial = (
                instance.twenty_cents.quantity if instance.twenty_cents else 0
            )
            self.fields["fifty_cents"].initial = (
                instance.fifty_cents.quantity if instance.fifty_cents else 0
            )
            self.fields["one_euro"].initial = (
                instance.one_euro.quantity if instance.one_euro else 0
            )
            self.fields["two_euros"].initial = (
                instance.two_euros.quantity if instance.two_euros else 0
            )
            self.fields["five_euros"].initial = (
                instance.five_euros.quantity if instance.five_euros else 0
            )
            self.fields["ten_euros"].initial = (
                instance.ten_euros.quantity if instance.ten_euros else 0
            )
            self.fields["twenty_euros"].initial = (
                instance.twenty_euros.quantity if instance.twenty_euros else 0
            )
            self.fields["fifty_euros"].initial = (
                instance.fifty_euros.quantity if instance.fifty_euros else 0
            )
            self.fields["hundred_euros"].initial = (
                instance.hundred_euros.quantity if instance.hundred_euros else 0
            )
            self.fields["check_1_quantity"].initial = (
                instance.check_1.quantity if instance.check_1 else 0
            )
            self.fields["check_2_quantity"].initial = (
                instance.check_2.quantity if instance.check_2 else 0
            )
            self.fields["check_3_quantity"].initial = (
                instance.check_3.quantity if instance.check_3 else 0
            )
            self.fields["check_4_quantity"].initial = (
                instance.check_4.quantity if instance.check_4 else 0
            )
            self.fields["check_5_quantity"].initial = (
                instance.check_5.quantity if instance.check_5 else 0
            )
            self.fields["check_1_value"].initial = (
                instance.check_1.value if instance.check_1 else 0
            )
            self.fields["check_2_value"].initial = (
                instance.check_2.value if instance.check_2 else 0
            )
            self.fields["check_3_value"].initial = (
                instance.check_3.value if instance.check_3 else 0
            )
            self.fields["check_4_value"].initial = (
                instance.check_4.value if instance.check_4 else 0
            )
            self.fields["check_5_value"].initial = (
                instance.check_5.value if instance.check_5 else 0
            )
            self.fields["comment"].initial = instance.comment
            self.fields["emptied"].initial = instance.emptied
            self.instance = instance
        else:
            self.instance = None

    def save(self, counter=None):
        cd = self.cleaned_data
        summary = self.instance or CashRegisterSummary(
            counter=counter, user=counter.get_random_barman()
        )
        summary.comment = cd["comment"]
        summary.emptied = cd["emptied"]
        summary.save()
        summary.items.all().delete()
        # Cash
        if cd["ten_cents"]:
            CashRegisterSummaryItem(
                cash_summary=summary, value=0.1, quantity=cd["ten_cents"]
            ).save()
        if cd["twenty_cents"]:
            CashRegisterSummaryItem(
                cash_summary=summary, value=0.2, quantity=cd["twenty_cents"]
            ).save()
        if cd["fifty_cents"]:
            CashRegisterSummaryItem(
                cash_summary=summary, value=0.5, quantity=cd["fifty_cents"]
            ).save()
        if cd["one_euro"]:
            CashRegisterSummaryItem(
                cash_summary=summary, value=1, quantity=cd["one_euro"]
            ).save()
        if cd["two_euros"]:
            CashRegisterSummaryItem(
                cash_summary=summary, value=2, quantity=cd["two_euros"]
            ).save()
        if cd["five_euros"]:
            CashRegisterSummaryItem(
                cash_summary=summary, value=5, quantity=cd["five_euros"]
            ).save()
        if cd["ten_euros"]:
            CashRegisterSummaryItem(
                cash_summary=summary, value=10, quantity=cd["ten_euros"]
            ).save()
        if cd["twenty_euros"]:
            CashRegisterSummaryItem(
                cash_summary=summary, value=20, quantity=cd["twenty_euros"]
            ).save()
        if cd["fifty_euros"]:
            CashRegisterSummaryItem(
                cash_summary=summary, value=50, quantity=cd["fifty_euros"]
            ).save()
        if cd["hundred_euros"]:
            CashRegisterSummaryItem(
                cash_summary=summary, value=100, quantity=cd["hundred_euros"]
            ).save()
        # Checks
        if cd["check_1_quantity"]:
            CashRegisterSummaryItem(
                cash_summary=summary,
                value=cd["check_1_value"],
                quantity=cd["check_1_quantity"],
                is_check=True,
            ).save()
        if cd["check_2_quantity"]:
            CashRegisterSummaryItem(
                cash_summary=summary,
                value=cd["check_2_value"],
                quantity=cd["check_2_quantity"],
                is_check=True,
            ).save()
        if cd["check_3_quantity"]:
            CashRegisterSummaryItem(
                cash_summary=summary,
                value=cd["check_3_value"],
                quantity=cd["check_3_quantity"],
                is_check=True,
            ).save()
        if cd["check_4_quantity"]:
            CashRegisterSummaryItem(
                cash_summary=summary,
                value=cd["check_4_value"],
                quantity=cd["check_4_quantity"],
                is_check=True,
            ).save()
        if cd["check_5_quantity"]:
            CashRegisterSummaryItem(
                cash_summary=summary,
                value=cd["check_5_value"],
                quantity=cd["check_5_quantity"],
                is_check=True,
            ).save()
        if summary.items.count() < 1:
            summary.delete()


class CounterCashSummaryView(CounterTabsMixin, CanViewMixin, DetailView):
    """Provide the cash summary form."""

    model = Counter
    pk_url_kwarg = "counter_id"
    template_name = "counter/cash_register_summary.jinja"
    current_tab = "cash_summary"

    def dispatch(self, request, *args, **kwargs):
        """We have here again a very particular right handling."""
        self.object = self.get_object()
        if is_logged_in_counter(request) and self.object.barmen_list:
            return super().dispatch(request, *args, **kwargs)
        return HttpResponseRedirect(
            reverse("counter:details", kwargs={"counter_id": self.object.id})
            + "?bad_location"
        )

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.form = CashRegisterSummaryForm()
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.form = CashRegisterSummaryForm(request.POST)
        if self.form.is_valid():
            self.form.save(self.object)
            return HttpResponseRedirect(self.get_success_url())
        return super().get(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy("counter:details", kwargs={"counter_id": self.object.id})

    def get_context_data(self, **kwargs):
        """Add form to the context."""
        kwargs = super().get_context_data(**kwargs)
        kwargs["form"] = self.form
        return kwargs


class CashSummaryEditView(CounterAdminTabsMixin, CounterAdminMixin, UpdateView):
    """Edit cash summaries."""

    model = CashRegisterSummary
    template_name = "counter/cash_register_summary.jinja"
    context_object_name = "cashsummary"
    pk_url_kwarg = "cashsummary_id"
    form_class = CashRegisterSummaryForm
    current_tab = "cash_summary"

    def get_success_url(self):
        return reverse("counter:cash_summary_list")


class CashSummaryListView(CounterAdminTabsMixin, CounterAdminMixin, ListView):
    """Display a list of cash summaries."""

    model = CashRegisterSummary
    template_name = "counter/cash_summary_list.jinja"
    context_object_name = "cashsummary_list"
    current_tab = "cash_summary"
    queryset = CashRegisterSummary.objects.all().order_by("-date")
    paginate_by = settings.SITH_COUNTER_CASH_SUMMARY_LENGTH

    def get_context_data(self, **kwargs):
        """Add sums to the context."""
        kwargs = super().get_context_data(**kwargs)
        form = CashSummaryFormBase(self.request.GET)
        kwargs["form"] = form
        kwargs["summaries_sums"] = {}
        kwargs["refilling_sums"] = {}
        for c in Counter.objects.filter(type="BAR").all():
            refillings = Refilling.objects.filter(counter=c)
            cashredistersummaries = CashRegisterSummary.objects.filter(counter=c)
            if form.is_valid() and form.cleaned_data["begin_date"]:
                refillings = refillings.filter(
                    date__gte=form.cleaned_data["begin_date"]
                )
                cashredistersummaries = cashredistersummaries.filter(
                    date__gte=form.cleaned_data["begin_date"]
                )
            else:
                last_summary = (
                    CashRegisterSummary.objects.filter(counter=c, emptied=True)
                    .order_by("-date")
                    .first()
                )
                if last_summary:
                    refillings = refillings.filter(date__gt=last_summary.date)
                    cashredistersummaries = cashredistersummaries.filter(
                        date__gt=last_summary.date
                    )
                else:
                    refillings = refillings.filter(
                        date__gte=datetime(year=1994, month=5, day=17, tzinfo=tz.utc)
                    )  # My birth date should be old enough
                    cashredistersummaries = cashredistersummaries.filter(
                        date__gte=datetime(year=1994, month=5, day=17, tzinfo=tz.utc)
                    )
            if form.is_valid() and form.cleaned_data["end_date"]:
                refillings = refillings.filter(date__lte=form.cleaned_data["end_date"])
                cashredistersummaries = cashredistersummaries.filter(
                    date__lte=form.cleaned_data["end_date"]
                )
            kwargs["summaries_sums"][c.name] = sum(
                [s.get_total() for s in cashredistersummaries.all()]
            )
            kwargs["refilling_sums"][c.name] = sum([s.amount for s in refillings.all()])
        return kwargs
