from django.shortcuts import render
from django.views.generic import ListView, DetailView, RedirectView
from django.views.generic.edit import UpdateView, CreateView, DeleteView, FormView
from django.core.urlresolvers import reverse_lazy, reverse
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

from core.views import CanViewMixin, CanEditMixin, CanEditPropMixin, CanCreateMixin
from election.models import Election, Responsability, Candidate

# Display elections


class ElectionsListView(CanViewMixin, ListView):
    """
    A list with all responsabilities and their candidates
    """
    model = Election
    template_name = 'election/election_list.jinja'


class ElectionDetailView(CanViewMixin, DetailView):
    """
    Details an election responsability by responsability
    """
    model = Election
    template_name = 'election/election_detail.jinja'
    pk_url_kwarg = "election_id"

# Forms
