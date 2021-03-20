from django.urls import include, path
from django.views.generic import RedirectView

from . import views

app_name = "tutors"
urlpatterns = [
    path("", RedirectView.as_view(pattern_name="tutors:dashboard"), name="main_index"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path(
        "collaborator/",
        include(
            [
                path("signup/", views.collaborator_signup, name="collaborator_signup"),
                path("signup/success/", views.collaborator_signup_success, name="collaborator_signup_success"),
            ],
        ),
    ),
    path(
        "tutor/",
        include(
            [
                path(
                    "signup/",
                    include(
                        [
                            path("", views.tutor_signup, name="tutor_signup"),
                            path("success/", views.tutor_signup_success, name="tutor_signup_success"),
                            path(
                                "confirm/",
                                views.tutor_signup_confirmation_required,
                                name="tutor_signup_confirmation_required",
                            ),
                            path("confirm/<uidb64>/<token>/", views.tutor_signup_confirm, name="tutor_signup_confirm"),
                            path("invalid/", views.tutor_signup_invalid, name="tutor_signup_invalid"),
                        ],
                    ),
                ),
                path(
                    "list/",
                    include(
                        [
                            path("all/", views.list_participants, {"status": "all"}, name="list_status_all"),
                            path(
                                "accepted/",
                                views.list_participants,
                                {"status": "accepted"},
                                name="list_status_accepted",
                            ),
                            path("active/", views.list_participants, {"status": "active"}, name="list_status_active"),
                            path(
                                "declined/",
                                views.list_participants,
                                {"status": "declined"},
                                name="list_status_declined",
                            ),
                            path(
                                "inactive/",
                                views.list_participants,
                                {"status": "inactive"},
                                name="list_status_inactive",
                            ),
                            path(
                                "collaborator/",
                                views.list_participants,
                                {"status": "employee"},
                                name="list_status_employee",
                            ),
                        ],
                    ),
                ),
                path("view/<uuid:uid>/", views.view_tutor, name="view_tutor"),
                path("status/<uuid:uid>/<str:status>/", views.change_tutor_status, name="change_tutor_status"),
                path("delete/<uuid:uid>/", views.del_tutor, name="del_tutor"),
                path("edit/<uuid:uid>/", views.edit_tutor, name="edit_tutor"),
                path(
                    "export/",
                    include(
                        [
                            path("<str:file_type>/", views.export, name="export_tutors"),
                            path("<str:file_type>/<str:status>/", views.export, name="export_tutors_by_status"),
                        ],
                    ),
                ),
                path(
                    "mail/",
                    include(
                        [
                            path("<str:status>/", views.send_mail, name="mail_status"),
                            path("<str:status>/<int:mail_pk>/", views.send_mail, name="mail_status_template"),
                            path("tutor/<uuid:uid>/", views.send_mail, name="mail_tutor"),
                            path("tutor/<uuid:uid>/<int:mail_pk>/", views.send_mail, name="mail_template"),
                        ],
                    ),
                ),
                path(
                    "batch/",
                    include(
                        [
                            path("accept/", views.batch_accept, name="batch_accept"),
                            path("decline/", views.batch_decline, name="batch_decline"),
                        ],
                    ),
                ),
            ],
        ),
    ),
    path(
        "event/",
        include(
            [
                path("list/", views.list_event, name="list_event"),
                path("add/", views.add_event, name="add_event"),
                path("edit/<uuid:uid>/", views.edit_event, name="edit_event"),
                path("delete/<uuid:uid>/", views.del_event, name="del_event"),
                path("view/<uuid:uid>/", views.view_event, name="view_event"),
            ],
        ),
    ),
    path(
        "task/",
        include(
            [
                path("list/", views.list_task, name="list_task"),
                path("add/", views.add_task, name="add_task"),
                path("add/<uuid:eid>/", views.add_task, name="add_task_for_event"),
                path("edit/<uuid:uid>/", views.edit_task, name="edit_task"),
                path("delete/<uuid:uid>/", views.del_task, name="del_task"),
                path("view/<uuid:uid>/", views.view_task, name="view_task"),
                path("mail/<uuid:uid>/", views.task_mail, name="task_mail"),
                path("mail/<uuid:uid>/<int:mail_pk>/", views.task_mail, name="task_mail_template"),
                path("export/<str:file_type>/<uuid:uid>/", views.export_task, name="export_task"),
            ],
        ),
    ),
    path(
        "requirement/",
        include(
            [
                path("list/", views.list_requirements, name="list_requirements"),
                path("add/", views.add_requirement, name="add_requirement"),
                path("edit/<uuid:uid>/", views.edit_requirement, name="edit_requirement"),
                path("delete/<uuid:uid>/", views.del_requirement, name="del_requirement"),
                path("view/<uuid:uid>/", views.view_requirement, name="view_requirement"),
            ],
        ),
    ),
    path(
        "settings/",
        include(
            [
                path("", RedirectView.as_view(pattern_name="general_settings")),
                path("general/", views.general_settings, name="general_settings"),
                path("tutors/", views.tutor_settings, name="tutor_settings"),
            ],
        ),
    ),
]
