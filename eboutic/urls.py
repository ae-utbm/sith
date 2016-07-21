from django.conf.urls import url, include

from eboutic.views import *

urlpatterns = [
    # Subscription views
    url(r'^$', EbouticMain.as_view(), name='main'),
    url(r'^command$', EbouticCommand.as_view(), name='command'),
    url(r'^pay$', EbouticPayWithSith.as_view(), name='pay_with_sith'),
    url(r'^et_autoanswer$', EtransactionAutoAnswer.as_view(), name='etransation_autoanswer'),
]



