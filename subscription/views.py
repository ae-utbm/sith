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

class SubscriberMixin(View):
    def dispatch(self, request, *arg, **kwargs):
        res = super(SubscriberMixin, self).dispatch(request, *arg, **kwargs)
        subscriber = Subscriber.objects.filter(pk=request.user.pk).first()
        if subscriber is not None and subscriber.is_subscribed():
            return ret
        raise PermissionDenied

class SubscriptionForm(forms.ModelForm):
    class Meta:
        model = Subscription
        fields = ['member', 'subscription_type', 'payment_method']
        #widgets = {
        #    'subscription_type': Select(choices={(k.lower(), k+" - "+str(v['price'])+"€"+str(Subscription.compute_end(2))) for k,v in settings.AE_SUBSCRIPTIONS.items()}),
        #}


class NewSubscription(CanEditMixin, CreateView):
    template_name = 'subscription/subscription.html'
    form_class = SubscriptionForm
