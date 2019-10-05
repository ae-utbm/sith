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

from django.urls import re_path

from com.views import *
from club.views import MailingDeleteView

urlpatterns = [
    re_path(r"^sith/edit/alert$", AlertMsgEditView.as_view(), name="alert_edit"),
    re_path(r"^sith/edit/info$", InfoMsgEditView.as_view(), name="info_edit"),
    re_path(
        r"^sith/edit/weekmail_destinations$",
        WeekmailDestinationEditView.as_view(),
        name="weekmail_destinations",
    ),
    re_path(r"^weekmail$", WeekmailEditView.as_view(), name="weekmail"),
    re_path(
        r"^weekmail/preview$", WeekmailPreviewView.as_view(), name="weekmail_preview"
    ),
    re_path(
        r"^weekmail/new_article$",
        WeekmailArticleCreateView.as_view(),
        name="weekmail_article",
    ),
    re_path(
        r"^weekmail/article/(?P<article_id>[0-9]+)/delete$",
        WeekmailArticleDeleteView.as_view(),
        name="weekmail_article_delete",
    ),
    re_path(
        r"^weekmail/article/(?P<article_id>[0-9]+)/edit$",
        WeekmailArticleEditView.as_view(),
        name="weekmail_article_edit",
    ),
    re_path(r"^news$", NewsListView.as_view(), name="news_list"),
    re_path(r"^news/admin$", NewsAdminListView.as_view(), name="news_admin_list"),
    re_path(r"^news/create$", NewsCreateView.as_view(), name="news_new"),
    re_path(
        r"^news/(?P<news_id>[0-9]+)/delete$",
        NewsDeleteView.as_view(),
        name="news_delete",
    ),
    re_path(
        r"^news/(?P<news_id>[0-9]+)/moderate$",
        NewsModerateView.as_view(),
        name="news_moderate",
    ),
    re_path(
        r"^news/(?P<news_id>[0-9]+)/edit$", NewsEditView.as_view(), name="news_edit"
    ),
    re_path(
        r"^news/(?P<news_id>[0-9]+)$", NewsDetailView.as_view(), name="news_detail"
    ),
    re_path(r"^mailings$", MailingListAdminView.as_view(), name="mailing_admin"),
    re_path(
        r"^mailings/(?P<mailing_id>[0-9]+)/moderate$",
        MailingModerateView.as_view(),
        name="mailing_moderate",
    ),
    re_path(
        r"^mailings/(?P<mailing_id>[0-9]+)/delete$",
        MailingDeleteView.as_view(redirect_page="com:mailing_admin"),
        name="mailing_delete",
    ),
    re_path(r"^poster$", PosterListView.as_view(), name="poster_list"),
    re_path(r"^poster/create$", PosterCreateView.as_view(), name="poster_create"),
    re_path(
        r"^poster/(?P<poster_id>[0-9]+)/edit$",
        PosterEditView.as_view(),
        name="poster_edit",
    ),
    re_path(
        r"^poster/(?P<poster_id>[0-9]+)/delete$",
        PosterDeleteView.as_view(),
        name="poster_delete",
    ),
    re_path(
        r"^poster/moderate$",
        PosterModerateListView.as_view(),
        name="poster_moderate_list",
    ),
    re_path(
        r"^poster/(?P<object_id>[0-9]+)/moderate$",
        PosterModerateView.as_view(),
        name="poster_moderate",
    ),
    re_path(r"^screen$", ScreenListView.as_view(), name="screen_list"),
    re_path(r"^screen/create$", ScreenCreateView.as_view(), name="screen_create"),
    re_path(
        r"^screen/(?P<screen_id>[0-9]+)/slideshow$",
        ScreenSlideshowView.as_view(),
        name="screen_slideshow",
    ),
    re_path(
        r"^screen/(?P<screen_id>[0-9]+)/edit$",
        ScreenEditView.as_view(),
        name="screen_edit",
    ),
    re_path(
        r"^screen/(?P<screen_id>[0-9]+)/delete$",
        ScreenDeleteView.as_view(),
        name="screen_delete",
    ),
]
