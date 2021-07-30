from django.conf import settings
from django.conf.urls import include
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path
from django.views.generic import RedirectView, TemplateView

urlpatterns = [
    # admin
    path("admin/", admin.site.urls),
    # login, logout
    path("login/", auth_views.LoginView.as_view(template_name="login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="/"), name="logout"),
    # localization
    path("i18n/", include("django.conf.urls.i18n")),
    # index
    path("", TemplateView.as_view(template_name="main_index.html"), name="main-view"),
    # settool_common: choose semester
    path("semester/", include("settool_common.urls")),
    # guided tours
    path("tours/", include("guidedtours.urls")),
    path("g/", RedirectView.as_view(pattern_name="guidedtours:signup"), name="short_guidedtour_signup"),
    # freshmen bags
    path("bags/", include("bags.urls")),
    # SET-Fahrt
    path("fahrt/", include("fahrt.urls")),
    path("f/", RedirectView.as_view(pattern_name="fahrt:signup"), name="short_fahrt_signup"),
    # calendars
    path("calendar/", include("kalendar.urls")),
    # tutors
    path("tutors/", include("tutors.urls")),
    path("c/", RedirectView.as_view(pattern_name="tutors:collaborator_signup"), name="short_collaborator_signup"),
    path("t/", RedirectView.as_view(pattern_name="tutors:tutor_signup"), name="short_tutor_signup"),
]
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
