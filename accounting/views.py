from django.views.generic import ListView, DetailView, RedirectView
from django.views.generic.edit import UpdateView, CreateView, DeleteView
from django.shortcuts import render
from django.core.urlresolvers import reverse_lazy

from core.views import CanViewMixin, CanEditMixin, CanEditPropMixin
from accounting.models import BankAccount, ClubAccount, GeneralJournal, Operation

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

class BankAccountCreateView(CanEditMixin, CreateView):
    """
    Create a bank account (for the admins)
    """
    model = BankAccount
    fields = ['name', 'rib', 'number']
    template_name = 'accounting/account_edit.jinja'

class BankAccountDeleteView(CanEditMixin, DeleteView):
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

class ClubAccountCreateView(CanEditMixin, CreateView):
    """
    Create a club account (for the admins)
    """
    model = ClubAccount
    fields = ['name', 'club', 'bank_account']
    template_name = 'accounting/account_edit.jinja'

class ClubAccountDeleteView(CanEditMixin, DeleteView):
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
    fields = ['name']
    template_name = 'accounting/account_edit.jinja'

