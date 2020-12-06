from django.conf.urls import url
from django.views.generic import RedirectView

from . import views

urlpatterns = [
    url(r'^$', RedirectView.as_view(pattern_name="tours_dashboard"), name="tour_main_index"),  # needed for active_link
    url(r'^dashboard/$', views.dashboard, name='tours_dashboard'),
    url(r'^list/$', views.list_tours, name='tours_list_tours'),
    url(r'^view/(?P<tour_pk>[0-9]+)/$', views.view, name="tours_view"),
    url(r'^signup/$', views.signup, name='tours_signup'),
    url(r'^add/participant/$', views.signup_internal, name='tours_signup_internal'),
    url(r'^add/tour/$', views.add, name='tours_add_tour'),
    url(r'^edit/(?P<tour_pk>[0-9]+)/$', views.edit, name="tours_edit"),
    url(r'^del/(?P<tour_pk>[0-9]+)/$', views.delete, name="tours_del"),
    url(r'^success/$', views.signup_success, name='tours_signup_success'),
    url(r'^filter/$', views.filter_participants, name='tours_filter'),
    url(r'^filtered/$', views.filtered_list, name='tours_filteredparticipants'),
    url(r'^emails/$', views.index_mails, name='tours_listmails'),
    url(r'^email/$', RedirectView.as_view(pattern_name="tours_listmails")),  # needed for active_link
    url(r'^email/add/$', views.add_mail, name='tours_addmail'),
    url(r'^email/edit/(?P<mail_pk>[0-9]+)/$', views.edit_mail, name="tours_editmail"),
    url(r'^email/del/(?P<mail_pk>[0-9]+)/$', views.delete_mail, name="tours_delmail"),
    url(r'^email/send/(?P<mail_pk>[0-9]+)/$', views.send_mail, name="tours_sendmail"),
]
