from django.urls import include, path
from django.views.generic import RedirectView

from . import views

urlpatterns = [
    path("", RedirectView.as_view(pattern_name="fahrt_index"), name="fahrt_main_index"),
    # due to active_link
    path("dashboard/", views.fahrt_dashboard, name="fahrt_index"),
    path("export/<str:file_format>", views.export, name="fahrt_export"),
    path(
        "list/",
        include(
            [
                path("registered/", views.list_registered, name="fahrt_list_registered"),
                path("confirmed/", views.list_confirmed, name="fahrt_list_confirmed"),
                path("waitinglist/", views.list_waitinglist, name="fahrt_list_waitinglist"),
                path("cancelled/", views.list_cancelled, name="fahrt_list_cancelled"),
            ],
        ),
    ),
    path("view/<int:participant_pk>/", views.view, name="fahrt_viewparticipant"),
    path("non_liability/<int:participant_pk>", views.non_liability_form, name="fahrt_non_liability_form"),
    path("edit/<int:participant_pk>/", views.edit, name="fahrt_editparticipant"),
    path("del/<int:participant_pk>/", views.delete, name="fahrt_delparticipant"),
    path("togglemailinglist/<int:participant_pk>/", views.toggle_mailinglist, name="fahrt_toggle_mailinglist"),
    path("setpaid/<int:participant_pk>/", views.set_paid, name="fahrt_set_paid"),
    path("setnonliability/<int:participant_pk>/", views.set_nonliability, name="fahrt_set_nonliability"),
    path(
        "set_payment_deadline/<int:participant_pk>/<int:weeks>/",
        views.set_payment_deadline,
        name="fahrt_set_payment_deadline",
    ),
    path("confirm/<int:participant_pk>/", views.confirm, name="fahrt_confirm"),
    path("waitinglist/<int:participant_pk>/", views.waitinglist, name="fahrt_waitinglist"),
    path("cancel/<int:participant_pk>/", views.cancel, name="fahrt_cancel"),
    path("signup/", views.signup, name="fahrt_signup"),
    path("success/", views.signup_success, name="fahrt_signup_success"),
    path("add/", views.signup_internal, name="fahrt_signup_internal"),
    path("filter/", views.filter_participants, name="fahrt_filter"),
    path("filtered/", views.filtered_list, name="fahrt_filteredparticipants"),
    path("emails/", views.index_mails, name="fahrt_listmails"),
    path(
        "transport/",
        include(
            [
                path(
                    "mangagement/",
                    include(
                        [
                            path(
                                "add/option/<int:transport_type>",
                                views.transport_mangagement_add_option,
                                name="fahrt_transport_management_add_transport",
                            ),
                            path(
                                "add/participant/<int:transport_pk>/",
                                views.transport_mangagement_add_participant,
                                name="fahrt_transport_management_add_participant",
                            ),
                            path("", views.transport_mangagement, name="fahrt_transport_mangagement"),
                        ],
                    ),
                ),
                path(
                    "participant/",
                    include(
                        [
                            path(
                                "add/option/<uuid:participant_uuid>/<int:transport_type>/",
                                views.transport_add_option,
                                name="fahrt_transport_participant_add_option",
                            ),
                            path(
                                "add/participant/<uuid:participant_uuid>/<int:transport_pk>/",
                                views.transport_add_participant,
                                name="fahrt_transport_add_participant",
                            ),
                            path(
                                "<uuid:participant_uuid>/",
                                views.transport_participant,
                                name="fahrt_transport_participant",
                            ),
                        ],
                    ),
                ),
            ],
        ),
    ),
    path(
        "email/",  # due to active_link
        include(
            [
                path("", RedirectView.as_view(pattern_name="fahrt_listmails")),
                path("add/", views.add_mail, name="fahrt_addmail"),
                path("edit/<int:mail_pk>/", views.edit_mail, name="fahrt_editmail"),
                path("del/<int:mail_pk>/", views.delete_mail, name="fahrt_delmail"),
                path("send/<int:mail_pk>/", views.send_mail, name="fahrt_sendmail"),
            ],
        ),
    ),
    path("changedate/", views.change_date, name="fahrt_date"),
    path(
        "finanz/",
        include(
            [
                path("confirm/", views.fahrt_finanz_confirm, name="fahrt_finanz_confirm"),
                path("simple/", views.fahrt_finanz_simple, name="fahrt_finanz_simple"),
                path("automated/", views.fahrt_finanz_automated, name="fahrt_finanz_automated"),
                path("automated/matching/", views.fahrt_finanz_auto_matching, name="fahrt_finanz_auto_matching"),
            ],
        ),
    ),
]
