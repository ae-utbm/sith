from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView
from django.views.generic.edit import CreateView, UpdateView

from club.models import Club
from stock.forms import StockForm
from stock.heper import can_be_edited_by
from stock.models import Stock


class StockHomeView(UserPassesTestMixin, TemplateView):
    pk_url_kwarg = "club_id"
    template_name = "stock/home.jinja"

    def dispatch(self, request, *args, **kwargs):
        self.club = get_object_or_404(Club, pk=self.kwargs.get(self.pk_url_kwarg))
        self.is_editor = can_be_edited_by(self.request.user, self.club)
        return super().dispatch(request, *args, **kwargs)

    def test_func(self):
        return (
            self.club in self.request.user.clubs_with_rights
            or self.request.user.is_root
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["club"] = self.club
        context["stocks"] = Stock.objects.filter(club=self.club)
        context["is_editor"] = self.is_editor
        return context


class StockCreateView(UserPassesTestMixin, SuccessMessageMixin, CreateView):
    model = Stock
    form_class = StockForm
    template_name = "stock/create.jinja"

    def dispatch(self, request, *args, **kwargs):
        self.club = get_object_or_404(Club, pk=kwargs["club_id"])
        return super().dispatch(request, *args, **kwargs)

    def test_func(self):
        return can_be_edited_by(self.request.user, self.club)

    def get_form_kwargs(self):
        return super().get_form_kwargs() | {"club": self.club}

    def get_success_url(self):
        return reverse("stock:home", kwargs={"club_id": self.club.id})

    def get_success_message(self, cleaned_data):
        return cleaned_data["name"] + _(" created.")


class StockUpdateView(UserPassesTestMixin, SuccessMessageMixin, UpdateView):
    model = Stock
    form_class = StockForm
    pk_url_kwarg = "stock_id"
    template_name = "stock/edit.jinja"

    def dispatch(self, request, *args, **kwargs):
        self.club = get_object_or_404(Club, pk=kwargs["club_id"])
        return super().dispatch(request, *args, **kwargs)

    def test_func(self):
        return can_be_edited_by(self.request.user, self.club)

    def get_queryset(self):
        return Stock.objects.filter(club=self.club)

    def get_form_kwargs(self):
        return super().get_form_kwargs() | {"club": self.club}

    def get_success_url(self):
        return reverse("stock:home", kwargs={"club_id": self.club.id})

    def get_success_message(self, cleaned_data):
        return cleaned_data["name"] + _(" edited.")
