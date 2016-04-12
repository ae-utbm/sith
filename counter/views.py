from django.shortcuts import render
from django.views.generic import ListView, DetailView, RedirectView
from django.views.generic.edit import UpdateView, CreateView, DeleteView
from django.forms.models import modelform_factory
from django.forms import CheckboxSelectMultiple
from django.core.urlresolvers import reverse_lazy
from django.contrib.auth.forms import AuthenticationForm
from django.utils import timezone
from django.conf import settings

from datetime import timedelta

from core.views import CanViewMixin, CanEditMixin, CanEditPropMixin
from subscription.models import Subscriber
from counter.models import Counter

class CounterDetail(DetailView):
    """
    The public (barman) view
    """
    model = Counter
    template_name = 'counter/counter_detail.jinja'
    pk_url_kwarg = "counter_id"

    def get_context_data(self, **kwargs):
        """
        Get the barman list for the template

        Also handle the timeout
        """
        context = super(CounterDetail, self).get_context_data(**kwargs)
        context['login_form'] = AuthenticationForm()
        print(self.object.id)
        print(list(Counter.barmen_session.keys()))
        if str(self.object.id) in list(Counter.barmen_session.keys()):
            if (timezone.now() - Counter.barmen_session[str(self.object.id)]['time']) < timedelta(minutes=settings.SITH_BARMAN_TIMEOUT):
                context['barmen'] = []
                for b in Counter.barmen_session[str(self.object.id)]['users']:
                    context['barmen'].append(Subscriber.objects.filter(id=b).first())
                Counter.barmen_session[str(self.object.id)]['time'] = timezone.now()
            else:
                Counter.barmen_session[str(self.object.id)]['users'] = {}
        else:
            context['barmen'] = []
        return context

class CounterLogin(RedirectView):
    """
    Handle the login of a barman

    Logged barmen are stored in the class-wide variable 'barmen_session', in the Counter model
    """
    permanent = False
    def post(self, request, *args, **kwargs):
        """
        Register the logged user as barman for this counter
        """
        self.counter_id = kwargs['counter_id']
# TODO: make some checks on the counter type
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = Subscriber.objects.filter(username=form.cleaned_data['username']).first()
            if self.counter_id not in Counter.barmen_session.keys():
                Counter.barmen_session[self.counter_id] = {'users': {user.id}, 'time': timezone.now()}
            else:
                Counter.barmen_session[self.counter_id]['users'].add(user.id)
        else:
            print("Error logging the barman") # TODO handle that nicely
        return super(CounterLogin, self).post(request, *args, **kwargs)

    def get_redirect_url(self, *args, **kwargs):
        return reverse_lazy('counter:details', args=args, kwargs=kwargs)

class CounterLogout(RedirectView):
    permanent = False
    def post(self, request, *args, **kwargs):
        """
        Unregister the user from the barman
        """
        self.counter_id = kwargs['counter_id']
        Counter.barmen_session[str(self.counter_id)]['users'].remove(int(request.POST['user_id']))
        return super(CounterLogout, self).post(request, *args, **kwargs)

    def get_redirect_url(self, *args, **kwargs):
        return reverse_lazy('counter:details', args=args, kwargs=kwargs)

class CounterListView(CanViewMixin, ListView):
    """
    A list view for the admins
    """
    model = Counter
    template_name = 'counter/counter_list.jinja'

class CounterEditView(CanEditMixin, UpdateView):
    """
    Edit a counter's main informations (for the counter's admin)
    """
    model = Counter
    form_class = modelform_factory(Counter, fields=['name', 'club', 'type', 'products'],
            widgets={'products':CheckboxSelectMultiple})
    pk_url_kwarg = "counter_id"
    template_name = 'counter/counter_edit.jinja'

class CounterCreateView(CanEditMixin, CreateView):
    """
    Create a counter (for the admins)
    """
    model = Counter
    form_class = modelform_factory(Counter, fields=['name', 'club', 'type', 'products'],
            widgets={'products':CheckboxSelectMultiple})
    template_name = 'counter/counter_edit.jinja'

class CounterDeleteView(CanEditMixin, DeleteView):
    """
    Delete a counter (for the admins)
    """
    model = Counter
    pk_url_kwarg = "counter_id"
    template_name = 'core/delete_confirm.jinja'
    success_url = reverse_lazy('counter:admin_list')


