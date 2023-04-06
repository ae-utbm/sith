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
        "customer/<int:customer_id>/card/delete/<int:card_id>/",
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
