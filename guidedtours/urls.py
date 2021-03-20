from django.urls import include, path
from django.views.generic import RedirectView

from . import views

app_name = "guidedtours"
urlpatterns = [
    path("", RedirectView.as_view(pattern_name="guidedtours:dashboard"), name="main_index"),  # needed for active_link
    path("dashboard/", views.dashboard, name="dashboard"),
    path(
        "signup/",
        include(
            [
                path("", views.signup, name="signup"),
                path("success/", views.signup_success, name="signup_success"),
                path("internal/", views.signup_internal, name="signup_internal"),
            ],
        ),
    ),
    path(
        "tour/",
        include(
            [
                path("add/", views.add_tour, name="add_tour"),
                path("list/", views.list_tours, name="list_tours"),
                path("view/<int:tour_pk>/", views.view_tour, name="view_tour"),
                path("edit/<int:tour_pk>/", views.edit_tour, name="edit_tour"),
                path("delete/<int:tour_pk>/", views.del_tour, name="del_tour"),
                path("export/<str:file_format>/<int:tour_pk>/", views.export_tour, name="export_tour"),
            ],
        ),
    ),
    path(
        "filter/",
        include(
            [
                path("", views.filter_participants, name="filter"),
                path("filtered/", views.filtered_list, name="filtered_participants"),
            ],
        ),
    ),
    path(
        "email/",
        include(
            [
                path("", RedirectView.as_view(pattern_name="guidedtours:list_mails")),  # needed for active_link
                path("list/", views.list_mails, name="list_mails"),
                path("add/", views.add_mail, name="add_mail"),
                path("edit/<int:mail_pk>/", views.edit_mail, name="edit_mail"),
                path("delete/<int:mail_pk>/", views.delete_mail, name="del_mail"),
                path("send/<int:mail_pk>/", views.send_mail, name="send_mail"),
                path("settings/", views.settings, name="settings"),
            ],
        ),
    ),
]
