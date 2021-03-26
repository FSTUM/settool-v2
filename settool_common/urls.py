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
                                        path("list/", views.list_subjects, name="list_subjects"),
                                        path("add/", views.add_subject, name="add_subject"),
                                        path("delete/<int:subject_pk>/", views.del_subject, name="del_subject"),
                                        path("edit/<int:subject_pk>/", views.edit_subject, name="edit_subject"),
                                    ],
                                ),
                            ),
                            path(
                                "course_bundle/",
                                include(
                                    [
                                        path("list/", views.list_course_bundles, name="list_course_bundles"),
                                        path("add/", views.add_course_bundle, name="add_course_bundle"),
                                        path(
                                            "delete/<int:course_bundle_pk>/",
                                            views.del_course_bundle,
                                            name="del_course_bundle",
                                        ),
                                        path(
                                            "edit/<int:course_bundle_pk>/",
                                            views.edit_course_bundle,
                                            name="edit_course_bundle",
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
                                            views.list_filtered_mail,
                                            {"mail_filter": "tutors"},
                                            name="list_filtered_mail_tutors",
                                        ),
                                        path("all/", views.list_mail, name="list_mail"),
                                    ],
                                ),
                            ),
                            path("import/", views.import_mail, name="import_mail"),
                            path("export/", views.export_mail, name="export_mail"),
                            path("add/", views.add_mail, name="add_mail"),
                            path("edit/<int:mail_pk>/", views.edit_mail, name="edit_mail"),
                            path("delete/<int:mail_pk>/", views.del_mail, name="del_mail"),
                            path("view/<int:mail_pk>/", views.view_mail, name="view_mail"),
                        ],
                    ),
                ),
                path(
                    "qr-codes/",
                    include(
                        [
                            path("list/", views.list_qr_codes, name="list_qr_codes"),
                            path("add/", views.add_qr_code, name="add_qr_code"),
                            path("del/<int:qr_code_pk>/", views.del_qr_code, name="del_qr_code"),
                        ],
                    ),
                ),
            ],
        ),
    ),
]
