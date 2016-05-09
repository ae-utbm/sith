from django.views.generic import ListView, DetailView, RedirectView
from django.views.generic.edit import UpdateView, CreateView, DeleteView
from django.shortcuts import render
from django.core.urlresolvers import reverse_lazy

from core.views import CanViewMixin, CanEditMixin, CanEditPropMixin
from accounting.models import BankAccount, ClubAccount, GeneralJournal, Operation, AccountingType

# Accounting types

class AccountingTypeListView(CanViewMixin, ListView):
    """
    A list view for the admins
    """
    model = AccountingType
    template_name = 'accounting/accountingtype_list.jinja'

class AccountingTypeEditView(CanViewMixin, UpdateView):
    """
    An edit view for the admins
    """
    model = AccountingType
    pk_url_kwarg = "type_id"
    fields = ['code', 'label', 'movement_type']
    template_name = 'accounting/account_edit.jinja'

class AccountingTypeCreateView(CanEditPropMixin, CreateView):
    """
    Create an accounting type (for the admins)
    """
    model = AccountingType
    fields = ['code', 'label', 'movement_type']
    template_name = 'accounting/account_edit.jinja'

# BankAccount views

class BankAccountListView(CanViewMixin, ListView):
    """
    A list view for the admins
    """
    model = BankAccount
    template_name = 'accounting/bank_account_list.jinja'

class BankAccountEditView(CanViewMixin, UpdateView):
    """
    An edit view for the admins
    """
    model = BankAccount
    pk_url_kwarg = "b_account_id"
    fields = ['name', 'rib', 'number']
    template_name = 'accounting/account_edit.jinja'

class BankAccountDetailView(CanViewMixin, DetailView):
    """
    A detail view, listing every club account
    """
    model = BankAccount
    pk_url_kwarg = "b_account_id"
    template_name = 'accounting/bank_account_details.jinja'

class BankAccountCreateView(CanEditPropMixin, CreateView):
    """
    Create a bank account (for the admins)
    """
    model = BankAccount
    fields = ['name', 'rib', 'number']
    template_name = 'accounting/account_edit.jinja'

class BankAccountDeleteView(CanEditPropMixin, DeleteView): # TODO change Delete to Close
    """
    Delete a bank account (for the admins)
    """
    model = BankAccount
    pk_url_kwarg = "b_account_id"
    template_name = 'core/delete_confirm.jinja'
    success_url = reverse_lazy('accounting:bank_list')

# ClubAccount views

class ClubAccountEditView(CanViewMixin, UpdateView):
    """
    An edit view for the admins
    """
    model = ClubAccount
    pk_url_kwarg = "c_account_id"
    fields = ['name', 'club', 'bank_account']
    template_name = 'accounting/account_edit.jinja'

class ClubAccountDetailView(CanViewMixin, DetailView):
    """
    A detail view, listing every journal
    """
    model = ClubAccount
    pk_url_kwarg = "c_account_id"
    template_name = 'accounting/club_account_details.jinja'

class ClubAccountCreateView(CanEditPropMixin, CreateView):
    """
    Create a club account (for the admins)
    """
    model = ClubAccount
    fields = ['name', 'club', 'bank_account']
    template_name = 'accounting/account_edit.jinja'

class ClubAccountDeleteView(CanEditPropMixin, DeleteView): # TODO change Delete to Close
    """
    Delete a club account (for the admins)
    """
    model = ClubAccount
    pk_url_kwarg = "c_account_id"
    template_name = 'core/delete_confirm.jinja'
    success_url = reverse_lazy('accounting:bank_list')

# Journal views

class JournalCreateView(CanEditMixin, CreateView):
    """
    Create a general journal
    """
    model = GeneralJournal
    fields = ['name', 'start_date', 'club_account']
    template_name = 'accounting/account_edit.jinja'

class JournalDetailView(CanViewMixin, DetailView):
    """
    A detail view, listing every operation
    """
    model = GeneralJournal
    pk_url_kwarg = "j_id"
    template_name = 'accounting/journal_details.jinja'

class JournalEditView(CanEditMixin, UpdateView):
    """
    Update a general journal
    """
    model = GeneralJournal
    pk_url_kwarg = "j_id"
    fields = ['name', 'start_date', 'club_account']
    template_name = 'accounting/account_edit.jinja'

# Operation views

class OperationCreateView(CanEditMixin, CreateView):
    """
    Create an operation
    """
    model = Operation
    fields = ['journal', 'date', 'cheque_number', 'type']
    template_name = 'accounting/account_edit.jinja'

class OperationEditView(CanViewMixin, UpdateView):
    """
    An edit view, working as detail for the moment
    """
    model = Operation
    pk_url_kwarg = "op_id"
    fields = ['journal', 'date', 'cheque_number', 'type']
    template_name = 'accounting/account_edit.jinja'

