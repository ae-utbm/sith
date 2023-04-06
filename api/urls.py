# -*- coding:utf-8 -*-
#
# Copyright 2023 © AE UTBM
# ae@utbm.fr / ae.info@utbm.fr
# All contributors are listed in the CONTRIBUTORS file.
#
# This file is part of the website of the UTBM Student Association (AE UTBM),
# https://ae.utbm.fr.
#
# You can find the whole source code at https://github.com/ae-utbm/sith3
#
# LICENSED UNDER THE GNU GENERAL PUBLIC LICENSE VERSION 3 (GPLv3)
# SEE : https://raw.githubusercontent.com/ae-utbm/sith3/master/LICENSE
# OR WITHIN THE LOCAL FILE "LICENSE"
#
# PREVIOUSLY LICENSED UNDER THE MIT LICENSE,
# SEE : https://raw.githubusercontent.com/ae-utbm/sith3/master/LICENSE.old
# OR WITHIN THE LOCAL FILE "LICENSE.old"
#

from django.urls import include, path, re_path
from rest_framework import routers

from api.views import *

# Router config
router = routers.DefaultRouter()
router.register(r"counter", CounterViewSet, basename="api_counter")
router.register(r"user", UserViewSet, basename="api_user")
router.register(r"club", ClubViewSet, basename="api_club")
router.register(r"group", GroupViewSet, basename="api_group")

# Launderette
router.register(
    r"launderette/place", LaunderettePlaceViewSet, basename="api_launderette_place"
)
router.register(
    r"launderette/machine",
    LaunderetteMachineViewSet,
    basename="api_launderette_machine",
)
router.register(
    r"launderette/token", LaunderetteTokenViewSet, basename="api_launderette_token"
)

urlpatterns = [
    # API
    re_path(r"^", include(router.urls)),
    re_path(r"^login/", include("rest_framework.urls", namespace="rest_framework")),
    re_path(r"^markdown$", RenderMarkdown, name="api_markdown"),
    re_path(r"^mailings$", FetchMailingLists, name="mailings_fetch"),
    re_path(r"^uv$", uv_endpoint, name="uv_endpoint"),
    path("sas/<int:user>", all_pictures_of_user_endpoint, name="all_pictures_of_user"),
]
