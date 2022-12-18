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
