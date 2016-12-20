from django.shortcuts import render
from django.views.generic import ListView, DetailView, RedirectView
from django.views.generic.edit import UpdateView, CreateView, DeleteView, FormView
from django.core.urlresolvers import reverse_lazy, reverse
from django.utils.translation import ugettext_lazy as _
from django.forms.models import modelform_factory
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist, ImproperlyConfigured
from django.forms import CheckboxSelectMultiple
from django.utils import timezone
from django.conf import settings
from django import forms

from core.views import CanViewMixin, CanEditMixin, CanEditPropMixin, CanCreateMixin
from core.views.forms import SelectDateTime
from core.widgets import ChoiceWithOtherField
from election.models import Election, Role, Candidature, ElectionList

from ajax_select.fields import AutoCompleteSelectField


# Forms


class CandidateForm(forms.Form):
    """ Form to candidate """
    user = AutoCompleteSelectField('users', label=_('User to candidate'), help_text=None, required=True)
    program = forms.CharField(widget=forms.Textarea)

    def __init__(self, election_id, *args, **kwargs):
        super(CandidateForm, self).__init__(*args, **kwargs)
        self.fields['role'] = forms.ModelChoiceField(Role.objects.filter(election__id=election_id))
        self.fields['election_list'] = forms.ModelChoiceField(ElectionList.objects.filter(election__id=election_id))

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

    def get_context_data(self, **kwargs):
        """ Add additionnal data to the template """
        kwargs = super(ElectionDetailView, self).get_context_data(**kwargs)
        kwargs['candidate_form'] = CandidateForm(self.get_object().id)
        return kwargs

# Create views

class ElectionCreateView(CanCreateMixin, CreateView):
    model = Election
    form_class = modelform_factory(Election,
        fields=['title', 'description', 'start_candidature', 'end_candidature', 'start_date', 'end_date',
                'edit_groups', 'view_groups', 'vote_groups', 'candidature_groups'],
        widgets={
            'edit_groups': CheckboxSelectMultiple,
            'view_groups': CheckboxSelectMultiple,
            'edit_groups': CheckboxSelectMultiple,
            'vote_groups': CheckboxSelectMultiple,
            'candidature_groups': CheckboxSelectMultiple,
            'start_date': SelectDateTime,
            'end_date': SelectDateTime,
            'start_candidature': SelectDateTime,
            'end_candidature': SelectDateTime,
        })
    template_name = 'core/page_prop.jinja'

    def get_success_url(self, **kwargs):
        return reverse_lazy('election:detail', kwargs={'election_id': self.object.id})


class ElectionListCreateView(CanCreateMixin, CreateView):
    model = ElectionList
    form_class = modelform_factory(ElectionList,
        fields=['title', 'election'])
    template_name = 'core/page_prop.jinja'

    def form_valid(self, form):
        """
            Verify that the user can vote on this election
        """
        obj = form.instance
        res = super(CreateView, self).form_valid
        if obj.election:
            for grp in obj.election.candidature_groups.all():
                if self.request.user.is_in_group(grp):
                    return res(form)
            for grp in obj.election.edit_groups.all():
                if self.request.user.is_in_group(grp):
                    return res(form)
        raise PermissionDenied

    def get_success_url(self, **kwargs):
        return reverse_lazy('election:detail', kwargs={'election_id': self.object.election.id})
