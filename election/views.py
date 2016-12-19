from django.shortcuts import render
from django.views.generic import ListView, DetailView, RedirectView
from django.views.generic.edit import UpdateView, CreateView, DeleteView, FormView
from django.core.urlresolvers import reverse_lazy, reverse
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.conf import settings

from core.views import CanViewMixin, CanEditMixin, CanEditPropMixin, CanCreateMixin
from election.models import Election, Role, Candidature

# Display elections


class ElectionsListView(CanViewMixin, ListView):
    """
    A list with all responsabilities and their candidates
    """
    model = Election
    template_name = 'election/election_list.jinja'

    def get_queryset(self):
        qs = super(ElectionsListView, self).get_queryset()
        today = timezone.now()
        qs = qs.filter(end_date__gte=today, start_date__lte=today)
        return qs


class ElectionDetailView(CanViewMixin, DetailView):
    """
    Details an election responsability by responsability
    """
    model = Election
    template_name = 'election/election_detail.jinja'
    pk_url_kwarg = "election_id"

# Forms
