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

from accounting.views import *

urlpatterns = [
    # Accounting types
    path(
        "simple_type/",
        SimplifiedAccountingTypeListView.as_view,
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
    path("type/<int:type_id>/edit", AccountingTypeEditView.as_view(), name="type_edit"),
    # Bank accounts
    path("", BankAccountListView.as_view(), name="bank_list"),
    path("bank/create/", BankAccountCreateView.as_view(), name="bank_new"),
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
        "club<int:c_account_id>/delete/",
        ClubAccountDeleteView.as_view(),
        name="club_delete",
    ),
    # Journals
    path("journal/create/", JournalCreateView.as_view(), name="journal_new"),
    path("journal/<int:j_id>/", JournalDetailView.as_view(), name="journal_details"),
    path("journal/<int:j_id>/edit/", JournalEditView.as_view(), name="journal_edit"),
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
