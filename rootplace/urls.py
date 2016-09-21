from django.conf.urls import url, include

from rootplace.views import *

urlpatterns = [
    url(r'^merge$', MergeUsersView.as_view(), name='merge'),
]



