# -*- coding:utf-8 -*
#
# Copyright 2016,2017
# - Skia <skia@libskia.so>
# - Sli <antoine@bartuccio.fr>
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

from django import forms
from django.views.generic import ListView, DetailView, TemplateView
from django.views.generic.edit import DeleteView
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import UpdateView, CreateView
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse, reverse_lazy
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext as _t
from ajax_select.fields import AutoCompleteSelectField
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.core.validators import RegexValidator, validate_email

from core.views import CanViewMixin, CanEditMixin, CanEditPropMixin, TabedViewMixin
from core.views.forms import SelectDate, SelectDateTime
from club.models import Club, Membership, Mailing, MailingSubscription
from sith.settings import SITH_MAXIMUM_FREE_ROLE
from counter.models import Selling, Counter
from core.models import User

from django.conf import settings

# Custom forms


class MailingForm(forms.ModelForm):
    class Meta:
        model = Mailing
        fields = ('email', 'club', 'moderator')

    email = forms.CharField(
        label=_('Email address'),
        validators=[
            RegexValidator(
                validate_email.user_regex,
                _('Enter a valid address. Only the root of the address is needed.')
            )
        ],
        required=True)

    def __init__(self, *args, **kwargs):
        club_id = kwargs.pop('club_id', None)
        user_id = kwargs.pop('user_id', -1)  # Remember 0 is treated as None
        super(MailingForm, self).__init__(*args, **kwargs)
        if club_id:
            self.fields['club'].queryset = Club.objects.filter(id=club_id)
            self.fields['club'].initial = club_id
            self.fields['club'].widget = forms.HiddenInput()
        if user_id >= 0:
            self.fields['moderator'].queryset = User.objects.filter(id=user_id)
            self.fields['moderator'].initial = user_id
            self.fields['moderator'].widget = forms.HiddenInput()

    def clean(self):
        cleaned_data = super(MailingForm, self).clean()
        if self.is_valid():
            cleaned_data['email'] += '@' + settings.SITH_MAILING_DOMAIN
        return cleaned_data


class MailingSubscriptionForm(forms.ModelForm):
    class Meta:
        model = MailingSubscription
        fields = ('mailing', 'user', 'email')

    def __init__(self, *args, **kwargs):
        kwargs.pop('user_id', None)  # For standart interface
        club_id = kwargs.pop('club_id', None)
        super(MailingSubscriptionForm, self).__init__(*args, **kwargs)
        self.fields['email'].required = False
        if club_id:
            self.fields['mailing'].queryset = Mailing.objects.filter(club__id=club_id, is_moderated=True)

    user = AutoCompleteSelectField('users', label=_('User'), help_text=None, required=False)


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
            tab_list.append({
                'url': reverse('club:mailing', kwargs={'club_id': self.object.id}),
                'slug': 'mailing',
                        'name': _("Mailing list"),
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
        super(ClubMemberForm, self).save(*args, **kwargs)
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
        if 'user' in form.data and form.data.get('user') != '':  # Load an existing membership if possible
            form.instance = Membership.objects.filter(club=self.object).filter(user=form.data.get('user')).filter(end_date=None).first()
        if form.instance is None:  # Instanciate a new membership
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
        writer.writerow([_t('Date'), _t('Counter'), _t('Barman'), _t('Customer'), _t('Label'),
                         _t('Quantity'), _t('Total'), _t('Payment method'), _t('Selling price'), _t('Purchase price'), _t('Benefit')])
        for o in kwargs['result']:
            row = [o.date, o.counter]
            if o.seller:
                row.append(o.seller.get_display_name())
            else:
                row.append('')
            if o.customer:
                row.append(o.customer.user.get_display_name())
            else:
                row.append('')
            row = row + [o.label, o.quantity, o.quantity * o.unit_price,
                         o.get_payment_method_display()]
            if o.product:
                row.append(o.product.selling_price)
                row.append(o.product.purchase_price)
                row.append(o.product.selling_price - o.product.purchase_price)
            else:
                row = row + ['', '', '']
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
    template_name = "club/stats.jinja"

    def get_context_data(self, **kwargs):
        kwargs = super(ClubStatView, self).get_context_data(**kwargs)
        kwargs['club_list'] = Club.objects.all()
        return kwargs


class ClubMailingView(ClubTabsMixin, ListView):
    """
    A list of mailing for a given club
    """
    action = None
    model = Mailing
    template_name = "club/mailing.jinja"
    current_tab = 'mailing'

    def authorized(self):
        return self.club.has_rights_in_club(self.user) or self.user.is_root or self.user.is_in_group(settings.SITH_GROUP_COM_ADMIN_ID)

    def dispatch(self, request, *args, **kwargs):
        self.club = get_object_or_404(Club, pk=kwargs['club_id'])
        self.user = request.user
        self.object = self.club
        if not self.authorized():
            raise PermissionDenied
        self.member_form = MailingSubscriptionForm(club_id=self.club.id)
        self.mailing_form = MailingForm(club_id=self.club.id, user_id=self.user.id)
        return super(ClubMailingView, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        res = super(ClubMailingView, self).get(request, *args, **kwargs)
        if self.action != "display":
            if self.action == "add_mailing":
                form = MailingForm
                model = Mailing
            elif self.action == "add_member":
                form = MailingSubscriptionForm
                model = MailingSubscription
            return MailingGenericCreateView.as_view(model=model, list_view=self, form_class=form)(request, *args, **kwargs)
        return res

    def get_queryset(self):
        return Mailing.objects.filter(club_id=self.club.id).all()

    def get_context_data(self, **kwargs):
        kwargs = super(ClubMailingView, self).get_context_data(**kwargs)
        kwargs['add_member'] = self.member_form
        kwargs['add_mailing'] = self.mailing_form
        kwargs['club'] = self.club
        kwargs['user'] = self.user
        kwargs['has_objects'] = len(kwargs['object_list']) > 0
        return kwargs


class MailingGenericCreateView(CreateView, SingleObjectMixin):
    """
    Create a new mailing list
    """
    list_view = None
    form_class = None

    def get_context_data(self, **kwargs):
        view_kwargs = self.list_view.get_context_data(**kwargs)
        for key, data in super(MailingGenericCreateView, self).get_context_data(**kwargs).items():
            view_kwargs[key] = data
        view_kwargs[self.list_view.action] = view_kwargs['form']
        return view_kwargs

    def get_form_kwargs(self):
        kwargs = super(MailingGenericCreateView, self).get_form_kwargs()
        kwargs['club_id'] = self.list_view.club.id
        kwargs['user_id'] = self.list_view.user.id
        return kwargs

    def dispatch(self, request, *args, **kwargs):
        if not self.list_view.authorized():
            raise PermissionDenied
        self.template_name = self.list_view.template_name
        return super(MailingGenericCreateView, self).dispatch(request, *args, **kwargs)

    def get_success_url(self, **kwargs):
        return reverse_lazy('club:mailing', kwargs={'club_id': self.list_view.club.id})


class MailingDeleteView(CanEditMixin, DeleteView):

    model = Mailing
    template_name = 'core/delete_confirm.jinja'
    pk_url_kwarg = "mailing_id"
    redirect_page = None

    def dispatch(self, request, *args, **kwargs):
        self.club_id = self.get_object().club.id
        return super(MailingDeleteView, self).dispatch(request, *args, **kwargs)

    def get_success_url(self, **kwargs):
        if self.redirect_page:
            return reverse_lazy(self.redirect_page)
        else:
            return reverse_lazy('club:mailing', kwargs={'club_id': self.club_id})


class MailingSubscriptionDeleteView(CanEditMixin, DeleteView):

    model = MailingSubscription
    template_name = 'core/delete_confirm.jinja'
    pk_url_kwarg = "mailing_subscription_id"

    def dispatch(self, request, *args, **kwargs):
        self.club_id = self.get_object().mailing.club.id
        return super(MailingSubscriptionDeleteView, self).dispatch(request, *args, **kwargs)

    def get_success_url(self, **kwargs):
        return reverse_lazy('club:mailing', kwargs={'club_id': self.club_id})
