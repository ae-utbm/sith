# -*- coding:utf-8 -*
#
# Copyright 2016,2017
# - Skia <skia@libskia.so>
#
# Ce fichier fait partie du site de l'Association des Étudiants de l'UTBM,
# http://ae.utbm.fr.
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License a published by the Free Software
# Foundation; either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Sofware Foundation, Inc., 59 Temple
# Place - Suite 330, Boston, MA 02111-1307, USA.
#
#

from django.conf.urls import url

from counter.views import *

urlpatterns = [
    url(r"^(?P<counter_id>[0-9]+)$", CounterMain.as_view(), name="details"),
    url(
        r"^(?P<counter_id>[0-9]+)/click/(?P<user_id>[0-9]+)$",
        CounterClick.as_view(),
        name="click",
    ),
    url(
        r"^(?P<counter_id>[0-9]+)/last_ops$",
        CounterLastOperationsView.as_view(),
        name="last_ops",
    ),
    url(
        r"^(?P<counter_id>[0-9]+)/cash_summary$",
        CounterCashSummaryView.as_view(),
        name="cash_summary",
    ),
    url(
        r"^(?P<counter_id>[0-9]+)/activity$",
        CounterActivityView.as_view(),
        name="activity",
    ),
    url(r"^(?P<counter_id>[0-9]+)/stats$", CounterStatView.as_view(), name="stats"),
    url(r"^(?P<counter_id>[0-9]+)/login$", CounterLogin.as_view(), name="login"),
    url(r"^(?P<counter_id>[0-9]+)/logout$", CounterLogout.as_view(), name="logout"),
    url(
        r"^eticket/(?P<selling_id>[0-9]+)/pdf$",
        EticketPDFView.as_view(),
        name="eticket_pdf",
    ),
    url(r"^admin/(?P<counter_id>[0-9]+)$", CounterEditView.as_view(), name="admin"),
    url(
        r"^admin/(?P<counter_id>[0-9]+)/prop$",
        CounterEditPropView.as_view(),
        name="prop_admin",
    ),
    url(r"^admin$", CounterListView.as_view(), name="admin_list"),
    url(r"^admin/new$", CounterCreateView.as_view(), name="new"),
    url(
        r"^admin/delete/(?P<counter_id>[0-9]+)$",
        CounterDeleteView.as_view(),
        name="delete",
    ),
    url(r"^admin/invoices_call$", InvoiceCallView.as_view(), name="invoices_call"),
    url(
        r"^admin/cash_summary/list$",
        CashSummaryListView.as_view(),
        name="cash_summary_list",
    ),
    url(
        r"^admin/cash_summary/(?P<cashsummary_id>[0-9]+)$",
        CashSummaryEditView.as_view(),
        name="cash_summary_edit",
    ),
    url(r"^admin/product/list$", ProductListView.as_view(), name="product_list"),
    url(
        r"^admin/product/list_archived$",
        ProductArchivedListView.as_view(),
        name="product_list_archived",
    ),
    url(r"^admin/product/create$", ProductCreateView.as_view(), name="new_product"),
    url(
        r"^admin/product/(?P<product_id>[0-9]+)$",
        ProductEditView.as_view(),
        name="product_edit",
    ),
    url(
        r"^admin/producttype/list$",
        ProductTypeListView.as_view(),
        name="producttype_list",
    ),
    url(
        r"^admin/producttype/create$",
        ProductTypeCreateView.as_view(),
        name="new_producttype",
    ),
    url(
        r"^admin/producttype/(?P<type_id>[0-9]+)$",
        ProductTypeEditView.as_view(),
        name="producttype_edit",
    ),
    url(r"^admin/eticket/list$", EticketListView.as_view(), name="eticket_list"),
    url(r"^admin/eticket/new$", EticketCreateView.as_view(), name="new_eticket"),
    url(
        r"^admin/eticket/(?P<eticket_id>[0-9]+)$",
        EticketEditView.as_view(),
        name="edit_eticket",
    ),
    url(
        r"^admin/selling/(?P<selling_id>[0-9]+)/delete$",
        SellingDeleteView.as_view(),
        name="selling_delete",
    ),
    url(
        r"^admin/refilling/(?P<refilling_id>[0-9]+)/delete$",
        RefillingDeleteView.as_view(),
        name="refilling_delete",
    ),
    url(
        r"^admin/(?P<counter_id>[0-9]+)/refillings$",
        CounterRefillingListView.as_view(),
        name="refilling_list",
    ),
]
