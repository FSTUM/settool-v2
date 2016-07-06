from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^add/$', views.add, name='addcompany'),
    url(r'^view/(?P<company_pk>[0-9]+)/$', views.view, name="viewcompany"),
    url(r'^edit/(?P<company_pk>[0-9]+)/$', views.edit, name="editcompany"),
    url(r'^del/(?P<company_pk>[0-9]+)/$', views.delete, name="delcompany"),
    url(r'^$', views.index, name='listcompanies'),
    url(r'^filter/$', views.filtered_index, name='filteredcompanies'),
    url(r'^emails/$', views.index_mails, name='listmails'),
    url(r'^emails/add/$', views.add_mail, name='addmail'),
    url(r'^emails/edit/(?P<mail_pk>[0-9]+)/$', views.edit_mail,
        name="editmail"),
    url(r'^emails/del/(?P<mail_pk>[0-9]+)/$', views.delete_mail,
        name="delmail"),
    url(r'^emails/send/(?P<mail_pk>[0-9]+)/$', views.send_mail,
        name="sendmail"),
]
