from django.urls import include, path
from django.views.generic import RedirectView

from .views import dashboard_views, finanz_views, maintinance_views, participants_views, tex_views, transport_views

app_name = "fahrt"
urlpatterns = [
    path("", RedirectView.as_view(pattern_name="fahrt:dashboard"), name="main_index"),
    # due to active_link
    path("dashboard/", dashboard_views.dashboard, name="dashboard"),
    path(
        "participant/",
        include(
            [
                path(
                    "list/",
                    include(
                        [
                            path("registered/", participants_views.list_registered, name="list_registered"),
                            path("confirmed/", participants_views.list_confirmed, name="list_confirmed"),
                            path("waitinglist/", participants_views.list_waitinglist, name="list_waitinglist"),
                            path("cancelled/", participants_views.list_cancelled, name="list_cancelled"),
                            path("filter/", participants_views.filter_participants, name="filter"),
                            path("filtered/", participants_views.filtered_list, name="filtered_participants"),
                        ],
                    ),
                ),
                path("view/<uuid:participant_pk>/", participants_views.view_participant, name="view_participant"),
                path("edit/<uuid:participant_pk>/", participants_views.edit_participant, name="edit_participant"),
                path("delete/<uuid:participant_pk>/", participants_views.del_participant, name="del_participant"),
                path("non_liability/<uuid:participant_pk>", tex_views.non_liability_form, name="non_liability_form"),
                path(
                    "togglemailinglist/<uuid:participant_pk>/",
                    participants_views.toggle_mailinglist,
                    name="toggle_mailinglist",
                ),
                path(
                    "set/",
                    include(
                        [
                            path("paid/<uuid:participant_pk>/", participants_views.set_paid, name="set_paid"),
                            path(
                                "nonliability/<uuid:participant_pk>/",
                                participants_views.set_nonliability,
                                name="set_nonliability",
                            ),
                            path(
                                "payment_deadline/<uuid:participant_pk>/<int:weeks>/",
                                participants_views.set_payment_deadline,
                                name="set_payment_deadline",
                            ),
                            path(
                                "status/",
                                include(
                                    [
                                        path(
                                            "confirm/<uuid:participant_pk>/",
                                            participants_views.set_status_confirmed,
                                            name="set_status_confirmed",
                                        ),
                                        path(
                                            "waitinglist/<uuid:participant_pk>/",
                                            participants_views.set_status_waitinglist,
                                            name="set_status_waitinglist",
                                        ),
                                        path(
                                            "cancel/<uuid:participant_pk>/",
                                            participants_views.set_status_canceled,
                                            name="set_status_canceled",
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
                            path("", participants_views.signup, name="signup"),
                            path("success/", participants_views.signup_success, name="signup_success"),
                            path("internal/", participants_views.signup_internal, name="signup_internal"),
                        ],
                    ),
                ),
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
                            path("", transport_views.transport_mangagement, name="transport_mangagement"),
                            path(
                                "participant/",
                                include(
                                    [
                                        path(
                                            "delete/<uuid:participant_uuid>/",
                                            transport_views.del_transport_participant_by_management,
                                            name="del_transport_participant_by_management",
                                        ),
                                        path(
                                            "edit/<uuid:participant_uuid>/",
                                            transport_views.edit_transport_participant_by_management,
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
                                            transport_views.add_transport_option_by_management,
                                            name="add_transport_option_by_management",
                                        ),
                                        path(
                                            "participant/<int:transport_pk>/",
                                            transport_views.add_transport_participant_by_management,
                                            name="add_transport_participant_by_management",
                                        ),
                                    ],
                                ),
                            ),
                            path(
                                "chat/<int:transport_pk>/",
                                transport_views.transport_chat_by_management,
                                name="transport_chat_by_management",
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
                                            transport_views.add_transport_option,
                                            name="add_transport_option",
                                        ),
                                        path(
                                            "participant/<uuid:participant_uuid>/<int:transport_pk>/",
                                            transport_views.add_transport_participant,
                                            name="add_transport_participant",
                                        ),
                                    ],
                                ),
                            ),
                            path(
                                "<uuid:participant_uuid>/",
                                transport_views.transport_participant,
                                name="transport_participant",
                            ),
                            path(
                                "chat/<uuid:participant_uuid>/<int:transport_pk>/",
                                transport_views.transport_chat,
                                name="transport_chat",
                            ),
                        ],
                    ),
                ),
            ],
        ),
    ),
    path(
        "maintinance/",
        include(
            [
                path("settings/", maintinance_views.settings, name="settings"),
                path(
                    "email/",
                    include(
                        [
                            path("list", maintinance_views.list_mails, name="list_mails"),
                            path("add/", maintinance_views.add_mail, name="add_mail"),
                            path("edit/<int:mail_pk>/", maintinance_views.edit_mail, name="edit_mail"),
                            path("delete/<int:mail_pk>/", maintinance_views.del_mail, name="del_mail"),
                            path("send/<int:mail_pk>/", maintinance_views.send_mail, name="send_mail"),
                        ],
                    ),
                ),
            ],
        ),
    ),
    path(
        "finanz/",
        include(
            [
                path("confirm/", finanz_views.finanz_confirm, name="finanz_confirm"),
                path("simple/", finanz_views.finanz_simple, name="finanz_simple"),
                path("automated/", finanz_views.finanz_automated, name="finanz_automated"),
                path("automated/matching/", finanz_views.finanz_auto_matching, name="finanz_auto_matching"),
            ],
        ),
    ),
    path("export/<str:file_format>", tex_views.export, name="export"),
]
