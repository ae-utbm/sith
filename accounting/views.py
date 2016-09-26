from django.views.generic import ListView, DetailView, RedirectView
from django.views.generic.edit import UpdateView, CreateView, DeleteView
from django.shortcuts import render
from django.core.urlresolvers import reverse_lazy
from django.forms.models import modelform_factory
from django.forms import HiddenInput
from django import forms

from ajax_select.fields import AutoCompleteSelectField, AutoCompleteSelectMultipleField

from core.views import CanViewMixin, CanEditMixin, CanEditPropMixin, CanCreateMixin
from core.views.forms import SelectFile, SelectDate
from accounting.models import BankAccount, ClubAccount, GeneralJournal, Operation, AccountingType, Company, SimplifiedAccountingType

# Main accounting view

class BankAccountListView(CanViewMixin, ListView):
    """
    A list view for the admins
    """
    model = BankAccount
    template_name = 'accounting/bank_account_list.jinja'
    ordering = ['name']

# Simplified accounting types

class SimplifiedAccountingTypeListView(CanViewMixin, ListView):
    """
    A list view for the admins
    """
    model = SimplifiedAccountingType
    template_name = 'accounting/simplifiedaccountingtype_list.jinja'

class SimplifiedAccountingTypeEditView(CanViewMixin, UpdateView):
    """
    An edit view for the admins
    """
    model = SimplifiedAccountingType
    pk_url_kwarg = "type_id"
    fields = ['label', 'accounting_type']
    template_name = 'core/edit.jinja'

class SimplifiedAccountingTypeCreateView(CanCreateMixin, CreateView):
    """
    Create an accounting type (for the admins)
    """
    model = SimplifiedAccountingType
    fields = ['label', 'accounting_type']
    template_name = 'core/create.jinja'

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
    template_name = 'core/edit.jinja'

class AccountingTypeCreateView(CanCreateMixin, CreateView):
    """
    Create an accounting type (for the admins)
    """
    model = AccountingType
    fields = ['code', 'label', 'movement_type']
    template_name = 'core/create.jinja'

# BankAccount views

class BankAccountEditView(CanViewMixin, UpdateView):
    """
    An edit view for the admins
    """
    model = BankAccount
    pk_url_kwarg = "b_account_id"
    fields = ['name', 'iban', 'number', 'club']
    template_name = 'core/edit.jinja'

class BankAccountDetailView(CanViewMixin, DetailView):
    """
    A detail view, listing every club account
    """
    model = BankAccount
    pk_url_kwarg = "b_account_id"
    template_name = 'accounting/bank_account_details.jinja'

class BankAccountCreateView(CanCreateMixin, CreateView):
    """
    Create a bank account (for the admins)
    """
    model = BankAccount
    fields = ['name', 'club', 'iban', 'number']
    template_name = 'core/create.jinja'

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
    template_name = 'core/edit.jinja'

class ClubAccountDetailView(CanViewMixin, DetailView):
    """
    A detail view, listing every journal
    """
    model = ClubAccount
    pk_url_kwarg = "c_account_id"
    template_name = 'accounting/club_account_details.jinja'

class ClubAccountCreateView(CanCreateMixin, CreateView):
    """
    Create a club account (for the admins)
    """
    model = ClubAccount
    fields = ['name', 'club', 'bank_account']
    template_name = 'core/create.jinja'

    def get_initial(self):
        ret = super(ClubAccountCreateView, self).get_initial()
        if 'parent' in self.request.GET.keys():
            obj = BankAccount.objects.filter(id=int(self.request.GET['parent'])).first()
            if obj is not None:
                ret['bank_account'] = obj.id
        return ret

class ClubAccountDeleteView(CanEditPropMixin, DeleteView): # TODO change Delete to Close
    """
    Delete a club account (for the admins)
    """
    model = ClubAccount
    pk_url_kwarg = "c_account_id"
    template_name = 'core/delete_confirm.jinja'
    success_url = reverse_lazy('accounting:bank_list')

# Journal views

class JournalCreateView(CanCreateMixin, CreateView):
    """
    Create a general journal
    """
    model = GeneralJournal
    form_class = modelform_factory(GeneralJournal, fields=['name', 'start_date', 'club_account'],
            widgets={ 'start_date': SelectDate, })
    template_name = 'core/create.jinja'

    def get_initial(self):
        ret = super(JournalCreateView, self).get_initial()
        if 'parent' in self.request.GET.keys():
            obj = ClubAccount.objects.filter(id=int(self.request.GET['parent'])).first()
            if obj is not None:
                ret['club_account'] = obj.id
        return ret

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
    fields = ['name', 'start_date', 'end_date', 'club_account', 'closed']
    template_name = 'core/edit.jinja'

# Operation views

class OperationForm(forms.ModelForm):
    class Meta:
        model = Operation
        fields = ['amount', 'remark', 'journal', 'target_type', 'target_id', 'target_label', 'date', 'mode',
            'cheque_number', 'invoice', 'simpleaccounting_type', 'accounting_type', 'done']
        widgets = {
                'journal': HiddenInput,
                'target_id': HiddenInput,
                'date': SelectDate,
                'invoice': SelectFile,
                }
    user = AutoCompleteSelectField('users', help_text=None, required=False)
    club_account = AutoCompleteSelectField('club_accounts', help_text=None, required=False)
    club = AutoCompleteSelectField('clubs', help_text=None, required=False)
    company = AutoCompleteSelectField('companies', help_text=None, required=False)

    def __init__(self, *args, **kwargs):
        super(OperationForm, self).__init__(*args, **kwargs)
        if self.instance.target_type == "USER":
            self.fields['user'].initial = self.instance.target_id
        elif self.instance.target_type == "ACCOUNT":
            self.fields['club_account'].initial = self.instance.target_id
        elif self.instance.target_type == "CLUB":
            self.fields['club'].initial = self.instance.target_id
        elif self.instance.target_type == "COMPANY":
            self.fields['company'].initial = self.instance.target_id

    def clean(self):
        self.cleaned_data = super(OperationForm, self).clean()
        if self.cleaned_data['target_type'] == "USER":
            self.cleaned_data['target_id'] = self.cleaned_data['user'].id
        elif self.cleaned_data['target_type'] == "ACCOUNT":
            self.cleaned_data['target_id'] = self.cleaned_data['club_account'].id
        elif self.cleaned_data['target_type'] == "CLUB":
            self.cleaned_data['target_id'] = self.cleaned_data['club'].id
        elif self.cleaned_data['target_type'] == "COMPANY":
            self.cleaned_data['target_id'] = self.cleaned_data['company'].id
        return self.cleaned_data

    def save(self):
        ret = super(OperationForm, self).save()
        if self.instance.target_type == "ACCOUNT" and not self.instance.linked_operation and self.instance.target.has_open_journal():
            inst = self.instance
            club_account = inst.target
            acc_type = AccountingType.objects.exclude(movement_type="NEUTRAL").exclude(
                    movement_type=inst.accounting_type.movement_type).first() # Select a random opposite accounting type
            op = Operation(
                    journal=club_account.get_open_journal(),
                    amount=inst.amount,
                    date=inst.date,
                    remark=inst.remark,
                    mode=inst.mode,
                    cheque_number=inst.cheque_number,
                    invoice=inst.invoice,
                    done=False, # Has to be checked by hand
                    simpleaccounting_type=None,
                    accounting_type=acc_type,
                    target_type="ACCOUNT",
                    target_id=inst.journal.club_account.id,
                    target_label="",
                    linked_operation=inst,
                    )
            op.save()
            self.instance.linked_operation = op
            self.save()
        return ret

class OperationCreateView(CanCreateMixin, CreateView):
    """
    Create an operation
    """
    model = Operation
    form_class = OperationForm
    template_name = 'accounting/operation_edit.jinja'

    def get_initial(self):
        ret = super(OperationCreateView, self).get_initial()
        if 'parent' in self.request.GET.keys():
            self.journal = GeneralJournal.objects.filter(id=int(self.request.GET['parent'])).first()
            if self.journal is not None:
                ret['journal'] = self.journal.id
        return ret

    def get_context_data(self, **kwargs):
        """ Add journal to the context """
        kwargs = super(OperationCreateView, self).get_context_data(**kwargs)
        if self.journal:
            kwargs['object'] = self.journal
        return kwargs

class OperationEditView(CanEditMixin, UpdateView):
    """
    An edit view, working as detail for the moment
    """
    model = Operation
    pk_url_kwarg = "op_id"
    form_class = OperationForm
    template_name = 'accounting/operation_edit.jinja'

    def get_context_data(self, **kwargs):
        """ Add journal to the context """
        kwargs = super(OperationEditView, self).get_context_data(**kwargs)
        kwargs['object'] = self.object.journal
        return kwargs

# Company views

class CompanyCreateView(CanCreateMixin, CreateView):
    """
    Create a company
    """
    model = Company
    fields = ['name']
    template_name = 'core/create.jinja'

class CompanyEditView(CanCreateMixin, UpdateView):
    """
    Edit a company
    """
    model = Company
    pk_url_kwarg = "co_id"
    fields = ['name']
    template_name = 'core/edit.jinja'

