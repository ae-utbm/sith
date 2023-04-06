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

from accounting.views import *

urlpatterns = [
    # Accounting types
    path(
        "simple_type/",
        SimplifiedAccountingTypeListView.as_view(),
        name="simple_type_list",
    ),
    path(
        "simple_type/create/",
        SimplifiedAccountingTypeCreateView.as_view(),
        name="simple_type_new",
    ),
    path(
        "simple_type/<int:type_id>/edit/",
        SimplifiedAccountingTypeEditView.as_view(),
        name="simple_type_edit",
    ),
    # Accounting types
    path("type/", AccountingTypeListView.as_view(), name="type_list"),
    path("type/create/", AccountingTypeCreateView.as_view(), name="type_new"),
    path(
        "type/<int:type_id>/edit/",
        AccountingTypeEditView.as_view(),
        name="type_edit",
    ),
    # Bank accounts
    path("", BankAccountListView.as_view(), name="bank_list"),
    path("bank/create", BankAccountCreateView.as_view(), name="bank_new"),
    path(
        "bank/<int:b_account_id>/",
        BankAccountDetailView.as_view(),
        name="bank_details",
    ),
    path(
        "bank/<int:b_account_id>/edit/",
        BankAccountEditView.as_view(),
        name="bank_edit",
    ),
    path(
        "bank/<int:b_account_id>/delete/",
        BankAccountDeleteView.as_view(),
        name="bank_delete",
    ),
    # Club accounts
    path("club/create/", ClubAccountCreateView.as_view(), name="club_new"),
    path(
        "club/<int:c_account_id>/",
        ClubAccountDetailView.as_view(),
        name="club_details",
    ),
    path(
        "club/<int:c_account_id>/edit/",
        ClubAccountEditView.as_view(),
        name="club_edit",
    ),
    path(
        "club/<int:c_account_id>/delete/",
        ClubAccountDeleteView.as_view(),
        name="club_delete",
    ),
    # Journals
    path("journal/create/", JournalCreateView.as_view(), name="journal_new"),
    path(
        "journal/<int:j_id>/",
        JournalDetailView.as_view(),
        name="journal_details",
    ),
    path(
        "journal/<int:j_id>/edit/",
        JournalEditView.as_view(),
        name="journal_edit",
    ),
    path(
        "journal/<int:j_id>/delete/",
        JournalDeleteView.as_view(),
        name="journal_delete",
    ),
    path(
        "journal/<int:j_id>/statement/nature/",
        JournalNatureStatementView.as_view(),
        name="journal_nature_statement",
    ),
    path(
        "journal/<int:j_id>/statement/person/",
        JournalPersonStatementView.as_view(),
        name="journal_person_statement",
    ),
    path(
        "journal/<int:j_id>/statement/accounting/",
        JournalAccountingStatementView.as_view(),
        name="journal_accounting_statement",
    ),
    # Operations
    path(
        "operation/create/<int:j_id>/",
        OperationCreateView.as_view(),
        name="op_new",
    ),
    path("operation/<int:op_id>/", OperationEditView.as_view(), name="op_edit"),
    path("operation/<int:op_id>/pdf/", OperationPDFView.as_view(), name="op_pdf"),
    # Companies
    path("company/list/", CompanyListView.as_view(), name="co_list"),
    path("company/create/", CompanyCreateView.as_view(), name="co_new"),
    path("company/<int:co_id>/", CompanyEditView.as_view(), name="co_edit"),
    # Labels
    path("label/new/", LabelCreateView.as_view(), name="label_new"),
    path(
        "label/<int:clubaccount_id>/",
        LabelListView.as_view(),
        name="label_list",
    ),
    path("label/<int:label_id>/edit/", LabelEditView.as_view(), name="label_edit"),
    path(
        "label/<int:label_id>/delete/",
        LabelDeleteView.as_view(),
        name="label_delete",
    ),
    # User account
    path("refound/account/", RefoundAccountView.as_view(), name="refound_account"),
]
