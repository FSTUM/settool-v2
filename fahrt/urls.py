from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^view/(?P<participant_pk>[0-9]+)/$', views.view,
        name="fahrt_viewparticipant"),
    url(r'^edit/(?P<participant_pk>[0-9]+)/$', views.edit,
        name="fahrt_editparticipant"),
    url(r'^del/(?P<participant_pk>[0-9]+)/$', views.delete,
        name="fahrt_delparticipant"),
    url(r'^togglemailinglist/(?P<participant_pk>[0-9]+)/$',
        views.toggle_mailinglist,
        name="fahrt_toggle_mailinglist"),
    url(r'^setpaid/(?P<participant_pk>[0-9]+)/$',
        views.set_paid,
        name="fahrt_set_paid"),
    url(r'^setnonliability/(?P<participant_pk>[0-9]+)/$',
        views.set_nonliability,
        name="fahrt_set_nonliability"),
    url(r'^signup/$', views.signup, name='fahrt_signup'),
    url(r'^success/(?P<participant_pk>[0-9]+)/$', views.signup_success,
        name='fahrt_signup_success'),
]

