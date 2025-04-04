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

from collections import OrderedDict
from datetime import datetime, timedelta
from datetime import timezone as tz

from django import forms
from django.conf import settings
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db import transaction
from django.template import defaultfilters
from django.urls import reverse_lazy
from django.utils import dateparse, timezone
from django.utils.translation import gettext as _
from django.views.generic import DetailView, ListView, TemplateView
from django.views.generic.edit import BaseFormView, CreateView, DeleteView, UpdateView

from club.models import Club
from core.auth.mixins import CanEditMixin, CanEditPropMixin, CanViewMixin
from core.models import Page, User
from counter.forms import GetUserForm
from counter.models import Counter, Customer, Selling
from launderette.models import Launderette, Machine, Slot, Token

# For users


class LaunderetteMainView(TemplateView):
    """Main presentation view."""

    template_name = "launderette/launderette_main.jinja"

    def get_context_data(self, **kwargs):
        """Add page to the context."""
        kwargs = super().get_context_data(**kwargs)
        kwargs["page"] = Page.objects.filter(name="launderette").first()
        return kwargs


class LaunderetteBookMainView(CanViewMixin, ListView):
    """Choose which launderette to book."""

    model = Launderette
    template_name = "launderette/launderette_book_choose.jinja"


class LaunderetteBookView(CanViewMixin, DetailView):
    """Display the launderette schedule."""

    model = Launderette
    pk_url_kwarg = "launderette_id"
    template_name = "launderette/launderette_book.jinja"

    def get(self, request, *args, **kwargs):
        self.slot_type = "BOTH"
        self.machines = {}
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.slot_type = "BOTH"
        self.machines = {}
        with transaction.atomic():
            self.object = self.get_object()
            if "slot_type" in request.POST:
                self.slot_type = request.POST["slot_type"]
            if "slot" in request.POST and request.user.is_authenticated:
                self.subscriber = request.user
                if self.subscriber.is_subscribed:
                    self.date = dateparse.parse_datetime(request.POST["slot"]).replace(
                        tzinfo=tz.utc
                    )
                    if self.slot_type in ["WASHING", "DRYING"]:
                        if self.check_slot(self.slot_type):
                            Slot(
                                user=self.subscriber,
                                start_date=self.date,
                                machine=self.machines[self.slot_type],
                                type=self.slot_type,
                            ).save()
                    elif self.check_slot("WASHING") and self.check_slot(
                        "DRYING", self.date + timedelta(hours=1)
                    ):
                        Slot(
                            user=self.subscriber,
                            start_date=self.date,
                            machine=self.machines["WASHING"],
                            type="WASHING",
                        ).save()
                        Slot(
                            user=self.subscriber,
                            start_date=self.date + timedelta(hours=1),
                            machine=self.machines["DRYING"],
                            type="DRYING",
                        ).save()
        return super().get(request, *args, **kwargs)

    def check_slot(self, machine_type, date=None):
        if date is None:
            date = self.date
        for m in self.object.machines.filter(is_working=True, type=machine_type):
            slot = Slot.objects.filter(start_date=date, machine=m).first()
            if slot is None:
                self.machines[machine_type] = m
                return True
        return False

    @staticmethod
    def date_iterator(startDate, endDate, delta=timedelta(days=1)):
        currentDate = startDate
        while currentDate < endDate:
            yield currentDate
            currentDate += delta

    def get_context_data(self, **kwargs):
        """Add page to the context."""
        kwargs = super().get_context_data(**kwargs)
        kwargs["planning"] = OrderedDict()
        kwargs["slot_type"] = self.slot_type
        start_date = datetime.now().replace(
            hour=0, minute=0, second=0, microsecond=0, tzinfo=tz.utc
        )
        for date in LaunderetteBookView.date_iterator(
            start_date, start_date + timedelta(days=6), timedelta(days=1)
        ):
            kwargs["planning"][date] = []
            for h in LaunderetteBookView.date_iterator(
                date, date + timedelta(days=1), timedelta(hours=1)
            ):
                free = False
                if (
                    (
                        self.slot_type == "BOTH"
                        and self.check_slot("WASHING", h)
                        and self.check_slot("DRYING", h + timedelta(hours=1))
                    )
                    or (self.slot_type == "WASHING" and self.check_slot("WASHING", h))
                    or (self.slot_type == "DRYING" and self.check_slot("DRYING", h))
                ):
                    free = True
                if free and datetime.now().replace(tzinfo=tz.utc) < h:
                    kwargs["planning"][date].append(h)
                else:
                    kwargs["planning"][date].append(None)
        return kwargs


class SlotDeleteView(CanEditPropMixin, DeleteView):
    """Delete a slot."""

    model = Slot
    pk_url_kwarg = "slot_id"
    template_name = "core/delete_confirm.jinja"

    def get_success_url(self):
        return self.request.user.get_absolute_url()


# For admins


class LaunderetteListView(CanEditPropMixin, ListView):
    """Choose which launderette to administer."""

    model = Launderette
    template_name = "launderette/launderette_list.jinja"


class LaunderetteEditView(CanEditPropMixin, UpdateView):
    """Edit a launderette."""

    model = Launderette
    pk_url_kwarg = "launderette_id"
    fields = ["name"]
    template_name = "core/edit.jinja"


class LaunderetteCreateView(PermissionRequiredMixin, CreateView):
    """Create a new launderette."""

    model = Launderette
    fields = ["name"]
    template_name = "core/create.jinja"
    permission_required = "launderette.add_launderette"

    def form_valid(self, form):
        club = Club.objects.get(id=settings.SITH_LAUNDERETTE_CLUB_ID)
        c = Counter(name=form.instance.name, club=club, type="OFFICE")
        c.save()
        form.instance.counter = c
        return super().form_valid(form)


class ManageTokenForm(forms.Form):
    action = forms.ChoiceField(
        choices=[("BACK", _("Back")), ("ADD", _("Add")), ("DEL", _("Delete"))],
        initial="BACK",
        label=_("Action"),
        widget=forms.RadioSelect,
    )
    token_type = forms.ChoiceField(
        choices=settings.SITH_LAUNDERETTE_MACHINE_TYPES,
        label=_("Type"),
        initial="WASHING",
        widget=forms.RadioSelect,
    )
    tokens = forms.CharField(
        max_length=512,
        widget=forms.widgets.Textarea,
        label=_("Tokens, separated by spaces"),
    )

    def process(self, launderette):
        cleaned_data = self.cleaned_data
        token_list = cleaned_data["tokens"].strip(" \n\r").split(" ")
        token_type = cleaned_data["token_type"]
        self.data = {}

        if cleaned_data["action"] not in ["BACK", "ADD", "DEL"]:
            return

        tokens = list(
            Token.objects.filter(
                launderette=launderette, type=token_type, name__in=token_list
            )
        )
        existing_names = {t.name for t in tokens}
        if cleaned_data["action"] in ["BACK", "DEL"]:
            for t in set(token_list) - existing_names:
                self.add_error(
                    None,
                    _("Token %(token_name)s does not exists") % {"token_name": t},
                )
        if cleaned_data["action"] == "BACK":
            Token.objects.filter(id__in=[t.id for t in tokens]).update(
                borrow_date=None, user=None
            )
        elif cleaned_data["action"] == "DEL":
            Token.objects.filter(id__in=[t.id for t in tokens]).delete()
        elif cleaned_data["action"] == "ADD":
            for name in existing_names:
                self.add_error(
                    None,
                    _("Token %(token_name)s already exists") % {"token_name": name},
                )
            for t in token_list:
                if t == "":
                    self.add_error(None, _("Token name can not be blank"))
                else:
                    Token(launderette=launderette, type=token_type, name=t).save()


class LaunderetteAdminView(CanEditPropMixin, BaseFormView, DetailView):
    """The admin page of the launderette."""

    model = Launderette
    pk_url_kwarg = "launderette_id"
    template_name = "launderette/launderette_admin.jinja"
    form_class = ManageTokenForm

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        """We handle here the redirection, passing the user id of the asked customer."""
        form.process(self.object)
        if form.is_valid():
            return super().form_valid(form)
        else:
            return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        """We handle here the login form for the barman."""
        kwargs = super().get_context_data(**kwargs)
        if self.request.method == "GET":
            kwargs["form"] = self.get_form()
        return kwargs

    def get_success_url(self):
        return reverse_lazy(
            "launderette:launderette_admin", args=self.args, kwargs=self.kwargs
        )


class GetLaunderetteUserForm(GetUserForm):
    def clean(self):
        cleaned_data = super().clean()
        sub = cleaned_data["user"]
        if sub.slots.all().count() <= 0:
            raise forms.ValidationError(_("User has booked no slot"))
        return cleaned_data


class LaunderetteMainClickView(CanEditMixin, BaseFormView, DetailView):
    """The click page of the launderette."""

    model = Launderette
    pk_url_kwarg = "launderette_id"
    template_name = "counter/counter_main.jinja"
    form_class = GetLaunderetteUserForm  # Form to enter a client code and get the corresponding user id

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        """We handle here the redirection, passing the user id of the asked customer."""
        self.kwargs["user_id"] = form.cleaned_data["user_id"]
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        """We handle here the login form for the barman."""
        kwargs = super().get_context_data(**kwargs)
        kwargs["counter"] = self.object.counter
        kwargs["form"] = self.get_form()
        kwargs["barmen"] = [self.request.user]
        if "last_basket" in self.request.session:
            kwargs["last_basket"] = self.request.session.pop("last_basket", None)
            kwargs["last_customer"] = self.request.session.pop("last_customer", None)
            kwargs["last_total"] = self.request.session.pop("last_total", None)
            kwargs["new_customer_amount"] = self.request.session.pop(
                "new_customer_amount", None
            )
        return kwargs

    def get_success_url(self):
        return reverse_lazy("launderette:click", args=self.args, kwargs=self.kwargs)


class ClickTokenForm(forms.BaseForm):
    def clean(self):
        with transaction.atomic():
            operator = User.objects.filter(id=self.operator_id).first()
            customer = Customer.objects.filter(user__id=self.subscriber_id).first()
            counter = Counter.objects.filter(id=self.counter_id).first()
            subscriber = customer.user
            self.last_basket = {
                "last_basket": [],
                "last_customer": customer.user.get_display_name(),
            }
            total = 0
            for k, t in self.cleaned_data.items():
                if t is not None:
                    slot_id = int(k[5:])
                    slot = Slot.objects.filter(id=slot_id).first()
                    slot.token = t
                    slot.save()
                    t.user = subscriber
                    t.borrow_date = datetime.now().replace(tzinfo=tz.utc)
                    t.save()
                    price = settings.SITH_LAUNDERETTE_PRICES[t.type]
                    s = Selling(
                        label="Jeton " + t.get_type_display() + " N°" + t.name,
                        club=counter.club,
                        product=None,
                        counter=counter,
                        unit_price=price,
                        quantity=1,
                        seller=operator,
                        customer=customer,
                    )
                    s.save()
                    total += price
                    self.last_basket["last_basket"].append(
                        "Jeton " + t.get_type_display() + " N°" + t.name
                    )
            self.last_basket["new_customer_amount"] = str(customer.amount)
            self.last_basket["last_total"] = str(total)
        return self.cleaned_data


class LaunderetteClickView(CanEditMixin, DetailView, BaseFormView):
    """The click page of the launderette."""

    model = Launderette
    pk_url_kwarg = "launderette_id"
    template_name = "launderette/launderette_click.jinja"

    def get_form_class(self):
        fields = OrderedDict()
        kwargs = {}

        def clean_field_factory(field_name, slot):
            def clean_field(self2):
                t_name = str(self2.data[field_name])
                if t_name != "":
                    t = Token.objects.filter(
                        name=str(self2.data[field_name]),
                        type=slot.type,
                        launderette=self.object,
                        user=None,
                    ).first()
                    if t is None:
                        raise forms.ValidationError(_("Token not found"))
                    return t

            return clean_field

        for s in self.subscriber.slots.filter(
            token=None, start_date__gte=timezone.now().replace(tzinfo=None)
        ).all():
            field_name = "slot-%s" % (str(s.id))
            fields[field_name] = forms.CharField(
                max_length=5,
                required=False,
                label="%s - %s"
                % (
                    s.get_type_display(),
                    defaultfilters.date(s.start_date, "j N Y H:i"),
                ),
            )
            # XXX l10n settings.DATETIME_FORMAT didn't work here :/
            kwargs["clean_" + field_name] = clean_field_factory(field_name, s)
        kwargs["subscriber_id"] = self.subscriber.id
        kwargs["counter_id"] = self.object.counter.id
        kwargs["operator_id"] = self.operator.id
        kwargs["base_fields"] = fields
        return type("ClickForm", (ClickTokenForm,), kwargs)

    def get(self, request, *args, **kwargs):
        """Simple get view."""
        self.customer = Customer.objects.filter(user__id=self.kwargs["user_id"]).first()
        self.subscriber = self.customer.user
        self.operator = request.user
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """Handle the many possibilities of the post request."""
        self.object = self.get_object()
        self.customer = Customer.objects.filter(user__id=self.kwargs["user_id"]).first()
        self.subscriber = self.customer.user
        self.operator = request.user
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        """We handle here the redirection, passing the user id of the asked customer."""
        self.request.session.update(form.last_basket)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        """We handle here the login form for the barman."""
        kwargs = super().get_context_data(**kwargs)
        if "form" not in kwargs:
            kwargs["form"] = self.get_form()
        kwargs["counter"] = self.object.counter
        kwargs["customer"] = self.customer
        return kwargs

    def get_success_url(self):
        self.kwargs.pop("user_id", None)
        return reverse_lazy(
            "launderette:main_click", args=self.args, kwargs=self.kwargs
        )


class MachineEditView(CanEditPropMixin, UpdateView):
    """Edit a machine."""

    model = Machine
    pk_url_kwarg = "machine_id"
    fields = ["name", "launderette", "type", "is_working"]
    template_name = "core/edit.jinja"


class MachineDeleteView(CanEditPropMixin, DeleteView):
    """Edit a machine."""

    model = Machine
    pk_url_kwarg = "machine_id"
    template_name = "core/delete_confirm.jinja"
    success_url = reverse_lazy("launderette:launderette_list")


class MachineCreateView(PermissionRequiredMixin, CreateView):
    """Create a new machine."""

    model = Machine
    fields = ["name", "launderette", "type"]
    template_name = "core/create.jinja"
    permission_required = "launderette.add_machine"

    def get_initial(self):
        ret = super().get_initial()
        if "launderette" in self.request.GET:
            obj = Launderette.objects.filter(
                id=int(self.request.GET["launderette"])
            ).first()
            if obj is not None:
                ret["launderette"] = obj.id
        return ret
