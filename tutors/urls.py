from django.urls import include, path
from django.views.generic import RedirectView

from . import views

urlpatterns = [
    path("", RedirectView.as_view(pattern_name="tutor_dashboard"), name="tutor_main_index"),
    path("dashboard/", views.dashboard, name="tutor_dashboard"),
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
                path("signup/", views.tutor_signup, name="tutor_signup"),
                path("signup/success/", views.tutor_signup_success, name="tutor_signup_success"),
                path(
                    "signup/confirm/",
                    views.tutor_signup_confirmation_required,
                    name="tutor_signup_confirmation_required",
                ),
                path("signup/confirm/<uidb64>/<token>/", views.tutor_signup_confirm, name="tutor_signup_confirm"),
                path("signup/invalid/", views.tutor_signup_invalid, name="tutor_signup_invalid"),
                path(
                    "list/",
                    include(
                        [
                            path("all/", views.tutor_list, {"status": "all"}, name="tutor_list_status_all"),
                            path(
                                "accepted/",
                                views.tutor_list,
                                {"status": "accepted"},
                                name="tutor_list_status_accepted",
                            ),
                            path("active/", views.tutor_list, {"status": "active"}, name="tutor_list_status_active"),
                            path(
                                "declined/",
                                views.tutor_list,
                                {"status": "declined"},
                                name="tutor_list_status_declined",
                            ),
                            path(
                                "inactive/",
                                views.tutor_list,
                                {"status": "inactive"},
                                name="tutor_list_status_inactive",
                            ),
                            path(
                                "collaborator/",
                                views.tutor_list,
                                {"status": "employee"},
                                name="tutor_list_status_employee",
                            ),
                        ],
                    ),
                ),
                path("view/<uuid:uid>/", views.tutor_view, name="tutor_view"),
                path("status/<uuid:uid>/<str:status>/", views.tutor_change_status, name="tutor_change_status"),
                path("delete/<uuid:uid>/", views.tutor_delete, name="tutor_delete"),
                path("edit/<uuid:uid>/", views.tutor_edit, name="tutor_edit"),
                path("export/<str:file_type>/", views.tutor_export, name="tutor_export"),
                path("export/<str:file_type>/<str:status>/", views.tutor_export, name="tutor_export_status"),
                path("mail/<str:status>/", views.tutor_mail, name="tutor_mail_status"),
                path("mail/<str:status>/<int:mail_pk>/", views.tutor_mail, name="tutor_mail_status_template"),
                path("mail/tutor/<uuid:uid>/", views.tutor_mail, name="tutor_mail_tutor"),
                path("mail/tutor/<uuid:uid>/<int:mail_pk>/", views.tutor_mail, name="tutor_mail_tutor_template"),
                path("batch/accept/", views.tutor_batch_accept, name="tutor_batch_accept"),
                path("batch/decline/", views.tutor_batch_decline, name="tutor_batch_decline"),
            ],
        ),
    ),
    path(
        "event/",
        include(
            [
                path("list/", views.event_list, name="event_list"),
                path("add/", views.event_add, name="event_add"),
                path("edit/<uuid:uid>/", views.event_edit, name="event_edit"),
                path("delete/<uuid:uid>/", views.event_delete, name="event_delete"),
                path("view/<uuid:uid>/", views.event_view, name="event_view"),
            ],
        ),
    ),
    path(
        "task/",
        include(
            [
                path("list/", views.task_list, name="task_list"),
                path("add/", views.task_add, name="task_add"),
                path("add/<uuid:eid>/", views.task_add, name="task_add_event"),
                path("edit/<uuid:uid>/", views.task_edit, name="task_edit"),
                path("delete/<uuid:uid>/", views.task_delete, name="task_delete"),
                path("view/<uuid:uid>/", views.task_view, name="task_view"),
                path("mail/<uuid:uid>/", views.task_mail, name="task_mail"),
                path("mail/<uuid:uid>/<int:mail_pk>/", views.task_mail, name="task_mail_template"),
                path("export/<str:file_type>/<uuid:uid>/", views.task_export, name="task_export"),
            ],
        ),
    ),
    path(
        "requirement/",
        include(
            [
                path("list/", views.requirement_list, name="requirement_list"),
                path("add/", views.requirement_add, name="requirement_add"),
                path("edit/<uuid:uid>/", views.requirement_edit, name="requirement_edit"),
                path("delete/<uuid:uid>/", views.requirement_delete, name="requirement_delete"),
                path("view/<uuid:uid>/", views.requirement_view, name="requirement_view"),
            ],
        ),
    ),
    path(
        "settings/",
        include(
            [
                path("", RedirectView.as_view(pattern_name="tutors_settings_general")),
                path("general/", views.tutors_settings_general, name="tutors_settings_general"),
                path("tutors/", views.tutors_settings_tutors, name="tutors_settings_tutors"),
            ],
        ),
    ),
]
