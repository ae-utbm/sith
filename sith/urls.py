#
# Copyright 2023 © AE UTBM
# ae@utbm.fr / ae.info@utbm.fr
#
# This file is part of the website of the UTBM Student Association (AE UTBM),
# https://ae.utbm.fr.
#
# You can find the source code of the website at https://github.com/ae-utbm/sith
#
# LICENSED UNDER THE GNU GENERAL PUBLIC LICENSE VERSION 3 (GPLv3)
# SEE : https://raw.githubusercontent.com/ae-utbm/sith/master/LICENSE
# OR WITHIN THE LOCAL FILE "LICENSE"
#
#

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import Http404
from django.urls import include, path
from django.views.i18n import JavaScriptCatalog
from ninja_extra import NinjaExtraAPI

js_info_dict = {"packages": ("sith",)}

handler403 = "core.views.forbidden"
handler404 = "core.views.not_found"
handler500 = "core.views.internal_servor_error"

api = NinjaExtraAPI(version="0.2.0", urls_namespace="api", csrf=True)
api.auto_discover_controllers()

urlpatterns = [
    path("", include(("core.urls", "core"), namespace="core")),
    path("api/", api.urls),
    path("rootplace/", include(("rootplace.urls", "rootplace"), namespace="rootplace")),
    path(
        "subscription/",
        include(("subscription.urls", "subscription"), namespace="subscription"),
    ),
    path("com/", include(("com.urls", "com"), namespace="com")),
    path("club/", include(("club.urls", "club"), namespace="club")),
    path("counter/", include(("counter.urls", "counter"), namespace="counter")),
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
    path("election/", include(("election.urls", "election"), namespace="election")),
    path("forum/", include(("forum.urls", "forum"), namespace="forum")),
    path("galaxy/", include(("galaxy.urls", "galaxy"), namespace="galaxy")),
    path("trombi/", include(("trombi.urls", "trombi"), namespace="trombi")),
    path("matmatronch/", include(("matmat.urls", "matmat"), namespace="matmat")),
    path("pedagogy/", include(("pedagogy.urls", "pedagogy"), namespace="pedagogy")),
    path("admin/", admin.site.urls),
    path("i18n/", include("django.conf.urls.i18n")),
    path("jsi18n/", JavaScriptCatalog.as_view(), name="javascript-catalog"),
    path("captcha/", include("captcha.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    import debug_toolbar

    urlpatterns += [path("__debug__/", include(debug_toolbar.urls))]


def sentry_debug(request):
    """Sentry debug endpoint

    This function always crash and allows us to test
    the sentry configuration and the modal popup
    displayed to users on production

    The error will be displayed on Sentry
    inside the "development" environment

    NOTE : you need to specify the SENTRY_DSN setting in .env
    """
    if settings.SENTRY_ENV != "development" or not settings.SENTRY_DSN:
        raise Http404
    _division_by_zero = 1 / 0


urlpatterns += [path("sentry-debug/", sentry_debug, name="sentry-debug")]
