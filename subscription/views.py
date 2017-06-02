# -*- coding:utf-8 -*
#
# Copyright 2016,2017
# - Skia <skia@libskia.so>
#
# Ce fichier fait partie du site de l'Association des Étudiants de l'UTBM,
# http://ae.utbm.fr.
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License a published by the Free Software
# Foundation; either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Sofware Foundation, Inc., 59 Temple
# Place - Suite 330, Boston, MA 02111-1307, USA.
#
#

from django.shortcuts import render
from django.views.generic.edit import UpdateView, CreateView
from django.views.generic.base import View
from django.views.generic import TemplateView
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError
from django import forms
from django.forms import Select
from django.conf import settings

from ajax_select.fields import AutoCompleteSelectField
import random

from subscription.models import Subscription
from core.views import CanEditMixin, CanEditPropMixin, CanViewMixin
from core.models import User

class SubscriptionForm(forms.ModelForm):
    class Meta:
        model = Subscription
        fields = ['member', 'subscription_type', 'payment_method', 'location']
    member = AutoCompleteSelectField('users', required=False, help_text=None)

    def __init__(self, *args, **kwargs):
        super(SubscriptionForm, self).__init__(*args, **kwargs)
        # Add fields to allow basic user creation
        self.fields['last_name'] = forms.CharField(max_length=User._meta.get_field('last_name').max_length)
        self.fields['first_name'] = forms.CharField(max_length=User._meta.get_field('first_name').max_length)
        self.fields['email'] = forms.EmailField()
        self.fields.move_to_end('subscription_type')
        self.fields.move_to_end('payment_method')
        self.fields.move_to_end('location')

    def clean_member(self):
        subscriber = self.cleaned_data.get("member")
        if subscriber:
            subscriber = User.objects.filter(id=subscriber.id).first()
        return subscriber

    def clean(self):
        cleaned_data = super(SubscriptionForm, self).clean()
        if (cleaned_data.get("member") is None
                and "last_name" not in self.errors.as_data()
                and "first_name" not in self.errors.as_data()
                and "email" not in self.errors.as_data()):
            self.errors.pop("member", None)
            if self.errors:
                return cleaned_data
            if User.objects.filter(email=cleaned_data.get("email")).first() is not None:
                self.add_error("email", ValidationError(_("A user with that email address already exists")))
            else:
                u = User(last_name = self.cleaned_data.get("last_name"),
                        first_name = self.cleaned_data.get("first_name"),
                        email = self.cleaned_data.get("email"))
                u.generate_username()
                u.set_password(str(random.randrange(1000000, 10000000)))
                u.save()
                cleaned_data["member"] = u
        elif cleaned_data.get("member") is not None:
            self.errors.pop("last_name", None)
            self.errors.pop("first_name", None)
            self.errors.pop("email", None)
        if cleaned_data.get("member") is None:
            # This should be handled here, but it is done in the Subscription model's clean method
            # TODO investigate why!
            raise ValidationError(_("You must either choose an existing user or create a new one properly"))
        return cleaned_data

class NewSubscription(CreateView):
    template_name = 'subscription/subscription.jinja'
    form_class = SubscriptionForm

    def dispatch(self, request, *arg, **kwargs):
        res = super(NewSubscription, self).dispatch(request, *arg, **kwargs)
        if request.user.is_in_group(settings.SITH_MAIN_BOARD_GROUP):
            return res
        raise PermissionDenied

    def get_initial(self):
        if 'member' in self.request.GET.keys():
            return {'member': self.request.GET['member'], 'subscription_type': 'deux-semestres'}
        return {'subscription_type': 'deux-semestres'}

    def form_valid(self, form):
        form.instance.subscription_start = Subscription.compute_start(
                duration=settings.SITH_SUBSCRIPTIONS[form.instance.subscription_type]['duration'])
        form.instance.subscription_end = Subscription.compute_end(
                duration=settings.SITH_SUBSCRIPTIONS[form.instance.subscription_type]['duration'],
                start=form.instance.subscription_start
                )
        return super(NewSubscription, self).form_valid(form)


class SubscriptionsStatsView(TemplateView):
    template_name = "subscription/stats.jinja"

    def dispatch(self, request, *arg, **kwargs):
        res = super(SubscriptionsStatsView, self).dispatch(request, *arg, **kwargs)
        if request.user.is_root or request.user.is_board_member:
            return res
        raise PermissionDenied

    def get_context_data(self, **kwargs):
        from subscription.models import Subscription
        import datetime
        kwargs = super(SubscriptionsStatsView, self).get_context_data(**kwargs)
        kwargs['subscriptions_total'] = Subscription.objects.filter(subscription_end__gte=datetime.datetime.today())
        kwargs['subscriptions_types'] = settings.SITH_SUBSCRIPTIONS
        kwargs['payment_types'] = settings.SITH_COUNTER_PAYMENT_METHOD
        kwargs['locations'] = settings.SITH_SUBSCRIPTION_LOCATIONS
        return kwargs
