from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^view/(?P<tour_pk>[0-9]+)/$', views.view, name="view"),

]
