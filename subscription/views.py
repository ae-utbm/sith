from django.shortcuts import render
from django.views.generic.edit import UpdateView, CreateView
from django.views.generic.base import View
from django.core.exceptions import PermissionDenied
from django import forms
from django.forms import Select
from django.conf import settings

from subscription.models import Subscriber, Subscription
from core.views import CanEditMixin, CanEditPropMixin, CanViewMixin
from core.models import User

def get_subscriber(user):
    s = Subscriber.objects.filter(pk=user.pk).first()
    return s

class SubscriptionForm(forms.ModelForm):
    class Meta:
        model = Subscription
        fields = ['member', 'subscription_type', 'payment_method']

class NewSubscription(CanEditMixin, CreateView): # TODO: this must be able to create a new user if needed
    template_name = 'subscription/subscription.jinja'
    form_class = SubscriptionForm

    def get_initial(self):
        if 'member' in self.request.GET.keys():
            return {'member': self.request.GET['member']}
        return {}

    def form_valid(self, form):
        form.instance.subscription_start = Subscription.compute_start()
        form.instance.subscription_end = Subscription.compute_end(
                duration=settings.SITH_SUBSCRIPTIONS[form.instance.subscription_type]['duration'],
                start=form.instance.subscription_start
                )
        return super(NewSubscription, self).form_valid(form)
