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

from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _

from core.views.mixins import TabedViewMixin
from counter.utils import is_logged_in_counter


class CounterTabsMixin(TabedViewMixin):
    def get_tabs_title(self):
        return self.object

    def get_list_of_tabs(self):
        if self.object.type != "BAR":
            return []
        tab_list = [
            {
                "url": reverse(
                    "counter:details", kwargs={"counter_id": self.object.id}
                ),
                "slug": "counter",
                "name": _("Counter"),
            }
        ]
        if self.request.user.has_perm("counter.add_cashregistersummary"):
            tab_list.append(
                {
                    "url": reverse(
                        "counter:cash_summary", kwargs={"counter_id": self.object.id}
                    ),
                    "slug": "cash_summary",
                    "name": _("Cash summary"),
                }
            )
        if is_logged_in_counter(self.request):
            tab_list.append(
                {
                    "url": reverse(
                        "counter:last_ops", kwargs={"counter_id": self.object.id}
                    ),
                    "slug": "last_ops",
                    "name": _("Last operations"),
                }
            )
        if len(tab_list) <= 1:
            # It would be strange to show only one tab
            return []
        return tab_list


class CounterAdminTabsMixin(TabedViewMixin):
    tabs_title = _("Counter administration")

    def get_list_of_tabs(self):
        user = self.request.user
        res = [
            {
                "url": reverse_lazy("counter:admin_list"),
                "slug": "counters",
                "name": _("Counters"),
            }
        ]
        if user.has_perm("counter.view_product"):
            res.append(
                {
                    "url": reverse_lazy("counter:product_list"),
                    "slug": "products",
                    "name": _("Products"),
                }
            )
        if user.has_perm("counter.view_productformula"):
            res.append(
                {
                    "url": reverse_lazy("counter:product_formula_list"),
                    "slug": "formulas",
                    "name": _("Formulas"),
                }
            )
        if user.has_perm("counter.view_producttype"):
            res.append(
                {
                    "url": reverse_lazy("counter:product_type_list"),
                    "slug": "product_types",
                    "name": _("Product types"),
                }
            )
        if user.has_perm("counter.view_returnableproduct"):
            res.append(
                {
                    "url": reverse_lazy("counter:returnable_list"),
                    "slug": "returnable_products",
                    "name": _("Returnable products"),
                }
            )
        if user.has_perm("counter.view_cashregistersummary"):
            res.append(
                {
                    "url": reverse_lazy("counter:cash_summary_list"),
                    "slug": "cash_summary",
                    "name": _("Cash register summaries"),
                }
            )
        if user.has_perm("counter.view_invoicecall"):
            res.append(
                {
                    "url": reverse_lazy("counter:invoices_call"),
                    "slug": "invoices_call",
                    "name": _("Invoices call"),
                }
            )
        if user.has_perm("counter.view_eticket"):
            res.append(
                {
                    "url": reverse_lazy("counter:eticket_list"),
                    "slug": "etickets",
                    "name": _("Etickets"),
                }
            )
        return res
