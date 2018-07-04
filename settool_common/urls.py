from django.urls import path, include

from settool_common import views

urlpatterns = [
    path('', views.set_semester, name='set_semester'),
    path('mail/', include([
        path('list/', views.mail_list, name='mail_list'),
        path('add/', views.mail_add, name='mail_add'),
        path('edit/<int:pk>/', views.mail_edit, name="mail_edit"),
        path('delete/<int:pk>/', views.mail_delete, name="mail_delete"),
        path('view/<int:pk>/', views.mail_view, name="mail_view"),
        path('send/<int:pk>/', views.mail_send, name="mail_send"),
    ])),
    path('settings/', views.common_settings, name="common_settings"),
]
