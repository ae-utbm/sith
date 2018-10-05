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

from django.conf.urls import url

from com.views import *
from club.views import MailingDeleteView

urlpatterns = [
    url(r"^sith/edit/alert$", AlertMsgEditView.as_view(), name="alert_edit"),
    url(r"^sith/edit/info$", InfoMsgEditView.as_view(), name="info_edit"),
    url(r"^sith/edit/index$", IndexEditView.as_view(), name="index_edit"),
    url(
        r"^sith/edit/weekmail_destinations$",
        WeekmailDestinationEditView.as_view(),
        name="weekmail_destinations",
    ),
    url(r"^weekmail$", WeekmailEditView.as_view(), name="weekmail"),
    url(r"^weekmail/preview$", WeekmailPreviewView.as_view(), name="weekmail_preview"),
    url(
        r"^weekmail/new_article$",
        WeekmailArticleCreateView.as_view(),
        name="weekmail_article",
    ),
    url(
        r"^weekmail/article/(?P<article_id>[0-9]+)/delete$",
        WeekmailArticleDeleteView.as_view(),
        name="weekmail_article_delete",
    ),
    url(
        r"^weekmail/article/(?P<article_id>[0-9]+)/edit$",
        WeekmailArticleEditView.as_view(),
        name="weekmail_article_edit",
    ),
    url(r"^news$", NewsListView.as_view(), name="news_list"),
    url(r"^news/admin$", NewsAdminListView.as_view(), name="news_admin_list"),
    url(r"^news/create$", NewsCreateView.as_view(), name="news_new"),
    url(
        r"^news/(?P<news_id>[0-9]+)/delete$",
        NewsDeleteView.as_view(),
        name="news_delete",
    ),
    url(
        r"^news/(?P<news_id>[0-9]+)/moderate$",
        NewsModerateView.as_view(),
        name="news_moderate",
    ),
    url(r"^news/(?P<news_id>[0-9]+)/edit$", NewsEditView.as_view(), name="news_edit"),
    url(r"^news/(?P<news_id>[0-9]+)$", NewsDetailView.as_view(), name="news_detail"),
    url(r"^mailings$", MailingListAdminView.as_view(), name="mailing_admin"),
    url(
        r"^mailings/(?P<mailing_id>[0-9]+)/moderate$",
        MailingModerateView.as_view(),
        name="mailing_moderate",
    ),
    url(
        r"^mailings/(?P<mailing_id>[0-9]+)/delete$",
        MailingDeleteView.as_view(redirect_page="com:mailing_admin"),
        name="mailing_delete",
    ),
    url(r"^poster$", PosterListView.as_view(), name="poster_list"),
    url(r"^poster/create$", PosterCreateView.as_view(), name="poster_create"),
    url(
        r"^poster/(?P<poster_id>[0-9]+)/edit$",
        PosterEditView.as_view(),
        name="poster_edit",
    ),
    url(
        r"^poster/(?P<poster_id>[0-9]+)/delete$",
        PosterDeleteView.as_view(),
        name="poster_delete",
    ),
    url(
        r"^poster/moderate$",
        PosterModerateListView.as_view(),
        name="poster_moderate_list",
    ),
    url(
        r"^poster/(?P<object_id>[0-9]+)/moderate$",
        PosterModerateView.as_view(),
        name="poster_moderate",
    ),
    url(r"^screen$", ScreenListView.as_view(), name="screen_list"),
    url(r"^screen/create$", ScreenCreateView.as_view(), name="screen_create"),
    url(
        r"^screen/(?P<screen_id>[0-9]+)/slideshow$",
        ScreenSlideshowView.as_view(),
        name="screen_slideshow",
    ),
    url(
        r"^screen/(?P<screen_id>[0-9]+)/edit$",
        ScreenEditView.as_view(),
        name="screen_edit",
    ),
    url(
        r"^screen/(?P<screen_id>[0-9]+)/delete$",
        ScreenDeleteView.as_view(),
        name="screen_delete",
    ),
]
