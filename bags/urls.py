from django.urls import include, path, re_path
from django.views.generic import RedirectView

from . import views

app_name = "bags"
urlpatterns = [
    path("", RedirectView.as_view(pattern_name="bags:dashboard"), name="main_index"),
    path(
        "dashboard/",
        include(
            [
                path("", views.dashboard, name="dashboard"),
                re_path(
                    r"^update/(?P<company_pk>[0-9]+)/(?P<field>[a-z_]+)/",
                    views.update_field,
                    name="update_company",
                ),
            ],
        ),
    ),
    path(
        "company/",
        include(
            [
                path("add/", views.add_company, name="add_company"),
                path("view/<int:company_pk>/", views.view_company, name="view_company"),
                path("edit/<int:company_pk>/", views.edit_company, name="edit_company"),
                path("delete/<int:company_pk>/", views.del_company, name="del_company"),
            ],
        ),
    ),
    path(
        "giveaway/",
        include(
            [
                path("add/", views.add_giveaway, name="add_giveaway"),
            ],
        ),
    ),
    path(
        "io/",
        include(
            [
                path(
                    "import/",
                    include(
                        [
                            path("semester/", views.import_previous_semester, name="import_previous_semester"),
                            path("csv/", views.import_csv, name="import_csv"),
                        ],
                    ),
                ),
                path("export/", views.export_csv, name="export_csv"),
            ],
        ),
    ),
    path(
        "emails/",
        include(
            [
                path("list/", views.list_mails, name="list_mails"),
                path("add/", views.add_mail, name="add_mail"),
                path("edit/<int:mail_pk>/", views.edit_mail, name="edit_mail"),
                path("delete/<int:mail_pk>/", views.delete_mail, name="del_mail"),
                path("send/<int:mail_pk>/", views.send_mail, name="send_mail"),
            ],
        ),
    ),
]
