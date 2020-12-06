from django.conf.urls import url
from django.views.generic import RedirectView

from . import views

urlpatterns = [
    url(r'^$', RedirectView.as_view(pattern_name='listcompanies'), name='bags_main_index'),
    url(r'^add/$', views.add, name='addcompany'),
    url(r'^view/(?P<company_pk>[0-9]+)/$', views.view, name="viewcompany"),
    url(r'^edit/(?P<company_pk>[0-9]+)/$', views.edit, name="editcompany"),
    url(r'^del/(?P<company_pk>[0-9]+)/$', views.delete, name="delcompany"),
    url(r'^list$', views.index, name='listcompanies'),
    url(r'^giveaways/$', views.insert_giveaways, name='insert_giveaways'),
    url(r'^import/$', views.import_companies, name='import_companies'),
    url(r'^emails/$', views.index_mails, name='listmails'),
    url(r'^emails/add/$', views.add_mail, name='addmail'),
    url(r'^emails/edit/(?P<mail_pk>[0-9]+)/$', views.edit_mail,
        name="editmail"),
    url(r'^emails/del/(?P<mail_pk>[0-9]+)/$', views.delete_mail,
        name="delmail"),
    url(r'^emails/send/(?P<mail_pk>[0-9]+)/$', views.send_mail,
        name="sendmail"),
    url(r'^update/(?P<company_pk>[0-9]+)/(?P<field>[a-z_]+)/$',
        views.update_field, name='updatecompany'),
]
