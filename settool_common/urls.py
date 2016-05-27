from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.set_semester, name='set_semester'),
]
