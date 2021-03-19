from django.urls import include, path
from django.views.generic import RedirectView

from settool_common import views

urlpatterns = [
    path("", views.set_semester, name="set_semester"),
    path(
        "settings/",
        include(
            [
                path("", RedirectView.as_view(pattern_name="settings_dashboard"), name="settings_main_index"),
                path("dashboard/", views.dashboard, name="settings_dashboard"),
                path(
                    "study/",
                    include(
                        [
                            path(
                                "subjects/",
                                include(
                                    [
                                        path("list/", views.subject_list, name="subject_list"),
                                        path("add/", views.subject_add, name="subject_add"),
                                        path("delete/<int:subject_pk>/", views.subject_delete, name="subject_delete"),
                                        path("edit/<int:subject_pk>/", views.subject_edit, name="subject_edit"),
                                    ],
                                ),
                            ),
                            path(
                                "course_bundle/",
                                include(
                                    [
                                        path("list/", views.course_bundle_list, name="course_bundle_list"),
                                        path("add/", views.course_bundle_add, name="course_bundle_add"),
                                        path(
                                            "delete/<int:course_bundle_pk>/",
                                            views.course_bundle_delete,
                                            name="course_bundle_delete",
                                        ),
                                        path(
                                            "edit/<int:course_bundle_pk>/",
                                            views.course_bundle_edit,
                                            name="course_bundle_edit",
                                        ),
                                    ],
                                ),
                            ),
                        ],
                    ),
                ),
                path(
                    "mail/",
                    include(
                        [
                            path(
                                "list/",
                                include(
                                    [
                                        path(
                                            "tutors/",
                                            views.filtered_mail_list,
                                            {"mail_filter": "tutors"},
                                            name="filtered_mail_list_tutors",
                                        ),
                                        path("all/", views.mail_list, name="mail_list"),
                                    ],
                                ),
                            ),
                            path("import/", views.mail_import, name="mail_import"),
                            path("export/", views.mail_export, name="mail_export"),
                            path("add/", views.mail_add, name="mail_add"),
                            path("edit/<int:mail_pk>/", views.mail_edit, name="mail_edit"),
                            path("delete/<int:mail_pk>/", views.mail_delete, name="mail_delete"),
                            path("view/<int:mail_pk>/", views.mail_view, name="mail_view"),
                        ],
                    ),
                ),
            ],
        ),
    ),
]
