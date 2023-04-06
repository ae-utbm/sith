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

from django.urls import path

from club.views import MailingDeleteView
from com.views import *

urlpatterns = [
    path("sith/edit/alert/", AlertMsgEditView.as_view(), name="alert_edit"),
    path("sith/edit/info/", InfoMsgEditView.as_view(), name="info_edit"),
    path(
        "sith/edit/weekmail_destinations/",
        WeekmailDestinationEditView.as_view(),
        name="weekmail_destinations",
    ),
    path("weekmail/", WeekmailEditView.as_view(), name="weekmail"),
    path("weekmail/preview/", WeekmailPreviewView.as_view(), name="weekmail_preview"),
    path(
        "weekmail/new_article/",
        WeekmailArticleCreateView.as_view(),
        name="weekmail_article",
    ),
    path(
        "weekmail/article/<int:article_id>/delete/",
        WeekmailArticleDeleteView.as_view(),
        name="weekmail_article_delete",
    ),
    path(
        "weekmail/article/<int:article_id>/edit/",
        WeekmailArticleEditView.as_view(),
        name="weekmail_article_edit",
    ),
    path("news/", NewsListView.as_view(), name="news_list"),
    path("news/admin/", NewsAdminListView.as_view(), name="news_admin_list"),
    path("news/create/", NewsCreateView.as_view(), name="news_new"),
    path(
        "news/<int:news_id>/delete/",
        NewsDeleteView.as_view(),
        name="news_delete",
    ),
    path(
        "news/<int:news_id>/moderate/",
        NewsModerateView.as_view(),
        name="news_moderate",
    ),
    path("news/<int:news_id>/edit/", NewsEditView.as_view(), name="news_edit"),
    path("news/<int:news_id>/", NewsDetailView.as_view(), name="news_detail"),
    path("mailings/", MailingListAdminView.as_view(), name="mailing_admin"),
    path(
        "mailings/<int:mailing_id>/moderate/",
        MailingModerateView.as_view(),
        name="mailing_moderate",
    ),
    path(
        "mailings/<int:mailing_id>/delete/",
        MailingDeleteView.as_view(redirect_page="com:mailing_admin"),
        name="mailing_delete",
    ),
    path("poster/", PosterListView.as_view(), name="poster_list"),
    path("poster/create/", PosterCreateView.as_view(), name="poster_create"),
    path(
        "poster/<int:poster_id>/edit/",
        PosterEditView.as_view(),
        name="poster_edit",
    ),
    path(
        "poster/<int:poster_id>/delete/",
        PosterDeleteView.as_view(),
        name="poster_delete",
    ),
    path(
        "poster/moderate/",
        PosterModerateListView.as_view(),
        name="poster_moderate_list",
    ),
    path(
        "poster/<int:object_id>/moderate/",
        PosterModerateView.as_view(),
        name="poster_moderate",
    ),
    path("screen/", ScreenListView.as_view(), name="screen_list"),
    path("screen/create/", ScreenCreateView.as_view(), name="screen_create"),
    path(
        "screen/<int:screen_id>/slideshow/",
        ScreenSlideshowView.as_view(),
        name="screen_slideshow",
    ),
    path(
        "screen/<int:screen_id>/edit/",
        ScreenEditView.as_view(),
        name="screen_edit",
    ),
    path(
        "screen/<int:screen_id>/delete/",
        ScreenDeleteView.as_view(),
        name="screen_delete",
    ),
]
