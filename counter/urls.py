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

from django.urls import path

from counter.views import *

urlpatterns = [
    path("<int:counter_id>/", CounterMain.as_view(), name="details"),
    path(
        "<int:counter_id>/click/<int:user_id>/",
        CounterClick.as_view(),
        name="click",
    ),
    path(
        "<int:counter_id>/last_ops/",
        CounterLastOperationsView.as_view(),
        name="last_ops",
    ),
    path(
        "<int:counter_id>/cash_summary/",
        CounterCashSummaryView.as_view(),
        name="cash_summary",
    ),
    path(
        "<int:counter_id>/activity/",
        CounterActivityView.as_view(),
        name="activity",
    ),
    path("<int:counter_id>/stats/", CounterStatView.as_view(), name="stats"),
    path("<int:counter_id>/login/", CounterLogin.as_view(), name="login"),
    path("<int:counter_id>/logout/", CounterLogout.as_view(), name="logout"),
    path(
        "eticket/<int:selling_id>/pdf/",
        EticketPDFView.as_view(),
        name="eticket_pdf",
    ),
    path(
        "customer/<int:customer_id>/card/add/",
        StudentCardFormView.as_view(),
        name="add_student_card",
    ),
    path(
        "customer/<int:customer_id>/card/delete/(?P<card_id>[0-9]+)//",
        StudentCardDeleteView.as_view(),
        name="delete_student_card",
    ),
    path("admin/<int:counter_id>/", CounterEditView.as_view(), name="admin"),
    path(
        "admin/<int:counter_id>/prop/",
        CounterEditPropView.as_view(),
        name="prop_admin",
    ),
    path("admin/", CounterListView.as_view(), name="admin_list"),
    path("admin/new/", CounterCreateView.as_view(), name="new"),
    path(
        "admin/delete/<int:counter_id>/",
        CounterDeleteView.as_view(),
        name="delete",
    ),
    path("admin/invoices_call/", InvoiceCallView.as_view(), name="invoices_call"),
    path(
        "admin/cash_summary/list/",
        CashSummaryListView.as_view(),
        name="cash_summary_list",
    ),
    path(
        "admin/cash_summary/<int:cashsummary_id>/",
        CashSummaryEditView.as_view(),
        name="cash_summary_edit",
    ),
    path("admin/product/list/", ProductListView.as_view(), name="product_list"),
    path(
        "admin/product/list_archived/",
        ProductArchivedListView.as_view(),
        name="product_list_archived",
    ),
    path("admin/product/create/", ProductCreateView.as_view(), name="new_product"),
    path(
        "admin/product/<int:product_id>/",
        ProductEditView.as_view(),
        name="product_edit",
    ),
    path(
        "admin/producttype/list/",
        ProductTypeListView.as_view(),
        name="producttype_list",
    ),
    path(
        "admin/producttype/create/",
        ProductTypeCreateView.as_view(),
        name="new_producttype",
    ),
    path(
        "admin/producttype/<int:type_id>/",
        ProductTypeEditView.as_view(),
        name="producttype_edit",
    ),
    path("admin/eticket/list/", EticketListView.as_view(), name="eticket_list"),
    path("admin/eticket/new/", EticketCreateView.as_view(), name="new_eticket"),
    path(
        "admin/eticket/<int:eticket_id>/",
        EticketEditView.as_view(),
        name="edit_eticket",
    ),
    path(
        "admin/selling/<int:selling_id>/delete/",
        SellingDeleteView.as_view(),
        name="selling_delete",
    ),
    path(
        "admin/refilling/<int:refilling_id>/delete/",
        RefillingDeleteView.as_view(),
        name="refilling_delete",
    ),
    path(
        "admin/<int:counter_id>/refillings/",
        CounterRefillingListView.as_view(),
        name="refilling_list",
    ),
]
