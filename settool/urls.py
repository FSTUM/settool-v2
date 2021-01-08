from django.conf import settings
from django.conf.urls import include
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path
from django.views.generic import TemplateView

urlpatterns = [
    # admin
    path(
        "admin/",
        admin.site.urls,
    ),
    # login, logout
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="login.html"),
        name="login",
    ),
    path(
        "logout/",
        auth_views.LogoutView.as_view(next_page="/"),
        name="logout",
    ),
    # localization
    path(
        "i18n/",
        include("django.conf.urls.i18n"),
    ),
    # index
    path(
        "",
        TemplateView.as_view(template_name="main_index.html"),
        name="main-view",
    ),
    # settool_common: choose semester
    path(
        "semester/",
        include("settool_common.urls"),
    ),
    # guided tours
    path(
        "tours/",
        include("guidedtours.urls"),
    ),
    # freshmen bags
    path(
        "bags/",
        include("bags.urls"),
    ),
    # SET-Fahrt
    path(
        "fahrt/",
        include("fahrt.urls"),
    ),
    # Tutoren
    path(
        "tutors/",
        include("tutors.urls"),
    ),
]
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
