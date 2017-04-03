from django import forms
from django.shortcuts import render
from django.views.generic import ListView, DetailView, TemplateView
from django.views.generic.edit import UpdateView, CreateView
from django.forms import CheckboxSelectMultiple
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext as _t
from django.conf import settings
from ajax_select.fields import AutoCompleteSelectField

from datetime import timedelta

from core.views import CanViewMixin, CanEditMixin, CanEditPropMixin, TabedViewMixin
from core.views.forms import SelectDate, SelectSingle, SelectDateTime
from club.models import Club, Membership
from core.models import User
from sith.settings import SITH_MAXIMUM_FREE_ROLE, SITH_MAIN_BOARD_GROUP
from counter.models import Product, Selling, Counter

class ClubTabsMixin(TabedViewMixin):
    def get_tabs_title(self):
        return self.object.get_display_name()

    def get_list_of_tabs(self):
        tab_list = []
        tab_list.append({
                    'url': reverse('club:club_view', kwargs={'club_id': self.object.id}),
                    'slug': 'infos',
                    'name': _("Infos"),
                    })
        if self.request.user.can_view(self.object):
            tab_list.append({
                        'url': reverse('club:club_members', kwargs={'club_id': self.object.id}),
                        'slug': 'members',
                        'name': _("Members"),
                        })
            tab_list.append({
                        'url': reverse('club:club_old_members', kwargs={'club_id': self.object.id}),
                        'slug': 'elderlies',
                        'name': _("Old members"),
                        })
        if self.request.user.can_edit(self.object):
            tab_list.append({
                        'url': reverse('club:tools', kwargs={'club_id': self.object.id}),
                        'slug': 'tools',
                        'name': _("Tools"),
                        })
            tab_list.append({
                        'url': reverse('club:club_edit', kwargs={'club_id': self.object.id}),
                        'slug': 'edit',
                        'name': _("Edit"),
                        })
            tab_list.append({
                        'url': reverse('club:club_sellings', kwargs={'club_id': self.object.id}),
                        'slug': 'sellings',
                        'name': _("Sellings"),
                        })
        if self.request.user.is_owner(self.object):
            tab_list.append({
                        'url': reverse('club:club_prop', kwargs={'club_id': self.object.id}),
                        'slug': 'props',
                        'name': _("Props"),
                        })
        return tab_list

class ClubListView(ListView):
    """
    List the Clubs
    """
    model = Club
    template_name = 'club/club_list.jinja'

class ClubView(ClubTabsMixin, DetailView):
    """
    Front page of a Club
    """
    model = Club
    pk_url_kwarg = "club_id"
    template_name = 'club/club_detail.jinja'
    current_tab = "infos"

class ClubToolsView(ClubTabsMixin, CanEditMixin, DetailView):
    """
    Tools page of a Club
    """
    model = Club
    pk_url_kwarg = "club_id"
    template_name = 'club/club_tools.jinja'
    current_tab = "tools"

class ClubMemberForm(forms.ModelForm):
    """
    Form handling the members of a club
    """
    error_css_class = 'error'
    required_css_class = 'required'
    class Meta:
        model = Membership
        fields = ['user', 'role', 'start_date', 'description']
        widgets = {
                'start_date': SelectDate
                }
    user = AutoCompleteSelectField('users', required=True, label=_("Select user"), help_text=None)

    def save(self, *args, **kwargs):
        """
        Overloaded to return the club, and not to a Membership object that has no view
        """
        ret = super(ClubMemberForm, self).save(*args, **kwargs)
        return self.instance.club

class ClubMembersView(ClubTabsMixin, CanViewMixin, UpdateView):
    """
    View of a club's members
    """
    model = Club
    pk_url_kwarg = "club_id"
    form_class = ClubMemberForm
    template_name = 'club/club_members.jinja'
    current_tab = "members"

    def get_form(self):
        """
        Here we get a Membership object, but the view handles Club object.
        That's why the save method of ClubMemberForm is overridden.
        """
        form = super(ClubMembersView, self).get_form()
        if 'user' in form.data and form.data.get('user') != '': # Load an existing membership if possible
            form.instance = Membership.objects.filter(club=self.object).filter(user=form.data.get('user')).filter(end_date=None).first()
        if form.instance is None: # Instanciate a new membership
            form.instance = Membership(club=self.object, user=self.request.user)
        if not self.request.user.is_root:
            form.fields.pop('start_date', None)
        # form.initial = {'user': self.request.user}
        # form._user = self.request.user
        return form

    def post(self, request, *args, **kwargs):
        """
            Check user rights
        """
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            ms = self.object.get_membership_for(request.user)
            if (form.cleaned_data['role'] <= SITH_MAXIMUM_FREE_ROLE or
                (ms is not None and ms.role >= form.cleaned_data['role']) or
                request.user.is_board_member or
                request.user.is_root):
                return self.form_valid(form)
            else:
                form.add_error(None, _("You do not have the permission to do that"))
                return self.form_invalid(form)
        else:
            return self.form_invalid(form)

class ClubOldMembersView(ClubTabsMixin, CanViewMixin, DetailView):
    """
    Old members of a club
    """
    model = Club
    pk_url_kwarg = "club_id"
    template_name = 'club/club_old_members.jinja'
    current_tab = "elderlies"

class SellingsFormBase(forms.Form):
    begin_date = forms.DateTimeField(['%Y-%m-%d %H:%M:%S'], label=_("Begin date"), required=False, widget=SelectDateTime)
    end_date = forms.DateTimeField(['%Y-%m-%d %H:%M:%S'], label=_("End date"), required=False, widget=SelectDateTime)
    counter = forms.ModelChoiceField(Counter.objects.order_by('name').all(), label=_("Counter"), required=False)

class ClubSellingView(ClubTabsMixin, CanEditMixin, DetailView):
    """
    Sellings of a club
    """
    model = Club
    pk_url_kwarg = "club_id"
    template_name = 'club/club_sellings.jinja'
    current_tab = "sellings"

    def get_form_class(self):
        kwargs = {
                'product': forms.ModelChoiceField(self.object.products.order_by('name').all(), label=_("Product"), required=False)
                }
        return type('SellingsForm', (SellingsFormBase,), kwargs)

    def get_context_data(self, **kwargs):
        kwargs = super(ClubSellingView, self).get_context_data(**kwargs)
        form = self.get_form_class()(self.request.GET)
        qs = Selling.objects.filter(club=self.object)
        if form.is_valid():
            if not len([v for v in form.cleaned_data.values() if v is not None]):
                qs = Selling.objects.filter(id=-1)
            if form.cleaned_data['begin_date']:
                qs = qs.filter(date__gte=form.cleaned_data['begin_date'])
            if form.cleaned_data['end_date']:
                qs = qs.filter(date__lte=form.cleaned_data['end_date'])
            if form.cleaned_data['counter']:
                qs = qs.filter(counter=form.cleaned_data['counter'])
            if form.cleaned_data['product']:
                qs = qs.filter(product__id=form.cleaned_data['product'].id)
            kwargs['result'] = qs.all().order_by('-id')
            kwargs['total'] = sum([s.quantity * s.unit_price for s in qs.all()])
            kwargs['total_quantity'] = sum([s.quantity for s in qs.all()])
            kwargs['benefit'] = kwargs['total'] - sum([s.product.purchase_price for s in qs.exclude(product=None)])
        else:
            kwargs['result'] = qs[:0]
        kwargs['form'] = form
        return kwargs

class ClubSellingCSVView(ClubSellingView):
    """
    Generate sellings in csv for a given period
    """

    def get(self, request, *args, **kwargs):
        import csv
        response = HttpResponse(content_type='text/csv')
        self.object = self.get_object()
        name = _("Sellings") + "_" + self.object.name + ".csv"
        response['Content-Disposition'] = 'filename=' + name
        kwargs = self.get_context_data(**kwargs)
        writer = csv.writer(response, delimiter=";", lineterminator='\n', quoting=csv.QUOTE_ALL)

        writer.writerow([_t('Quantity'), kwargs['total_quantity']])
        writer.writerow([_t('Total'), kwargs['total']])
        writer.writerow([_t('Benefit'), kwargs['benefit']])
        writer.writerow([_t('Date'),_t('Counter'),_t('Barman'),_t('Customer'),_t('Label'),
                         _t('Quantity'), _t('Total'),_t('Payment method'), _t('Selling price'), _t('Purchase price'), _t('Benefit')])
        for o in kwargs['result']:
            row = [o.date, o.counter]
            if o.seller:
                row.append(o.seller.get_display_name())
            else: row.append('')
            if o.customer:
                row.append(o.customer.user.get_display_name())
            else: row.append('')
            row = row +[o.label, o.quantity, o.quantity * o.unit_price,
                       o.get_payment_method_display()]
            if o.product:
                row.append(o.product.selling_price)
                row.append(o.product.purchase_price)
                row.append(o.product.selling_price - o.product.purchase_price)
            else: row = row + ['', '', '']
            writer.writerow(row)

        return response

class ClubEditView(ClubTabsMixin, CanEditMixin, UpdateView):
    """
    Edit a Club's main informations (for the club's members)
    """
    model = Club
    pk_url_kwarg = "club_id"
    fields = ['address']
    template_name = 'core/edit.jinja'
    current_tab = "edit"

class ClubEditPropView(ClubTabsMixin, CanEditPropMixin, UpdateView):
    """
    Edit the properties of a Club object (for the Sith admins)
    """
    model = Club
    pk_url_kwarg = "club_id"
    fields = ['name', 'unix_name', 'parent']
    template_name = 'core/edit.jinja'
    current_tab = "props"

class ClubCreateView(CanEditPropMixin, CreateView):
    """
    Create a club (for the Sith admin)
    """
    model = Club
    pk_url_kwarg = "club_id"
    fields = ['name', 'unix_name', 'parent']
    template_name = 'core/edit.jinja'

class MembershipSetOldView(CanEditMixin, DetailView):
    """
    Set a membership as beeing old
    """
    model = Membership
    pk_url_kwarg = "membership_id"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.end_date = timezone.now()
        self.object.save()
        return HttpResponseRedirect(reverse('club:club_members', args=self.args, kwargs={'club_id': self.object.club.id}))

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return HttpResponseRedirect(reverse('club:club_members', args=self.args, kwargs={'club_id': self.object.club.id}))

class ClubStatView(TemplateView):
    template_name="club/stats.jinja"

    def get_context_data(self, **kwargs):
        kwargs = super(ClubStatView, self).get_context_data(**kwargs)
        kwargs['club_list'] = Club.objects.all()
        return kwargs
