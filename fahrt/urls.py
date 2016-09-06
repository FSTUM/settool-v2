from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^signup/$', views.signup, name='signup'),
    url(r'^success/(?P<participant_pk>[0-9]+)/$', views.signup_success,
        name='signup_success'),
]

