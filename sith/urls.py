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
from django.urls import include, path
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.views.i18n import JavaScriptCatalog
from ajax_select import urls as ajax_select_urls

import core.urls

js_info_dict = {"packages": ("sith",)}

handler403 = "core.views.forbidden"
handler404 = "core.views.not_found"
handler500 = "core.views.internal_servor_error"

urlpatterns = [
    path("", include(("core.urls", "core"), namespace="core")),
    path("rootplace/", include(("rootplace.urls", "rootplace"), namespace="rootplace")),
    path(
        "subscription/",
        include(("subscription.urls", "subscription"), namespace="subscription"),
    ),
    path("com/", include(("com.urls", "com"), namespace="com")),
    path("club/", include(("club.urls", "club"), namespace="club")),
    path("counter/", include(("counter.urls", "counter"), namespace="counter")),
    path("stock/", include(("stock.urls", "stock"), namespace="stock")),
    path(
        "accounting/",
        include(("accounting.urls", "accounting"), namespace="accounting"),
    ),
    path("eboutic/", include(("eboutic.urls", "eboutic"), namespace="eboutic")),
    path(
        "launderette/",
        include(("launderette.urls", "launderette"), namespace="launderette"),
    ),
    path("sas/", include(("sas.urls", "sas"), namespace="sas")),
    path("api/v1/", include(("api.urls", "api"), namespace="api")),
    path("election/", include(("election.urls", "election"), namespace="election")),
    path("forum/", include(("forum.urls", "forum"), namespace="forum")),
    path("trombi/", include(("trombi.urls", "trombi"), namespace="trombi")),
    path("matmatronch/", include(("matmat.urls", "matmat"), namespace="matmat")),
    path("pedagogy/", include(("pedagogy.urls", "pedagogy"), namespace="pedagogy")),
    path("admin/", admin.site.urls),
    path("ajax_select/", include(ajax_select_urls)),
    path("i18n/", include("django.conf.urls.i18n")),
    path("jsi18n/$", JavaScriptCatalog.as_view(), name="javascript-catalog"),
    path("captcha/", include("captcha.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    import debug_toolbar

    urlpatterns += [path("__debug__/", include(debug_toolbar.urls))]
