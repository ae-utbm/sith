from django.views.generic import ListView, DetailView, RedirectView
from django.views.generic.edit import UpdateView, CreateView, DeleteView, FormView
from django.shortcuts import render
from django.core.urlresolvers import reverse_lazy, reverse
from django.utils.translation import ugettext_lazy as _
from django.forms.models import modelform_factory
from django.core.exceptions import PermissionDenied
from django.forms import HiddenInput
from django.db import transaction
from django.conf import settings
from django import forms
from django.http import HttpResponseRedirect, HttpResponse
from django.utils.translation import ugettext as _
from django.conf import settings


from ajax_select.fields import AutoCompleteSelectField, AutoCompleteSelectMultipleField

from core.views import CanViewMixin, CanEditMixin, CanEditPropMixin, CanCreateMixin
from core.views.forms import SelectFile, SelectDate
from accounting.models import BankAccount, ClubAccount, GeneralJournal, Operation, AccountingType, Company, SimplifiedAccountingType, Label
from counter.models import Counter, Selling

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
            'cheque_number', 'invoice', 'simpleaccounting_type', 'accounting_type', 'label', 'done']
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
        club_account = kwargs.pop('club_account', None)
        super(OperationForm, self).__init__(*args, **kwargs)
        if club_account:
            self.fields['label'].queryset = club_account.labels.order_by('name').all()
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

    def get_form(self, form_class=None):
        self.journal = GeneralJournal.objects.filter(id=self.kwargs['j_id']).first()
        ca = self.journal.club_account if self.journal else None
        return self.form_class(club_account=ca, **self.get_form_kwargs())

    def get_initial(self):
        ret = super(OperationCreateView, self).get_initial()
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

class OperationPDFView(CanViewMixin, DetailView):
    """
    Display the PDF of a given operation
    """

    model = Operation
    pk_url_kwarg = "op_id"

    def get(self, request, *args, **kwargs):
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.utils import ImageReader
        from reportlab.graphics.shapes import Drawing
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.pdfbase import pdfmetrics

        pdfmetrics.registerFont(TTFont('DejaVu', 'DejaVuSerif.ttf'))



        self.object = self.get_object()
        amount = self.object.amount
        remark = self.object.remark
        nature = self.object.accounting_type.movement_type
        num = self.object.number
        date = self.object.date
        mode = self.object.mode
        cheque_number = self.object.cheque_number
        club_name = self.object.journal.club_account.name
        ti = self.object.journal.name
        op_label = self.object.label
        club_address = self.object.journal.club_account.club.address
        id_op = self.object.id

        if self.object.target_type == "OTHER":
            target = self.object.target_label
        else:
            target = self.object.target.get_display_name()


        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="op-%d(%s_on_%s).pdf"'  %(num, ti, club_name)
        p = canvas.Canvas(response)

        p.setFont('DejaVu', 12)

        p.setTitle("%s %d" % (_("Operation"), num))
        width, height = letter
        im = ImageReader("core/static/core/img/logo.jpg")
        iw, ih = im.getSize()
        p.drawImage(im, 40, height - 50, width=iw/2, height=ih/2)

        labelStr = [["%s %s - %s %s" % (_("Journal"), ti, _("Operation"), num)]]

        label = Table(labelStr, colWidths=[150], rowHeights=[20])

        label.setStyle(TableStyle([
                                ('ALIGN',(0,0),(-1,-1),'CENTER'),
                                ('BOX', (0,0), (-1,-1), 0.25, colors.black),
                                ]))
        w, h = label.wrapOn(label, 0, 0)
        label.drawOn(p, width-180, height)

        p.drawString(90, height - 100, _("Financial proof: ") + "OP%010d" % (id_op)) #Justificatif du libellé
        p.drawString(90, height - 130, _("Club: %(club_name)s") % ({"club_name": club_name}))
        p.drawString(90, height - 160, _("Label: %(op_label)s") % {"op_label": op_label if op_label != None else ""})

        data = []

        data += [["%s" % (_("Credit").upper() if nature == 'CREDIT' else _("Debit").upper())]]

        data += [[_("Amount: %(amount).2f €") % {"amount": amount}]]

        payment_mode = ""
        for m in settings.SITH_ACCOUNTING_PAYMENT_METHOD:
            if m[0] == mode:
                payment_mode += "[\u00D7]"
            else:
                payment_mode += "[  ]"
            payment_mode += " %s\n" %(m[1])

        data += [[payment_mode]]

        data += [["%s : %s" % (_("Debtor") if nature == 'CREDIT' else _("Creditor"), target), ""]]

        data += [["%s \n%s" % (_("Comment:"), remark)]]

        t = Table(data, colWidths=[(width-90*2)/2]*2, rowHeights=[20, 20, 70, 20, 80])
        t.setStyle(TableStyle([
                        ('ALIGN',(0,0),(-1,-1),'CENTER'),
                        ('VALIGN',(-2,-1),(-1,-1),'TOP'),
                        ('VALIGN',(0,0),(-1,-2),'MIDDLE'),
                        ('INNERGRID', (0,0), (-1,-1), 0.25, colors.black),
                        ('SPAN', (0, 0), (1, 0)), # line DEBIT/CREDIT
                        ('SPAN', (0, 1), (1, 1)), # line amount
                        ('SPAN',(-2, -1), (-1,-1)), # line comment
                        ('SPAN', (0, -2), (-1, -2)), # line creditor/debtor
                        ('SPAN', (0, 2), (1, 2)), # line payment_mode
                        ('ALIGN',(0, 2), (1, 2),'LEFT'), # line payment_mode
                        ('ALIGN', (-2, -1), (-1, -1), 'LEFT'),
                        ('BOX', (0,0), (-1,-1), 0.25, colors.black),
                        ]))

        w, h = t.wrapOn(p, 0, 0)

        t.drawOn(p, 90, 350)



        p.drawCentredString(10.5 * cm, 2 * cm, club_name)
        p.drawCentredString(10.5 * cm, 1 * cm, club_address)

        p.showPage()
        p.save()
        return response

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

# Label views

class LabelListView(CanViewMixin, DetailView):
    model = ClubAccount
    pk_url_kwarg = "clubaccount_id"
    template_name = 'accounting/label_list.jinja'

class LabelCreateView(CanEditMixin, CreateView): # FIXME we need to check the rights before creating the object
    model = Label
    form_class = modelform_factory(Label, fields=['name', 'club_account'], widgets={
        'club_account': HiddenInput,
        })
    template_name = 'core/create.jinja'

    def get_initial(self):
        ret = super(LabelCreateView, self).get_initial()
        if 'parent' in self.request.GET.keys():
            obj = ClubAccount.objects.filter(id=int(self.request.GET['parent'])).first()
            if obj is not None:
                ret['club_account'] = obj.id
        return ret

class LabelEditView(CanEditMixin, UpdateView):
    model = Label
    pk_url_kwarg = "label_id"
    fields = ['name']
    template_name = 'core/edit.jinja'

class LabelDeleteView(CanEditMixin, DeleteView):
    model = Label
    pk_url_kwarg = "label_id"
    template_name = 'core/delete_confirm.jinja'

    def get_success_url(self):
        return self.object.get_absolute_url()

class CloseCustomerAccountForm(forms.Form):
    user = AutoCompleteSelectField('users', label=_('Refound this account'), help_text=None, required=True)

class RefoundAccountView(FormView):
    """
    Create a selling with the same amount than the current user money
    """
    template_name = "accounting/refound_account.jinja"
    form_class = CloseCustomerAccountForm

    def permission(self, user):
        if user.is_root or user.is_in_group(settings.SITH_GROUP_ACCOUNTING_ADMIN_ID):
            return True
        else:
            raise PermissionDenied

    def dispatch(self, request, *arg, **kwargs):
        res = super(RefoundAccountView, self).dispatch(request, *arg, **kwargs)
        if self.permission(request.user):
            return res

    def post(self, request, *arg, **kwargs):
        self.operator = request.user
        if self.permission(request.user):
            return super(RefoundAccountView, self).post(self, request, *arg, **kwargs)

    def form_valid(self, form):
        self.customer = form.cleaned_data['user']
        self.create_selling()
        return super(RefoundAccountView, self).form_valid(form)

    def get_success_url(self):
        return reverse('accounting:refound_account')

    def create_selling(self):
        with transaction.atomic():
            uprice = self.customer.customer.amount
            main_club_counter = Counter.objects.filter(club__unix_name=settings.SITH_MAIN_CLUB['unix_name'],
                                                       type='OFFICE').first()
            main_club = main_club_counter.club
            s = Selling(label=_('Refound account'), unit_price=uprice,
                        quantity=1, seller=self.operator,
                        customer=self.customer.customer,
                        club=main_club, counter=main_club_counter)
            s.save()
