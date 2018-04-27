from django.urls import path

from . import views

urlpatterns = [
    path('signup/', views.tutoren_signup, name='tutoren_signup'),
    path('success/', views.tutoren_signup_success, name='tutoren_signup_success'),
    path('confirm/', views.tutoren_signup_confirmation_required, name='tutoren_signup_confirmation_required'),
    path('invalid/', views.tutoren_signup_invalid, name='tutoren_signup_invalid'),
    path('confirm/<uidb64>/<token>/', views.tutoren_signup_confirm, name='tutoren_signup_confirm'),
    path('list/', views.tutoren_list, name='tutoren_list'),
    path('list/<str:status>/', views.tutoren_list, name='tutoren_list_status'),
    path('view/<uuid:uid>/', views.tutoren_view, name='tutoren_view'),
    path('accept/<uuid:uid>/', views.tutoren_accept, name='tutoren_accept'),
    path('decline/<uuid:uid>/', views.tutoren_decline, name='tutoren_decline'),
    path('delete/<uuid:uid>/', views.tutoren_delete, name='tutoren_delete'),
    path('edit/<uuid:uid>/', views.tutoren_edit, name='tutoren_edit'),
]
