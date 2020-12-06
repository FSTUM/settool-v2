from django.conf.urls import url
from django.views.generic import RedirectView

from . import views

urlpatterns = [
    url(r'^$', views.index, name="fahrt_index"),
    url(r'^list/registered/$', views.list_registered, name='fahrt_list_registered'),
    url(r'^list/confirmed/$', views.list_confirmed, name='fahrt_list_confirmed'),
    url(r'^list/waitinglist/$', views.list_waitinglist, name='fahrt_list_waitinglist'),
    url(r'^list/cancelled/$', views.list_cancelled, name='fahrt_list_cancelled'),
    url(r'^view/(?P<participant_pk>[0-9]+)/$', views.view, name="fahrt_viewparticipant"),
    url(r'^edit/(?P<participant_pk>[0-9]+)/$', views.edit, name="fahrt_editparticipant"),
    url(r'^del/(?P<participant_pk>[0-9]+)/$', views.delete, name="fahrt_delparticipant"),
    url(r'^togglemailinglist/(?P<participant_pk>[0-9]+)/$', views.toggle_mailinglist,
        name="fahrt_toggle_mailinglist"),
    url(r'^setpaid/(?P<participant_pk>[0-9]+)/$', views.set_paid,
        name="fahrt_set_paid"),
    url(r'^setnonliability/(?P<participant_pk>[0-9]+)/$', views.set_nonliability,
        name="fahrt_set_nonliability"),
    url(r'^set_payment_deadline/(?P<participant_pk>[0-9]+)/(?P<weeks>[0-9]+)/$', views.set_payment_deadline,
        name="fahrt_set_payment_deadline"),
    url(r'^confirm/(?P<participant_pk>[0-9]+)/$', views.confirm, name="fahrt_confirm"),
    url(r'^waitinglist/(?P<participant_pk>[0-9]+)/$', views.waitinglist, name="fahrt_waitinglist"),
    url(r'^cancel/(?P<participant_pk>[0-9]+)/$', views.cancel, name="fahrt_cancel"),
    url(r'^signup/$', views.signup, name='fahrt_signup'),
    url(r'^success/$', views.signup_success, name='fahrt_signup_success'),
    url(r'^add/$', views.signup_internal, name='fahrt_signup_internal'),
    url(r'^filter/$', views.filter_participants, name='fahrt_filter'),
    url(r'^filtered/$', views.filtered_list, name='fahrt_filteredparticipants'),
    url(r'^emails/$', views.index_mails, name='fahrt_listmails'),
    url(r'^email/$', RedirectView.as_view(pattern_name="fahrt_listmails")),  # due to active_link
    url(r'^email/add/$', views.add_mail, name='fahrt_addmail'),
    url(r'^email/edit/(?P<mail_pk>[0-9]+)/$', views.edit_mail, name="fahrt_editmail"),
    url(r'^email/del/(?P<mail_pk>[0-9]+)/$', views.delete_mail, name="fahrt_delmail"),
    url(r'^email/send/(?P<mail_pk>[0-9]+)/$', views.send_mail, name="fahrt_sendmail"),
    url(r'^changedate/$', views.change_date, name="fahrt_date"),
]
