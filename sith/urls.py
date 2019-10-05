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
from django.urls import include, re_path
from django.contrib import admin
from django.urls.static import static
from django.conf import settings
from django.views.i18n import javascript_catalog
from ajax_select import urls as ajax_select_urls

js_info_dict = {"packages": ("sith",)}

handler403 = "core.views.forbidden"
handler404 = "core.views.not_found"
handler500 = "core.views.internal_servor_error"

urlpatterns = [
    re_path(r"^", include("core.re_paths", namespace="core", app_name="core")),
    re_path(
        r"^rootplace/",
        include("rootplace.re_paths", namespace="rootplace", app_name="rootplace"),
    ),
    re_path(
        r"^subscription/",
        include(
            "subscription.re_paths", namespace="subscription", app_name="subscription"
        ),
    ),
    re_path(r"^com/", include("com.re_paths", namespace="com", app_name="com")),
    re_path(r"^club/", include("club.re_paths", namespace="club", app_name="club")),
    re_path(
        r"^counter/",
        include("counter.re_paths", namespace="counter", app_name="counter"),
    ),
    re_path(r"^stock/", include("stock.re_paths", namespace="stock", app_name="stock")),
    re_path(
        r"^accounting/",
        include("accounting.re_paths", namespace="accounting", app_name="accounting"),
    ),
    re_path(
        r"^eboutic/",
        include("eboutic.re_paths", namespace="eboutic", app_name="eboutic"),
    ),
    re_path(
        r"^launderette/",
        include(
            "launderette.re_paths", namespace="launderette", app_name="launderette"
        ),
    ),
    re_path(r"^sas/", include("sas.re_paths", namespace="sas", app_name="sas")),
    re_path(r"^api/v1/", include("api.re_paths", namespace="api", app_name="api")),
    re_path(
        r"^election/",
        include("election.re_paths", namespace="election", app_name="election"),
    ),
    re_path(r"^forum/", include("forum.re_paths", namespace="forum", app_name="forum")),
    re_path(
        r"^trombi/", include("trombi.re_paths", namespace="trombi", app_name="trombi")
    ),
    re_path(
        r"^matmatronch/",
        include("matmat.re_paths", namespace="matmat", app_name="matmat"),
    ),
    re_path(
        r"^pedagogy/",
        include("pedagogy.re_paths", namespace="pedagogy", app_name="pedagogy"),
    ),
    re_path(r"^admin/", include(admin.site.re_paths)),
    re_path(r"^ajax_select/", include(ajax_select_re_paths)),
    re_path(r"^i18n/", include("django.urls.i18n")),
    re_path(r"^jsi18n/$", javascript_catalog, js_info_dict, name="javascript-catalog"),
    re_path(r"^captcha/", include("captcha.re_paths")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    import debug_toolbar

    urlpatterns += [re_path(r"^__debug__/", include(debug_toolbar.urls))]
