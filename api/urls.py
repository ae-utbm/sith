from django.conf.urls import url, include

from api.views import *
from rest_framework import routers

# Router config
router = routers.DefaultRouter()

urlpatterns = [

    # API
    url(r'^', include(router.urls)),
    url(r'^login/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^markdown$', RenderMarkdown, name='api_markdown'),

]