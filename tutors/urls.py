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
    ])),
    path('event/', include([

    ])),
    path('task/', include([

    ])),
]
