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

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic.base import View

from core.views.mixins import TabedViewMixin
from counter.utils import is_logged_in_counter


class CounterAdminMixin(View):
    """Protect counter admin section."""

    edit_group = [settings.SITH_GROUP_COUNTER_ADMIN_ID]
    edit_club = []

    def _test_group(self, user):
        return any(user.is_in_group(pk=grp_id) for grp_id in self.edit_group)

    def _test_club(self, user):
        return any(c.can_be_edited_by(user) for c in self.edit_club)

    def dispatch(self, request, *args, **kwargs):
        if not (
            request.user.is_root
            or self._test_group(request.user)
            or self._test_club(request.user)
        ):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


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
    list_of_tabs = [
        {
            "url": reverse_lazy("counter:admin_list"),
            "slug": "counters",
            "name": _("Counters"),
        },
        {
            "url": reverse_lazy("counter:product_list"),
            "slug": "products",
            "name": _("Products"),
        },
        {
            "url": reverse_lazy("counter:product_type_list"),
            "slug": "product_types",
            "name": _("Product types"),
        },
        {
            "url": reverse_lazy("counter:returnable_list"),
            "slug": "returnable_products",
            "name": _("Returnable products"),
        },
        {
            "url": reverse_lazy("counter:cash_summary_list"),
            "slug": "cash_summary",
            "name": _("Cash register summaries"),
        },
        {
            "url": reverse_lazy("counter:invoices_call"),
            "slug": "invoices_call",
            "name": _("Invoices call"),
        },
        {
            "url": reverse_lazy("counter:eticket_list"),
            "slug": "etickets",
            "name": _("Etickets"),
        },
    ]
