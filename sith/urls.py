"""sith URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf.urls import include, url
from django.contrib import admin
from django.conf.urls.static import static
from django.conf import settings
from django.views.i18n import javascript_catalog
from ajax_select import urls as ajax_select_urls

js_info_dict = {
    'packages': ('sith',),
}

handler403 = "core.views.forbidden"
handler404 = "core.views.not_found"

urlpatterns = [
    url(r'^', include('core.urls', namespace="core", app_name="core")),
    url(r'^rootplace/', include('rootplace.urls', namespace="rootplace", app_name="rootplace")),
    url(r'^subscription/', include('subscription.urls', namespace="subscription", app_name="subscription")),
    url(r'^club/', include('club.urls', namespace="club", app_name="club")),
    url(r'^counter/', include('counter.urls', namespace="counter", app_name="counter")),
    url(r'^accounting/', include('accounting.urls', namespace="accounting", app_name="accounting")),
    url(r'^eboutic/', include('eboutic.urls', namespace="eboutic", app_name="eboutic")),
    url(r'^launderette/', include('launderette.urls', namespace="launderette", app_name="launderette")),
    url(r'^api/v1/', include('api.urls', namespace="api", app_name="api")),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^ajax_select/', include(ajax_select_urls)),
    url(r'^i18n/', include('django.conf.urls.i18n')),
    url(r'^jsi18n/$', javascript_catalog, js_info_dict, name='javascript-catalog'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

