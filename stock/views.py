# -*- coding:utf-8 -*-
#
# Copyright 2023 © AE UTBM
# ae@utbm.fr / ae.info@utbm.fr
# All contributors are listed in the CONTRIBUTORS file.
#
# This file is part of the website of the UTBM Student Association (AE UTBM),
# https://ae.utbm.fr.
#
# You can find the whole source code at https://github.com/ae-utbm/sith3
#
# LICENSED UNDER THE GNU GENERAL PUBLIC LICENSE VERSION 3 (GPLv3)
# SEE : https://raw.githubusercontent.com/ae-utbm/sith3/master/LICENSE
# OR WITHIN THE LOCAL FILE "LICENSE"
#
# PREVIOUSLY LICENSED UNDER THE MIT LICENSE,
# SEE : https://raw.githubusercontent.com/ae-utbm/sith3/master/LICENSE.old
# OR WITHIN THE LOCAL FILE "LICENSE.old"
#

from collections import OrderedDict

from django import forms
from django.db import transaction
from django.forms.models import modelform_factory
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, ListView
from django.views.generic.edit import BaseFormView, CreateView, DeleteView, UpdateView

from core.views import CanCreateMixin, CanEditMixin, CanEditPropMixin, CanViewMixin
from counter.models import ProductType
from counter.views import CounterAdminTabsMixin, CounterTabsMixin
from stock.models import ShoppingList, ShoppingListItem, Stock, StockItem


class StockItemList(CounterAdminTabsMixin, CanCreateMixin, ListView):
    """
    The stockitems list view for the counter owner
    """

    model = Stock
    template_name = "stock/stock_item_list.jinja"
    pk_url_kwarg = "stock_id"
    current_tab = "stocks"

    def get_context_data(self):
        ret = super(StockItemList, self).get_context_data()
        if "stock_id" in self.kwargs.keys():
            ret["stock"] = Stock.objects.filter(id=self.kwargs["stock_id"]).first()
        return ret


class StockListView(CounterAdminTabsMixin, CanViewMixin, ListView):
    """
    A list view for the admins
    """

    model = Stock
    template_name = "stock/stock_list.jinja"
    current_tab = "stocks"


class StockEditForm(forms.ModelForm):
    """
    A form to change stock's characteristics
    """

    class Meta:
        model = Stock
        fields = ["name", "counter"]

    def __init__(self, *args, **kwargs):
        super(StockEditForm, self).__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        return super(StockEditForm, self).save(*args, **kwargs)


class StockEditView(CounterAdminTabsMixin, CanEditPropMixin, UpdateView):
    """
    An edit view for the stock
    """

    model = Stock
    form_class = modelform_factory(Stock, fields=["name", "counter"])
    pk_url_kwarg = "stock_id"
    template_name = "core/edit.jinja"
    current_tab = "stocks"


class StockItemEditView(CounterAdminTabsMixin, CanEditPropMixin, UpdateView):
    """
    An edit view for a stock item
    """

    model = StockItem
    form_class = modelform_factory(
        StockItem,
        fields=[
            "name",
            "unit_quantity",
            "effective_quantity",
            "minimal_quantity",
            "type",
            "stock_owner",
        ],
    )
    pk_url_kwarg = "item_id"
    template_name = "core/edit.jinja"
    current_tab = "stocks"


class StockCreateView(CounterAdminTabsMixin, CanCreateMixin, CreateView):
    """
    A create view for a new Stock
    """

    model = Stock
    form_class = modelform_factory(Stock, fields=["name", "counter"])
    template_name = "core/create.jinja"
    pk_url_kwarg = "counter_id"
    current_tab = "stocks"
    success_url = reverse_lazy("stock:list")

    def get_initial(self):
        ret = super(StockCreateView, self).get_initial()
        if "counter_id" in self.kwargs.keys():
            ret["counter"] = self.kwargs["counter_id"]
        return ret


class StockItemCreateView(CounterAdminTabsMixin, CanCreateMixin, CreateView):
    """
    A create view for a new StockItem
    """

    model = StockItem
    form_class = modelform_factory(
        StockItem,
        fields=[
            "name",
            "unit_quantity",
            "effective_quantity",
            "minimal_quantity",
            "type",
            "stock_owner",
        ],
    )
    template_name = "core/create.jinja"
    pk_url_kwarg = "stock_id"
    current_tab = "stocks"

    def get_initial(self):
        ret = super(StockItemCreateView, self).get_initial()
        if "stock_id" in self.kwargs.keys():
            ret["stock_owner"] = self.kwargs["stock_id"]
        return ret

    def get_success_url(self):
        return reverse_lazy(
            "stock:items_list", kwargs={"stock_id": self.object.stock_owner.id}
        )


class StockShoppingListView(CounterAdminTabsMixin, CanViewMixin, ListView):
    """
    A list view for the people to know the item to buy
    """

    model = Stock
    template_name = "stock/stock_shopping_list.jinja"
    pk_url_kwarg = "stock_id"
    current_tab = "stocks"

    def get_context_data(self):
        ret = super(StockShoppingListView, self).get_context_data()
        if "stock_id" in self.kwargs.keys():
            ret["stock"] = Stock.objects.filter(id=self.kwargs["stock_id"]).first()
        return ret


class StockItemQuantityForm(forms.BaseForm):
    def clean(self):
        with transaction.atomic():
            self.stock = Stock.objects.filter(id=self.stock_id).first()
            shopping_list = ShoppingList(
                name="Courses " + self.stock.counter.name,
                date=timezone.now(),
                todo=True,
            )
            shopping_list.save()
            shopping_list.stock_owner = self.stock
            shopping_list.save()
            for k, t in self.cleaned_data.items():
                if k == "name":
                    shopping_list.name = t
                    shopping_list.save()
                elif k == "comment":
                    shopping_list.comment = t
                    shopping_list.save()
                else:
                    if t > 0:
                        item_id = int(k[5:])
                        item = StockItem.objects.filter(id=item_id).first()
                        shoppinglist_item = ShoppingListItem(
                            stockitem_owner=item,
                            name=item.name,
                            type=item.type,
                            tobuy_quantity=t,
                        )
                        shoppinglist_item.save()
                        shoppinglist_item.shopping_lists.add(shopping_list)
                        shoppinglist_item.save()

        return self.cleaned_data


class StockItemQuantityBaseFormView(
    CounterAdminTabsMixin, CanEditMixin, DetailView, BaseFormView
):
    """
    docstring for StockItemOutList
    """

    model = StockItem
    template_name = "stock/shopping_list_quantity.jinja"
    pk_url_kwarg = "stock_id"
    current_tab = "stocks"

    def get_form_class(self):
        fields = OrderedDict()
        kwargs = {}
        fields["name"] = forms.CharField(
            max_length=30, required=True, label=_("Shopping list name")
        )
        for t in ProductType.objects.order_by("name").all():
            for i in self.stock.items.filter(type=t).order_by("name").all():
                if i.effective_quantity <= i.minimal_quantity:
                    field_name = "item-%s" % (str(i.id))
                    fields[field_name] = forms.IntegerField(
                        required=True,
                        label=str(i),
                        initial=0,
                        help_text=_(str(i.effective_quantity) + " left"),
                    )
        fields["comment"] = forms.CharField(
            widget=forms.Textarea(
                attrs={
                    "placeholder": _(
                        "Add here, items to buy that are not reference as a stock item (example : sponge, knife, mugs ...)"
                    )
                }
            ),
            required=False,
            label=_("Comments"),
        )
        kwargs["stock_id"] = self.stock.id
        kwargs["base_fields"] = fields
        return type("StockItemQuantityForm", (StockItemQuantityForm,), kwargs)

    def get(self, request, *args, **kwargs):
        """
        Simple get view
        """
        self.stock = Stock.objects.filter(id=self.kwargs["stock_id"]).first()
        return super(StockItemQuantityBaseFormView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """
        Handle the many possibilities of the post request
        """
        self.object = self.get_object()
        self.stock = Stock.objects.filter(id=self.kwargs["stock_id"]).first()
        return super(StockItemQuantityBaseFormView, self).post(request, *args, **kwargs)

    def form_valid(self, form):
        return super(StockItemQuantityBaseFormView, self).form_valid(form)

    def get_context_data(self, **kwargs):
        kwargs = super(StockItemQuantityBaseFormView, self).get_context_data(**kwargs)
        if "form" not in kwargs.keys():
            kwargs["form"] = self.get_form()
        kwargs["stock"] = self.stock
        return kwargs

    def get_success_url(self):
        return reverse_lazy(
            "stock:shoppinglist_list", args=self.args, kwargs=self.kwargs
        )


class StockShoppingListItemListView(CounterAdminTabsMixin, CanViewMixin, ListView):
    """docstring for StockShoppingListItemListView"""

    model = ShoppingList
    template_name = "stock/shopping_list_items.jinja"
    pk_url_kwarg = "shoppinglist_id"
    current_tab = "stocks"

    def get_context_data(self):
        ret = super(StockShoppingListItemListView, self).get_context_data()
        if "shoppinglist_id" in self.kwargs.keys():
            ret["shoppinglist"] = ShoppingList.objects.filter(
                id=self.kwargs["shoppinglist_id"]
            ).first()
        return ret


class StockShoppingListDeleteView(CounterAdminTabsMixin, CanEditMixin, DeleteView):
    """
    Delete a ShoppingList (for the resonsible account)
    """

    model = ShoppingList
    pk_url_kwarg = "shoppinglist_id"
    template_name = "core/delete_confirm.jinja"
    current_tab = "stocks"

    def get_success_url(self):
        return reverse_lazy(
            "stock:shoppinglist_list", kwargs={"stock_id": self.object.stock_owner.id}
        )


class StockShopppingListSetDone(CanEditMixin, DetailView):
    """
    Set a ShoppingList as done
    """

    model = ShoppingList
    pk_url_kwarg = "shoppinglist_id"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.todo = False
        self.object.save()
        return HttpResponseRedirect(
            reverse(
                "stock:shoppinglist_list",
                args=self.args,
                kwargs={"stock_id": self.object.stock_owner.id},
            )
        )

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return HttpResponseRedirect(
            reverse(
                "stock:shoppinglist_list",
                args=self.args,
                kwargs={"stock_id": self.object.stock_owner.id},
            )
        )


class StockShopppingListSetTodo(CanEditMixin, DetailView):
    """
    Set a ShoppingList as done
    """

    model = ShoppingList
    pk_url_kwarg = "shoppinglist_id"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.todo = True
        self.object.save()
        return HttpResponseRedirect(
            reverse(
                "stock:shoppinglist_list",
                args=self.args,
                kwargs={"stock_id": self.object.stock_owner.id},
            )
        )

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return HttpResponseRedirect(
            reverse(
                "stock:shoppinglist_list",
                args=self.args,
                kwargs={"stock_id": self.object.stock_owner.id},
            )
        )


class StockUpdateAfterShopppingForm(forms.BaseForm):
    def clean(self):
        with transaction.atomic():
            self.shoppinglist = ShoppingList.objects.filter(
                id=self.shoppinglist_id
            ).first()
            for k, t in self.cleaned_data.items():
                shoppinglist_item_id = int(k[5:])
                if int(t) > 0:
                    shoppinglist_item = ShoppingListItem.objects.filter(
                        id=shoppinglist_item_id
                    ).first()
                    shoppinglist_item.bought_quantity = int(t)
                    shoppinglist_item.save()
                    shoppinglist_item.stockitem_owner.effective_quantity += int(t)
                    shoppinglist_item.stockitem_owner.save()
            self.shoppinglist.todo = False
            self.shoppinglist.save()
        return self.cleaned_data


class StockUpdateAfterShopppingBaseFormView(
    CounterAdminTabsMixin, CanEditMixin, DetailView, BaseFormView
):
    """
    docstring for StockUpdateAfterShopppingBaseFormView
    """

    model = ShoppingList
    template_name = "stock/update_after_shopping.jinja"
    pk_url_kwarg = "shoppinglist_id"
    current_tab = "stocks"

    def get_form_class(self):
        fields = OrderedDict()
        kwargs = {}
        for t in ProductType.objects.order_by("name").all():
            for i in (
                self.shoppinglist.shopping_items_to_buy.filter(type=t)
                .order_by("name")
                .all()
            ):
                field_name = "item-%s" % (str(i.id))
                fields[field_name] = forms.CharField(
                    max_length=30,
                    required=True,
                    label=str(i),
                    help_text=_(str(i.tobuy_quantity) + " asked"),
                )
        kwargs["shoppinglist_id"] = self.shoppinglist.id
        kwargs["base_fields"] = fields
        return type(
            "StockUpdateAfterShopppingForm", (StockUpdateAfterShopppingForm,), kwargs
        )

    def get(self, request, *args, **kwargs):
        self.shoppinglist = ShoppingList.objects.filter(
            id=self.kwargs["shoppinglist_id"]
        ).first()
        return super(StockUpdateAfterShopppingBaseFormView, self).get(
            request, *args, **kwargs
        )

    def post(self, request, *args, **kwargs):
        """
        Handle the many possibilities of the post request
        """
        self.object = self.get_object()
        self.shoppinglist = ShoppingList.objects.filter(
            id=self.kwargs["shoppinglist_id"]
        ).first()
        return super(StockUpdateAfterShopppingBaseFormView, self).post(
            request, *args, **kwargs
        )

    def form_valid(self, form):
        """
        We handle here the redirection
        """
        return super(StockUpdateAfterShopppingBaseFormView, self).form_valid(form)

    def get_context_data(self, **kwargs):
        kwargs = super(StockUpdateAfterShopppingBaseFormView, self).get_context_data(
            **kwargs
        )
        if "form" not in kwargs.keys():
            kwargs["form"] = self.get_form()
        kwargs["shoppinglist"] = self.shoppinglist
        kwargs["stock"] = self.shoppinglist.stock_owner
        return kwargs

    def get_success_url(self):
        self.kwargs.pop("shoppinglist_id", None)
        return reverse_lazy(
            "stock:shoppinglist_list", args=self.args, kwargs=self.kwargs
        )


class StockTakeItemsForm(forms.BaseForm):
    """
    docstring for StockTakeItemsFormView
    """

    def clean(self):
        with transaction.atomic():
            for k, t in self.cleaned_data.items():
                item_id = int(k[5:])
                if t > 0:
                    item = StockItem.objects.filter(id=item_id).first()
                    item.effective_quantity -= t
                    item.save()
        return self.cleaned_data


class StockTakeItemsBaseFormView(
    CounterTabsMixin, CanEditMixin, DetailView, BaseFormView
):
    """
    docstring for StockTakeItemsBaseFormView
    """

    model = StockItem
    template_name = "stock/stock_take_items.jinja"
    pk_url_kwarg = "stock_id"
    current_tab = "take_items_from_stock"

    def get_form_class(self):
        fields = OrderedDict()
        kwargs = {}
        for t in ProductType.objects.order_by("name").all():
            for i in self.stock.items.filter(type=t).order_by("name").all():
                field_name = "item-%s" % (str(i.id))
                fields[field_name] = forms.IntegerField(
                    required=False,
                    label=str(i),
                    initial=0,
                    min_value=0,
                    max_value=i.effective_quantity,
                    help_text=_(
                        "%(effective_quantity)s left"
                        % {"effective_quantity": str(i.effective_quantity)}
                    ),
                )
                kwargs[field_name] = i.effective_quantity
        kwargs["stock_id"] = self.stock.id
        kwargs["counter_id"] = self.stock.counter.id
        kwargs["base_fields"] = fields
        return type("StockTakeItemsForm", (StockTakeItemsForm,), kwargs)

    def get(self, request, *args, **kwargs):
        """
        Simple get view
        """
        self.stock = Stock.objects.filter(id=self.kwargs["stock_id"]).first()
        return super(StockTakeItemsBaseFormView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """
        Handle the many possibilities of the post request
        """
        self.object = self.get_object()
        self.stock = Stock.objects.filter(id=self.kwargs["stock_id"]).first()
        if self.stock.counter.type == "BAR" and not (
            "counter_token" in self.request.session.keys()
            and self.request.session["counter_token"] == self.stock.counter.token
        ):  # Also check the token to avoid the bar to be stolen
            return HttpResponseRedirect(
                reverse_lazy(
                    "counter:details",
                    args=self.args,
                    kwargs={"counter_id": self.stock.counter.id},
                )
                + "?bad_location"
            )
        return super(StockTakeItemsBaseFormView, self).post(request, *args, **kwargs)

    def form_valid(self, form):
        return super(StockTakeItemsBaseFormView, self).form_valid(form)

    def get_context_data(self, **kwargs):
        kwargs = super(StockTakeItemsBaseFormView, self).get_context_data(**kwargs)
        if "form" not in kwargs.keys():
            kwargs["form"] = self.get_form()
        kwargs["stock"] = self.stock
        kwargs["counter"] = self.stock.counter
        return kwargs

    def get_success_url(self):
        stock = Stock.objects.filter(id=self.kwargs["stock_id"]).first()
        self.kwargs["counter_id"] = stock.counter.id
        self.kwargs.pop("stock_id", None)
        return reverse_lazy("counter:details", args=self.args, kwargs=self.kwargs)
