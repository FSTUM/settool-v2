from django.urls import path

from . import views

urlpatterns = [
    path('signup/', views.tutoren_signup, name='tutoren_signup'),
    path('success/', views.tutoren_signup_success, name='tutoren_signup_success'),
    path('confirm/', views.tutoren_signup_confirmation_required, name='tutoren_signup_confirmation_required'),
    path('invalid/', views.tutoren_signup_invalid, name='tutoren_signup_invalid'),
    path('confirm/<uidb64>/<token>/', views.tutoren_signup_confirm, name='tutoren_signup_confirm'),
]
