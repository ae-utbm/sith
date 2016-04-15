from django.shortcuts import render
from django.views.generic import ListView, DetailView, RedirectView
from django.views.generic.edit import UpdateView, CreateView, DeleteView, ProcessFormView, FormMixin
from django.forms.models import modelform_factory
from django.forms import CheckboxSelectMultiple
from django.core.urlresolvers import reverse_lazy
from django.contrib.auth.forms import AuthenticationForm
from django.utils import timezone
from django.conf import settings
from django import forms

from datetime import timedelta

from core.views import CanViewMixin, CanEditMixin, CanEditPropMixin
from subscription.models import Subscriber
from accounting.models import Customer
from counter.models import Counter

class GetUserForm(forms.Form):
    username = forms.CharField(label="Name", max_length=64, required=False)

class CounterMain(DetailView, FormMixin):
    """
    The public (barman) view
    """
    model = Counter
    template_name = 'counter/counter_main.jinja'
    pk_url_kwarg = "counter_id"
    form_class = GetUserForm

    def get_context_data(self, **kwargs):
        """
        Get the barman list for the template

        Also handle the timeout
        """
        kwargs = super(CounterMain, self).get_context_data(**kwargs)
        kwargs['login_form'] = AuthenticationForm()
        kwargs['form'] = self.get_form()
        print(kwargs)
        if str(self.object.id) in list(Counter.barmen_session.keys()):
            if (timezone.now() - Counter.barmen_session[str(self.object.id)]['time']) < timedelta(minutes=settings.SITH_BARMAN_TIMEOUT):
                kwargs['barmen'] = []
                for b in Counter.barmen_session[str(self.object.id)]['users']:
                    kwargs['barmen'].append(Subscriber.objects.filter(id=b).first())
                Counter.barmen_session[str(self.object.id)]['time'] = timezone.now()
            else:
                Counter.barmen_session[str(self.object.id)]['users'] = {}
        else:
            kwargs['barmen'] = []
        return kwargs

class CounterClick(DetailView, ProcessFormView, FormMixin):
    """
    The click view
    """
    model = Counter # TODO change that to a basket class
    template_name = 'counter/counter_click.jinja'
    pk_url_kwarg = "counter_id"
    form_class = GetUserForm

    def post(self, request, *args, **kwargs):
        # TODO: handle the loading of a user, to display the click view
        # TODO: Do the form and the template for the click view
        return super(CounterClick, self).post(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy('counter:click', args=self.args, kwargs=self.kwargs)

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


