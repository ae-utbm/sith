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
    url(r'^com/', include('com.urls', namespace="com", app_name="com")),
    url(r'^club/', include('club.urls', namespace="club", app_name="club")),
    url(r'^counter/', include('counter.urls', namespace="counter", app_name="counter")),
    url(r'^stock/', include('stock.urls', namespace="stock", app_name="stock")),
    url(r'^accounting/', include('accounting.urls', namespace="accounting", app_name="accounting")),
    url(r'^eboutic/', include('eboutic.urls', namespace="eboutic", app_name="eboutic")),
    url(r'^launderette/', include('launderette.urls', namespace="launderette", app_name="launderette")),
    url(r'^sas/', include('sas.urls', namespace="sas", app_name="sas")),
    url(r'^api/v1/', include('api.urls', namespace="api", app_name="api")),
    url(r'^election/', include('election.urls', namespace="election", app_name="election")),
    url(r'^forum/', include('forum.urls', namespace="forum", app_name="forum")),
    url(r'^trombi/', include('trombi.urls', namespace="trombi", app_name="trombi")),
    url(r'^matmatronch/', include('matmat.urls', namespace="matmat", app_name="matmat")),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^ajax_select/', include(ajax_select_urls)),
    url(r'^i18n/', include('django.conf.urls.i18n')),
    url(r'^jsi18n/$', javascript_catalog, js_info_dict, name='javascript-catalog'),
    url(r'^captcha/', include('captcha.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    import debug_toolbar
    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]
