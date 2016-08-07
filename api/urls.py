from django.conf.urls import url, include

from api.views import *
from rest_framework import routers

# Router config
router = routers.DefaultRouter()
router.register(r'counter', CounterViewSet, base_name='api_counter')
router.register(r'user', UserViewSet, base_name='api_user')
router.register(r'club', ClubViewSet, base_name='api_club')
router.register(r'group', GroupViewSet, base_name='api_group')

urlpatterns = [

    # API
    url(r'^', include(router.urls)),
    url(r'^login/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^markdown$', RenderMarkdown, name='api_markdown'),

]
