from django.urls import include
from django.urls import path
from django.views.generic import RedirectView

from settool_common import views

urlpatterns = [
    path("", views.set_semester, name="set_semester"),
    path(
        "settings/",
        include(
            [
                path(
                    "",
                    RedirectView.as_view(pattern_name="settings_dashboard"),
                    name="settings_main_index",
                ),
                path("dashboard/", views.dashboard, name="settings_dashboard"),
                path(
                    "mail/",
                    include(
                        [
                            path(
                                "list/",
                                views.mail_list,
                                name="mail_list",
                            ),
                            path(
                                "import/",
                                views.mail_import,
                                name="mail_import",
                            ),
                            path(
                                "export/",
                                views.mail_export,
                                name="mail_export",
                            ),
                            path(
                                "add/",
                                views.mail_add,
                                name="mail_add",
                            ),
                            path(
                                "edit/<int:private_key>/",
                                views.mail_edit,
                                name="mail_edit",
                            ),
                            path(
                                "delete/<int:private_key>/",
                                views.mail_delete,
                                name="mail_delete",
                            ),
                            path(
                                "view/<int:private_key>/",
                                views.mail_view,
                                name="mail_view",
                            ),
                            path(
                                "send/<int:private_key>/",
                                views.mail_send,
                                name="mail_send",
                            ),
                        ],
                    ),
                ),
            ],
        ),
    ),
]
