from django.conf.urls import url, include

from com.views import *

urlpatterns = [
    url(r'^edit/alert$', AlertMsgEditView.as_view(), name='alert_edit'),
    url(r'^edit/info$', InfoMsgEditView.as_view(), name='info_edit'),
    url(r'^edit/index$', IndexEditView.as_view(), name='index_edit'),
]

