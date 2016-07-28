from django.shortcuts import render
from django.views.generic import ListView, DetailView, RedirectView, TemplateView
from django.views.generic.edit import UpdateView, CreateView, DeleteView, ProcessFormView, FormMixin
from django.forms.models import modelform_factory
from django.forms import CheckboxSelectMultiple
from django.utils.translation import ugettext as _
from django.conf import settings

from core.models import Page
from core.views import CanViewMixin, CanEditMixin, CanEditPropMixin, CanCreateMixin
from launderette.models import Launderette, Token, Machine, Slot

# For users

class LaunderetteMainView(TemplateView):
    """Main presentation view"""
    template_name = 'launderette/launderette_main.jinja'

    def get_context_data(self, **kwargs):
        """ Add page to the context """
        kwargs = super(LaunderetteMainView, self).get_context_data(**kwargs)
        kwargs['page'] = Page.objects.filter(name='launderette').first()
        return kwargs

class LaunderetteBookMainView(CanViewMixin, ListView):
    """Choose which launderette to book"""
    model = Launderette
    template_name = 'launderette/launderette_book.jinja'

class LaunderetteBookView(TemplateView):
    """Display the launderette schedule"""
    model = Launderette
    pk_url_kwarg = "launderette_id"
    template_name = 'launderette/launderette_book.jinja'


# For admins

class LaunderetteListView(CanViewMixin, ListView):
    """Choose which launderette to administer"""
    model = Launderette
    template_name = 'launderette/launderette_list.jinja'

class LaunderetteDetailView(CanViewMixin, DetailView):
    """The admin page of the launderette"""
    model = Launderette
    pk_url_kwarg = "launderette_id"
    template_name = 'launderette/launderette_detail.jinja'

class LaunderetteEditView(CanViewMixin, UpdateView):
    """Edit a launderette"""
    model = Launderette
    pk_url_kwarg = "launderette_id"
    form_class = modelform_factory(Launderette, fields=['name', 'sellers'],
            widgets={'sellers':CheckboxSelectMultiple})
    template_name = 'core/edit.jinja'

class LaunderetteCreateView(CanCreateMixin, CreateView):
    """Create a new launderette"""
    model = Launderette
    fields = ['name', 'sellers']
    template_name = 'core/create.jinja'
