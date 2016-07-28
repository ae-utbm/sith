from datetime import datetime, timedelta
from collections import OrderedDict

from django.shortcuts import render
from django.views.generic import ListView, DetailView, RedirectView, TemplateView
from django.views.generic.edit import UpdateView, CreateView, DeleteView, ProcessFormView, FormMixin
from django.forms.models import modelform_factory
from django.forms import CheckboxSelectMultiple
from django.utils.translation import ugettext as _
from django.utils.timezone import make_aware
from django.utils import dateparse
from django.conf import settings

from core.models import Page
from core.views import CanViewMixin, CanEditMixin, CanEditPropMixin, CanCreateMixin
from launderette.models import Launderette, Token, Machine, Slot
from subscription.views import get_subscriber

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
    template_name = 'launderette/launderette_book_choose.jinja'

class LaunderetteBookView(DetailView):
    """Display the launderette schedule"""
    model = Launderette
    pk_url_kwarg = "launderette_id"
    template_name = 'launderette/launderette_book.jinja'

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if 'slot' in request.POST.keys() and request.user.is_authenticated():
            subscriber = get_subscriber(request.user)
            if subscriber.is_subscribed():
                date = dateparse.parse_datetime(request.POST['slot'])
                for m in self.object.machines.filter(is_working=True).all():
                    slot = Slot.objects.filter(start_date=date, machine=m).first()
                    print(slot)
                    if slot is None:
                        Slot(user=subscriber, start_date=date, machine=m, type="WASHING").save()
                        print("Saved")
                        break
        return super(LaunderetteBookView, self).get(request, *args, **kwargs)

    @staticmethod
    def date_iterator(startDate, endDate, delta=timedelta(days=1)):
        currentDate = startDate
        while currentDate < endDate:
            yield currentDate
            currentDate += delta

    def get_context_data(self, **kwargs):
        """ Add page to the context """
        kwargs = super(LaunderetteBookView, self).get_context_data(**kwargs)
        kwargs['planning'] = OrderedDict()
        start_date = make_aware(datetime.now().replace(hour=0, minute=0, second=0, microsecond=0))
        for date in LaunderetteBookView.date_iterator(start_date, start_date+timedelta(days=6), timedelta(days=1)):
            kwargs['planning'][date] = []
            for h in LaunderetteBookView.date_iterator(date, date+timedelta(days=1), timedelta(hours=1)):
                free = False
                for m in self.object.machines.filter(is_working=True).all():
                    s = Slot.objects.filter(start_date=h, machine=m).first()
                    if s is None:
                        free = True
                if free and make_aware(datetime.now()) < h:
                    kwargs['planning'][date].append(h)
                else:
                    kwargs['planning'][date].append(None)
                    print("Taken")
        return kwargs

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
