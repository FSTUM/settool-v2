from django.urls import include, path
from django.views.generic import RedirectView

from . import views

app_name = "fahrt"
urlpatterns = [
    path("", RedirectView.as_view(pattern_name="fahrt:dashboard"), name="main_index"),
    # due to active_link
    path("dashboard/", views.dashboard, name="dashboard"),
    path(
        "list/",
        include(
            [
                path("registered/", views.list_registered, name="list_registered"),
                path("confirmed/", views.list_confirmed, name="list_confirmed"),
                path("waitinglist/", views.list_waitinglist, name="list_waitinglist"),
                path("cancelled/", views.list_cancelled, name="list_cancelled"),
            ],
        ),
    ),
    path(
        "participant/",
        include(
            [
                path("view/<int:participant_pk>/", views.view_participant, name="view_participant"),
                path("edit/<int:participant_pk>/", views.edit_participant, name="edit_participant"),
                path("delete/<int:participant_pk>/", views.del_participant, name="del_participant"),
                path("non_liability/<int:participant_pk>", views.non_liability_form, name="non_liability_form"),
                path("togglemailinglist/<int:participant_pk>/", views.toggle_mailinglist, name="toggle_mailinglist"),
                path(
                    "set/",
                    include(
                        [
                            path("paid/<int:participant_pk>/", views.set_paid, name="set_paid"),
                            path("nonliability/<int:participant_pk>/", views.set_nonliability, name="set_nonliability"),
                            path(
                                "payment_deadline/<int:participant_pk>/<int:weeks>/",
                                views.set_payment_deadline,
                                name="set_payment_deadline",
                            ),
                            path(
                                "status/",
                                include(
                                    [
                                        path(
                                            "confirm/<int:participant_pk>/",
                                            views.set_status_confirmed,
                                            name="set_status_confirmed",
                                        ),
                                        path(
                                            "waitinglist/<int:participant_pk>/",
                                            views.set_status_waitinglist,
                                            name="set_status_waitinglist",
                                        ),
                                        path(
                                            "cancel/<int:participant_pk>/",
                                            views.set_status_canceled,
                                            name="set_status_canceled",
                                        ),
                                    ],
                                ),
                            ),
                        ],
                    ),
                ),
            ],
        ),
    ),
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
        "filter/",
        include(
            [
                path("", views.filter_participants, name="filter"),
                path("filtered/", views.filtered_list, name="filtered_participants"),
            ],
        ),
    ),
    path(
        "transport/",
        include(
            [
                path(
                    "mangagement/",
                    include(
                        [
                            path("", views.transport_mangagement, name="transport_mangagement"),
                            path(
                                "participant/",
                                include(
                                    [
                                        path(
                                            "delete/<uuid:participant_uuid>/",
                                            views.del_transport_participant_by_management,
                                            name="del_transport_participant_by_management",
                                        ),
                                        path(
                                            "edit/<uuid:participant_uuid>/",
                                            views.edit_transport_participant_by_management,
                                            name="edit_transport_participant_by_management",
                                        ),
                                    ],
                                ),
                            ),
                            path(
                                "add/",
                                include(
                                    [
                                        path(
                                            "option/<int:transport_type>",
                                            views.add_transport_option_by_management,
                                            name="add_transport_option_by_management",
                                        ),
                                        path(
                                            "participant/<int:transport_pk>/",
                                            views.add_transport_participant_by_management,
                                            name="add_transport_participant_by_management",
                                        ),
                                    ],
                                ),
                            ),
                        ],
                    ),
                ),
                path(
                    "participant/",
                    include(
                        [
                            path(
                                "add/",
                                include(
                                    [
                                        path(
                                            "option/<uuid:participant_uuid>/<int:transport_type>/",
                                            views.add_transport_option,
                                            name="add_transport_option",
                                        ),
                                        path(
                                            "participant/<uuid:participant_uuid>/<int:transport_pk>/",
                                            views.add_transport_participant,
                                            name="add_transport_participant",
                                        ),
                                    ],
                                ),
                            ),
                            path(
                                "<uuid:participant_uuid>/",
                                views.transport_participant,
                                name="transport_participant",
                            ),
                        ],
                    ),
                ),
            ],
        ),
    ),
    path(
        "email/",
        include(
            [
                path("list", views.list_mails, name="list_mails"),
                path("add/", views.add_mail, name="add_mail"),
                path("edit/<int:mail_pk>/", views.edit_mail, name="edit_mail"),
                path("delete/<int:mail_pk>/", views.del_mail, name="del_mail"),
                path("send/<int:mail_pk>/", views.send_mail, name="send_mail"),
            ],
        ),
    ),
    path(
        "finanz/",
        include(
            [
                path("confirm/", views.finanz_confirm, name="finanz_confirm"),
                path("simple/", views.finanz_simple, name="finanz_simple"),
                path("automated/", views.finanz_automated, name="finanz_automated"),
                path("automated/matching/", views.finanz_auto_matching, name="finanz_auto_matching"),
            ],
        ),
    ),
    path("settings/", views.settings, name="settings"),
    path("export/<str:file_format>", views.export, name="export"),
]
