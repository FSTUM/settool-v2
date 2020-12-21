from django.urls import include
from django.urls import path
from django.urls import re_path
from django.views.generic import RedirectView

from . import views

urlpatterns = [
    path(
        "",
        RedirectView.as_view(pattern_name="bags_dashboard"),
        name="bags_main_index",
    ),
    path(
        "add/",
        views.add,
        name="addcompany",
    ),
    path(
        "view/<int:company_pk>/",
        views.company_details,
        name="viewcompany",
    ),
    path(
        "edit/<int:company_pk>/",
        views.edit,
        name="editcompany",
    ),
    path(
        "del/<int:company_pk>/",
        views.delete,
        name="delcompany",
    ),
    path(
        "dashboard/",
        views.bags_dashboard,
        name="bags_dashboard",
    ),
    path(
        "giveaways/",
        views.insert_giveaways,
        name="insert_giveaways",
    ),
    path(
        "import/",
        views.import_companies,
        name="import_companies",
    ),
    path(
        "emails/",
        include(
            [
                path(
                    "",
                    views.index_mails,
                    name="listmails",
                ),
                path(
                    "add/",
                    views.add_mail,
                    name="addmail",
                ),
                path(
                    "edit/<int:mail_pk>/",
                    views.edit_mail,
                    name="editmail",
                ),
                path(
                    "del/<int:mail_pk>/",
                    views.delete_mail,
                    name="delmail",
                ),
                path(
                    "send/<int:mail_pk>/",
                    views.send_mail,
                    name="sendmail",
                ),
            ],
        ),
    ),
    re_path(
        r"^update/(?P<company_pk>[0-9]+)/(?P<field>[a-z_]+)/",
        views.update_field,
        name="updatecompany",
    ),
]
