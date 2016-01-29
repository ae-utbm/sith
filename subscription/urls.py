from django.conf.urls import url, include

from subscription.views import *

urlpatterns = [
    # Subscription views
    url(r'^$', NewSubscription.as_view(), name='subscription'),
]



