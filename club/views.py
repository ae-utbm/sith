from django.shortcuts import render
from django.views.generic import ListView, DetailView
from django.views.generic.edit import UpdateView
from core.views import CanViewMixin, CanEditMixin, CanEditPropMixin

from club.models import Club, Membership

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

class ClubEditMembersView(CanEditMixin, UpdateView):
    model = Club
    pk_url_kwarg = "club_id"
    fields = ['user']
    template_name = 'club/club_members.jinja'

class ClubEditPropView(CanEditPropMixin, UpdateView):
    model = Club
    pk_url_kwarg = "club_id"
    fields = ['name', 'address', 'parent']
    template_name = 'club/club_edit_prop.jinja'

