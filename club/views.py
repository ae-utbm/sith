from django import forms
from django.shortcuts import render
from django.views.generic import ListView, DetailView
from django.views.generic.edit import UpdateView, CreateView
from django.forms import CheckboxSelectMultiple
from django.core.exceptions import ValidationError


from core.views import CanViewMixin, CanEditMixin, CanEditPropMixin
from club.models import Club, Membership
from subscription.views import SubscriberMixin

class ClubListView(CanViewMixin, ListView):
    model = Club
    template_name = 'club/club_list.jinja'

class ClubView(CanViewMixin, DetailView):
    model = Club
    pk_url_kwarg = "club_id"
    template_name = 'club/club_detail.jinja'

class ClubEditView(CanEditMixin, UpdateView):
    model = Club
    pk_url_kwarg = "club_id"
    fields = ['address']
    template_name = 'club/club_edit.jinja'

class ClubMemberForm(forms.ModelForm):
    error_css_class = 'error'
    required_css_class = 'required'
    class Meta:
        model = Membership
        fields = ['user', 'role']

    def clean(self):
        ret = super(ClubMemberForm, self).clean()
        ms = self.instance.club.get_membership_for(self._user)
        if ms is not None and ms.role >= self.cleaned_data['role']:
            return ret
        raise ValidationError("You do not have the permission to do that")

class ClubMembersView(CanViewMixin, UpdateView):
    model = Club
    pk_url_kwarg = "club_id"
    form_class = ClubMemberForm
    template_name = 'club/club_members.jinja'

    def __init__(self, *args, **kwargs):
        super(ClubMembersView, self).__init__(*args, **kwargs)
    # TODO FIXME: error forbidden when adding new member to club, because self.object changes to the Membership object
    # somewhere!!!

    def get_form(self):
        form = super(ClubMembersView, self).get_form()
        if 'user' in form.data and form.data.get('user') != '': # Load an existing membership if possible
            form.instance = Membership.objects.filter(club=self.object).filter(user=form.data.get('user')).filter(end_date=None).first()
        if form.instance is None: # Instanciate a new membership
            form.instance = Membership(club=self.object, user=self.request.user)
        form.initial = {'user': self.request.user}
        form._user = self.request.user
        return form

class ClubEditPropView(CanEditPropMixin, UpdateView):
    model = Club
    pk_url_kwarg = "club_id"
    fields = ['name', 'address', 'parent']
    template_name = 'club/club_edit_prop.jinja'

