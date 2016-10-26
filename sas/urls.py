from django.conf.urls import url, include

from sas.views import *

urlpatterns = [
    url(r'^$', SASMainView.as_view(), name='main'),
    url(r'^album/(?P<album_id>[0-9]+)$', AlbumView.as_view(), name='album'),
    url(r'^picture/(?P<picture_id>[0-9]+)$', PictureView.as_view(), name='picture'),
    url(r'^picture/(?P<picture_id>[0-9]+)/download$', send_pict, name='download'),
    # url(r'^album/new$', AlbumCreateView.as_view(), name='album_new'),
    # url(r'^(?P<club_id>[0-9]+)/$', ClubView.as_view(), name='club_view'),
]

