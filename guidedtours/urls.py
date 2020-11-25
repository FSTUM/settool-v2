from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='tours_list'),
    url(r'^view/(?P<tour_pk>[0-9]+)/$', views.view, name="tours_view"),
    url(r'^signup/$', views.signup, name='tours_signup'),
    url(r'^add/participant/$', views.signup_internal, name='tours_signup_internal'),
    url(r'^add/tour/$', views.add, name='tours_add'),
    url(r'^edit/(?P<tour_pk>[0-9]+)/$', views.edit, name="tours_edit"),
    url(r'^del/(?P<tour_pk>[0-9]+)/$', views.delete, name="tours_del"),
    url(r'^success/$', views.signup_success, name='tours_signup_success'),
    url(r'^filter/$', views.filter_participants, name='tours_filter'),
    url(r'^filtered/$', views.filtered_list, name='tours_filteredparticipants'),
    url(r'^emails/$', views.index_mails, name='tours_listmails'),
    url(r'^emails/add/$', views.add_mail, name='tours_addmail'),
    url(r'^emails/edit/(?P<mail_pk>[0-9]+)/$', views.edit_mail, name="tours_editmail"),
    url(r'^emails/del/(?P<mail_pk>[0-9]+)/$', views.delete_mail, name="tours_delmail"),
    url(r'^emails/send/(?P<mail_pk>[0-9]+)/$', views.send_mail, name="tours_sendmail"),
]
