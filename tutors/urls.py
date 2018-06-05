from django.urls import path, include

from . import views

urlpatterns = [
    path('tutor/', include([
        path('signup/', views.tutor_signup, name='tutor_signup'),
        path('signup/success/', views.tutor_signup_success, name='tutor_signup_success'),
        path('signup/confirm/', views.tutor_signup_confirmation_required, name='tutor_signup_confirmation_required'),
        path('signup/confirm/<uidb64>/<token>/', views.tutor_signup_confirm, name='tutor_signup_confirm'),
        path('signup/invalid/', views.tutor_signup_invalid, name='tutor_signup_invalid'),
        path('list/', views.tutor_list, name='tutor_list'),
        path('list/<str:status>/', views.tutor_list, name='tutor_list_status'),
        path('view/<uuid:uid>/', views.tutor_view, name='tutor_view'),
        path('accept/<uuid:uid>/', views.tutor_accept, name='tutor_accept'),
        path('decline/<uuid:uid>/', views.tutor_decline, name='tutor_decline'),
        path('delete/<uuid:uid>/', views.tutor_delete, name='tutor_delete'),
        path('edit/<uuid:uid>/', views.tutor_edit, name='tutor_edit'),
        path('export/<str:type>/', views.tutor_export, name='tutor_export'),
        path('export/<str:type>/<str:status>', views.tutor_export, name='tutor_export_status'),
    ])),
    path('event/', include([
        path('list/', views.event_list, name='event_list'),
        path('add/', views.event_add, name='event_add'),
        path('edit/<uuid:uid>/', views.event_edit, name='event_edit'),
        path('delete/<uuid:uid>/', views.event_delete, name='event_delete'),
        path('view/<uuid:uid>/', views.event_view, name='event_view'),
    ])),
    path('task/', include([
        path('list/', views.task_list, name='task_list'),
        path('add/', views.task_add, name='task_add'),
        path('edit/<uuid:uid>/', views.task_edit, name='task_edit'),
        path('delete/<uuid:uid>/', views.task_delete, name='task_delete'),
        path('view/<uuid:uid>/', views.task_view, name='task_view'),
        path('mail/<uuid:uid>/', views.task_mail, name='task_mail'),
    ])),
    path('requirement/', include([
        path('list/', views.requirement_list, name='requirement_list'),
        path('add/', views.requirement_add, name='requirement_add'),
        path('edit/<uuid:uid>/', views.requirement_edit, name='requirement_edit'),
        path('delete/<uuid:uid>/', views.requirement_delete, name='requirement_delete'),
        path('view/<uuid:uid>/', views.requirement_view, name='requirement_view'),
    ]))
]
