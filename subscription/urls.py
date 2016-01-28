from django.conf.urls import url, include

from subscription.views import *

urlpatterns = [
    # Subscription views
    url(r'^subscription/(?P<user_id>[0-9]+)/$', NewSubscription.as_view(), name='subscription'),
]



