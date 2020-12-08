from django.urls import path, include
from django.views.generic import RedirectView

from settool_common import views

urlpatterns = [
    path('', views.set_semester, name='set_semester'),
    path('settings/', include([
        path('', RedirectView.as_view(pattern_name="mail_list"), name='settings_main_index'),
        path('mail/', include([
            path('list/', views.mail_list, name='mail_list'),
            path('add/', views.mail_add, name='mail_add'),
            path('edit/<int:private_key>/', views.mail_edit, name="mail_edit"),
            path('delete/<int:private_key>/', views.mail_delete, name="mail_delete"),
            path('view/<int:private_key>/', views.mail_view, name="mail_view"),
            path('send/<int:private_key>/', views.mail_send, name="mail_send"),
        ])),
    ])),
]
