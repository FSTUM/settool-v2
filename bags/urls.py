from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^add/$', views.add, name='addcompany'),
    url(r'^view/(?P<company_pk>[0-9]+)/$', views.view, name="viewcompany"),
    url(r'^edit/(?P<company_pk>[0-9]+)/$', views.edit, name="editcompany"),
    url(r'^del/(?P<company_pk>[0-9]+)/$', views.delete, name="delcompany"),
   url(r'^$', views.index, name='listcompanies'),
]
