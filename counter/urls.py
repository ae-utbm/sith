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

from django.urls import re_path, path

from counter.views import *

urlpatterns = [
    re_path(r"^(?P<counter_id>[0-9]+)$", CounterMain.as_view(), name="details"),
    re_path(
        r"^(?P<counter_id>[0-9]+)/click/(?P<user_id>[0-9]+)$",
        CounterClick.as_view(),
        name="click",
    ),
    re_path(
        r"^(?P<counter_id>[0-9]+)/last_ops$",
        CounterLastOperationsView.as_view(),
        name="last_ops",
    ),
    re_path(
        r"^(?P<counter_id>[0-9]+)/cash_summary$",
        CounterCashSummaryView.as_view(),
        name="cash_summary",
    ),
    re_path(
        r"^(?P<counter_id>[0-9]+)/activity$",
        CounterActivityView.as_view(),
        name="activity",
    ),
    re_path(r"^(?P<counter_id>[0-9]+)/stats$", CounterStatView.as_view(), name="stats"),
    re_path(r"^(?P<counter_id>[0-9]+)/login$", CounterLogin.as_view(), name="login"),
    re_path(r"^(?P<counter_id>[0-9]+)/logout$", CounterLogout.as_view(), name="logout"),
    re_path(
        r"^eticket/(?P<selling_id>[0-9]+)/pdf$",
        EticketPDFView.as_view(),
        name="eticket_pdf",
    ),
    re_path(
        r"^customer/(?P<customer_id>[0-9]+)/card/add$",
        StudentCardFormView.as_view(),
        name="add_student_card",
    ),
    re_path(
        r"^customer/(?P<customer_id>[0-9]+)/card/delete/(?P<card_id>[0-9]+)/$",
        StudentCardDeleteView.as_view(),
        name="delete_student_card",
    ),
    path(
        "customer/<int:user_id>/billing_info/create",
        create_billing_info,
        name="create_billing_info",
    ),
    path(
        "customer/<int:user_id>/billing_info/edit",
        edit_billing_info,
        name="edit_billing_info",
    ),
    re_path(r"^admin/(?P<counter_id>[0-9]+)$", CounterEditView.as_view(), name="admin"),
    re_path(
        r"^admin/(?P<counter_id>[0-9]+)/prop$",
        CounterEditPropView.as_view(),
        name="prop_admin",
    ),
    re_path(r"^admin$", CounterListView.as_view(), name="admin_list"),
    re_path(r"^admin/new$", CounterCreateView.as_view(), name="new"),
    re_path(
        r"^admin/delete/(?P<counter_id>[0-9]+)$",
        CounterDeleteView.as_view(),
        name="delete",
    ),
    re_path(r"^admin/invoices_call$", InvoiceCallView.as_view(), name="invoices_call"),
    re_path(
        r"^admin/cash_summary/list$",
        CashSummaryListView.as_view(),
        name="cash_summary_list",
    ),
    re_path(
        r"^admin/cash_summary/(?P<cashsummary_id>[0-9]+)$",
        CashSummaryEditView.as_view(),
        name="cash_summary_edit",
    ),
    re_path(r"^admin/product/list$", ProductListView.as_view(), name="product_list"),
    re_path(
        r"^admin/product/list_archived$",
        ProductArchivedListView.as_view(),
        name="product_list_archived",
    ),
    re_path(r"^admin/product/create$", ProductCreateView.as_view(), name="new_product"),
    re_path(
        r"^admin/product/(?P<product_id>[0-9]+)$",
        ProductEditView.as_view(),
        name="product_edit",
    ),
    re_path(
        r"^admin/producttype/list$",
        ProductTypeListView.as_view(),
        name="producttype_list",
    ),
    re_path(
        r"^admin/producttype/create$",
        ProductTypeCreateView.as_view(),
        name="new_producttype",
    ),
    re_path(
        r"^admin/producttype/(?P<type_id>[0-9]+)$",
        ProductTypeEditView.as_view(),
        name="producttype_edit",
    ),
    re_path(r"^admin/eticket/list$", EticketListView.as_view(), name="eticket_list"),
    re_path(r"^admin/eticket/new$", EticketCreateView.as_view(), name="new_eticket"),
    re_path(
        r"^admin/eticket/(?P<eticket_id>[0-9]+)$",
        EticketEditView.as_view(),
        name="edit_eticket",
    ),
    re_path(
        r"^admin/selling/(?P<selling_id>[0-9]+)/delete$",
        SellingDeleteView.as_view(),
        name="selling_delete",
    ),
    re_path(
        r"^admin/refilling/(?P<refilling_id>[0-9]+)/delete$",
        RefillingDeleteView.as_view(),
        name="refilling_delete",
    ),
    re_path(
        r"^admin/(?P<counter_id>[0-9]+)/refillings$",
        CounterRefillingListView.as_view(),
        name="refilling_list",
    ),
]
