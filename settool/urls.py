"""settool URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Import the include() function: from django.conf.urls import url, include
    3. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf import settings
from django.conf.urls import include
from django.conf.urls import url
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView

urlpatterns = [
    # admin
    url(
        r"^admin/",
        admin.site.urls,
    ),
    # login, logout
    url(
        r"^login/$",
        auth_views.LoginView.as_view(template_name="login.html"),
        name="login",
    ),
    url(
        r"^logout/$",
        auth_views.LogoutView.as_view(next_page="/"),
        name="logout",
    ),
    # localization
    url(
        r"^i18n/",
        include("django.conf.urls.i18n"),
    ),
    # index
    url(
        r"^$",
        TemplateView.as_view(template_name="main_index.html"),
        name="main-view",
    ),
    # settool_common: choose semester
    url(
        r"^semester/",
        include("settool_common.urls"),
    ),
    # guided tours
    url(
        r"^tours/",
        include("guidedtours.urls"),
    ),
    # freshmen bags
    url(
        r"^bags/",
        include("bags.urls"),
    ),
    # SET-Fahrt
    url(
        r"^fahrt/",
        include("fahrt.urls"),
    ),
    # Tutoren
    url(
        r"^tutors/",
        include("tutors.urls"),
    ),
]
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
