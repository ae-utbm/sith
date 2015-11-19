from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^login$', views.login, name='login'),
    url(r'^logout$', views.logout, name='logout'),
    url(r'^register$', views.register, name='register'),
    url(r'^user/$', views.user, name='user_list'),
    url(r'^user/(?P<user_id>[0-9]+)/$', views.user, name='user_profile'),
    url(r'^user/(?P<user_id>[0-9]+)/edit$', views.user_edit, name='user_edit'),
]

