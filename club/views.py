from django import forms
from django.shortcuts import render
from django.views.generic import ListView, DetailView
from django.views.generic.edit import UpdateView, CreateView
from django.forms import CheckboxSelectMultiple
from django.core.exceptions import ValidationError


from core.views import CanViewMixin, CanEditMixin, CanEditPropMixin
from club.models import Club, Membership
from sith.settings import SITH_MAXIMUM_FREE_ROLE, SITH_MAIN_BOARD_GROUP

class ClubListView(CanViewMixin, ListView):
    """
    List the Clubs
    """
    model = Club
    template_name = 'club/club_list.jinja'

class ClubView(CanViewMixin, DetailView):
    """
    Front page of a Club
    """
    model = Club
    pk_url_kwarg = "club_id"
    template_name = 'club/club_detail.jinja'

class ClubToolsView(CanEditMixin, DetailView):
    """
    Tools page of a Club
    """
    model = Club
    pk_url_kwarg = "club_id"
    template_name = 'club/club_tools.jinja'

class ClubMemberForm(forms.ModelForm):
    """
    Form handling the members of a club
    """
    error_css_class = 'error'
    required_css_class = 'required'
    class Meta:
        model = Membership
        fields = ['user', 'role']

    def clean(self):
        """
        Validates the permissions
        e.g.: the president can add anyone anywhere, but a member can not make someone become president
        """
        ret = super(ClubMemberForm, self).clean()
        ms = self.instance.club.get_membership_for(self._user)
        if (self.cleaned_data['role'] <= SITH_MAXIMUM_FREE_ROLE or
            (ms is not None and ms.role >= self.cleaned_data['role']) or
            self._user.is_in_group(SITH_MAIN_BOARD_GROUP) or
            self._user.is_superuser):
            return ret
        raise ValidationError("You do not have the permission to do that")

    def save(self, *args, **kwargs):
        """
        Overloaded to return the club, and not to a Membership object that has no view
        """
        ret = super(ClubMemberForm, self).save(*args, **kwargs)
        return self.instance.club

class ClubMembersView(CanViewMixin, UpdateView):
    """
    View of a club's members
    """
    model = Club
    pk_url_kwarg = "club_id"
    form_class = ClubMemberForm
    template_name = 'club/club_members.jinja'

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
        form.initial = {'user': self.request.user}
        form._user = self.request.user
        return form

class ClubEditView(CanEditMixin, UpdateView):
    """
    Edit a Club's main informations (for the club's members)
    """
    model = Club
    pk_url_kwarg = "club_id"
    fields = ['address']
    template_name = 'club/club_edit.jinja'

class ClubEditPropView(CanEditPropMixin, UpdateView):
    """
    Edit the properties of a Club object (for the Sith admins)
    """
    model = Club
    pk_url_kwarg = "club_id"
    fields = ['name', 'unix_name', 'parent']
    template_name = 'club/club_edit_prop.jinja'


class ClubCreateView(CanEditPropMixin, CreateView):
    """
    Create a club (for the Sith admin)
    """
    model = Club
    pk_url_kwarg = "club_id"
    fields = ['name', 'unix_name', 'parent']
    template_name = 'club/club_edit_prop.jinja'

