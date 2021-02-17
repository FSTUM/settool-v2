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
