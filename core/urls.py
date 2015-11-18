from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='core_index'),
    url(r'^login$', views.login, name='login'),
    url(r'^register$', views.register, name='register'),
    url(r'^guy$', views.guy, name='guy'),
]

