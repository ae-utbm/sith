from django.shortcuts import render
from django.views.generic.edit import UpdateView, CreateView
from django import forms
from django.forms import Select
from django.conf import settings

from subscription.models import Member, Subscription
from core.views import CanEditMixin, CanEditPropMixin, CanViewMixin

class SubscriptionForm(forms.ModelForm):
    class Meta:
        model = Subscription
        fields = ['subscription_type', 'payment_method']
        #widgets = {
        #    'subscription_type': Select(choices={(k.lower(), k+" - "+str(v['price'])+"€"+str(Subscription.compute_end(2))) for k,v in settings.AE_SUBSCRIPTIONS.items()}),
        #}


class NewSubscription(CanEditMixin, CreateView):
    template_name = 'subscription/subscription.html'
    form_class = SubscriptionForm
