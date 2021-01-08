from django.urls import include
from django.urls import path
from django.views.generic import RedirectView

from . import views

urlpatterns = [
    path(
        "",
        RedirectView.as_view(
            pattern_name="tours_dashboard",
        ),
        name="tour_main_index",
    ),  # needed for active_link
    path(
        "dashboard/",
        views.dashboard,
        name="tours_dashboard",
    ),
    path(
        "list/",
        views.list_tours,
        name="tours_list_tours",
    ),
    path(
        "view/<int:tour_pk>/",
        views.view,
        name="tours_view",
    ),
    path(
        "signup/",
        views.signup,
        name="tours_signup",
    ),
    path(
        "add/",
        include(
            [
                path("", RedirectView.as_view(pattern_name="tour_main_index")),
                path(
                    "participant/",
                    views.signup_internal,
                    name="tours_signup_internal",
                ),
                path(
                    "tour/",
                    views.add,
                    name="tours_add_tour",
                ),
            ],
        ),
    ),
    path(
        "edit/<int:tour_pk>/",
        views.edit,
        name="tours_edit",
    ),
    path(
        "del/<int:tour_pk>/",
        views.delete,
        name="tours_del",
    ),
    path(
        "success/",
        views.signup_success,
        name="tours_signup_success",
    ),
    path(
        "filter/",
        views.filter_participants,
        name="tours_filter",
    ),
    path(
        "filtered/",
        views.filtered_list,
        name="tours_filteredparticipants",
    ),
    path(
        "emails/",
        views.index_mails,
        name="tours_listmails",
    ),
    path(
        "email/",
        RedirectView.as_view(pattern_name="tours_listmails"),
    ),  # needed for active_link
    path(
        "email/add/",
        views.add_mail,
        name="tours_addmail",
    ),
    path(
        "email/edit/<int:mail_pk>/",
        views.edit_mail,
        name="tours_editmail",
    ),
    path(
        "email/del/<int:mail_pk>/",
        views.delete_mail,
        name="tours_delmail",
    ),
    path(
        "email/send/<int:mail_pk>/",
        views.send_mail,
        name="tours_sendmail",
    ),
]
