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

from accounting.views import *

urlpatterns = [
    # Accounting types
    url(
        r"^simple_type$",
        SimplifiedAccountingTypeListView.as_view(),
        name="simple_type_list",
    ),
    url(
        r"^simple_type/create$",
        SimplifiedAccountingTypeCreateView.as_view(),
        name="simple_type_new",
    ),
    url(
        r"^simple_type/(?P<type_id>[0-9]+)/edit$",
        SimplifiedAccountingTypeEditView.as_view(),
        name="simple_type_edit",
    ),
    # Accounting types
    url(r"^type$", AccountingTypeListView.as_view(), name="type_list"),
    url(r"^type/create$", AccountingTypeCreateView.as_view(), name="type_new"),
    url(
        r"^type/(?P<type_id>[0-9]+)/edit$",
        AccountingTypeEditView.as_view(),
        name="type_edit",
    ),
    # Bank accounts
    url(r"^$", BankAccountListView.as_view(), name="bank_list"),
    url(r"^bank/create$", BankAccountCreateView.as_view(), name="bank_new"),
    url(
        r"^bank/(?P<b_account_id>[0-9]+)$",
        BankAccountDetailView.as_view(),
        name="bank_details",
    ),
    url(
        r"^bank/(?P<b_account_id>[0-9]+)/edit$",
        BankAccountEditView.as_view(),
        name="bank_edit",
    ),
    url(
        r"^bank/(?P<b_account_id>[0-9]+)/delete$",
        BankAccountDeleteView.as_view(),
        name="bank_delete",
    ),
    # Club accounts
    url(r"^club/create$", ClubAccountCreateView.as_view(), name="club_new"),
    url(
        r"^club/(?P<c_account_id>[0-9]+)$",
        ClubAccountDetailView.as_view(),
        name="club_details",
    ),
    url(
        r"^club/(?P<c_account_id>[0-9]+)/edit$",
        ClubAccountEditView.as_view(),
        name="club_edit",
    ),
    url(
        r"^club/(?P<c_account_id>[0-9]+)/delete$",
        ClubAccountDeleteView.as_view(),
        name="club_delete",
    ),
    # Journals
    url(r"^journal/create$", JournalCreateView.as_view(), name="journal_new"),
    url(
        r"^journal/(?P<j_id>[0-9]+)$",
        JournalDetailView.as_view(),
        name="journal_details",
    ),
    url(
        r"^journal/(?P<j_id>[0-9]+)/edit$",
        JournalEditView.as_view(),
        name="journal_edit",
    ),
    url(
        r"^journal/(?P<j_id>[0-9]+)/delete$",
        JournalDeleteView.as_view(),
        name="journal_delete",
    ),
    url(
        r"^journal/(?P<j_id>[0-9]+)/statement/nature$",
        JournalNatureStatementView.as_view(),
        name="journal_nature_statement",
    ),
    url(
        r"^journal/(?P<j_id>[0-9]+)/statement/person$",
        JournalPersonStatementView.as_view(),
        name="journal_person_statement",
    ),
    url(
        r"^journal/(?P<j_id>[0-9]+)/statement/accounting$",
        JournalAccountingStatementView.as_view(),
        name="journal_accounting_statement",
    ),
    # Operations
    url(
        r"^operation/create/(?P<j_id>[0-9]+)$",
        OperationCreateView.as_view(),
        name="op_new",
    ),
    url(r"^operation/(?P<op_id>[0-9]+)$", OperationEditView.as_view(), name="op_edit"),
    url(
        r"^operation/(?P<op_id>[0-9]+)/pdf$", OperationPDFView.as_view(), name="op_pdf"
    ),
    # Companies
    url(r"^company/list$", CompanyListView.as_view(), name="co_list"),
    url(r"^company/create$", CompanyCreateView.as_view(), name="co_new"),
    url(r"^company/(?P<co_id>[0-9]+)$", CompanyEditView.as_view(), name="co_edit"),
    # Labels
    url(r"^label/new$", LabelCreateView.as_view(), name="label_new"),
    url(
        r"^label/(?P<clubaccount_id>[0-9]+)$",
        LabelListView.as_view(),
        name="label_list",
    ),
    url(
        r"^label/(?P<label_id>[0-9]+)/edit$", LabelEditView.as_view(), name="label_edit"
    ),
    url(
        r"^label/(?P<label_id>[0-9]+)/delete$",
        LabelDeleteView.as_view(),
        name="label_delete",
    ),
    # User account
    url(r"^refound/account$", RefoundAccountView.as_view(), name="refound_account"),
]
