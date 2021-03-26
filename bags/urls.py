from django.contrib.auth.decorators import permission_required
from django.urls import include, path, re_path
from django.views.generic import RedirectView

from . import views

app_name = "bags"
urlpatterns = [
    path("", RedirectView.as_view(pattern_name="bags:dashboard"), name="main_index"),
    path("dashboard", views.dashboard, name="dashboard"),
    path(
        "company/",
        include(
            [
                path("add/", views.add_company, name="add_company"),
                path("view/<int:company_pk>/", views.view_company, name="view_company"),
                path("edit/<int:company_pk>/", views.edit_company, name="edit_company"),
                path("delete/<int:company_pk>/", views.del_company, name="del_company"),
                path(
                    "list/",
                    include(
                        [
                            path("", views.list_companys, name="list_companys"),
                            re_path(
                                r"^update/(?P<company_pk>[0-9]+)/(?P<field>[a-z_]+)/",
                                views.update_field,
                                name="update_company",
                            ),
                        ],
                    ),
                ),
            ],
        ),
    ),
    path(
        "giveaway/",
        include(
            [
                path(
                    "group/",
                    include(
                        [
                            path("list/", views.list_giveaway_group, name="list_giveaway_group"),
                            path("add/", views.add_giveaway_group, name="add_giveaway_group"),
                            path(
                                "add/<int:giveaway_group_pk>/",
                                views.add_giveaway_to_giveaway_group,
                                name="add_giveaway_to_giveaway_group",
                            ),
                            path(
                                "edit/<int:giveaway_group_pk>/",
                                views.edit_giveaway_group,
                                name="edit_giveaway_group",
                            ),
                            path(
                                "delete/<int:giveaway_group_pk>/",
                                views.del_giveaway_group,
                                name="del_giveaway_group",
                            ),
                        ],
                    ),
                ),
                path("add/", views.add_giveaway, name="add_giveaway"),
                path(
                    "update/",
                    include(
                        [
                            path(
                                "<int:pk>/",
                                permission_required("bags.view_companies")(
                                    views.GiveawayDistributionUpdateView.as_view(),
                                ),
                                name="update_giveaway",
                            ),
                            path(
                                "giveaway_data/",
                                include(
                                    [
                                        path(
                                            "ungrouped/",
                                            views.giveaway_data_ungrouped,
                                            name="giveaway_data_ungrouped",
                                        ),
                                        path("grouped/", views.giveaway_data_grouped, name="giveaway_data_grouped"),
                                        path(
                                            "condensed/",
                                            views.giveaway_data_condensed_grouped,
                                            name="giveaway_data_condensed_grouped",
                                        ),
                                    ],
                                ),
                            ),
                        ],
                    ),
                ),
                path("view/<int:giveaway_pk>/", views.view_giveaway, name="view_giveaway"),
                path("edit/<int:giveaway_pk>/", views.edit_giveaway, name="edit_giveaway"),
                path("delete/<int:giveaway_pk>/", views.del_giveaway, name="del_giveaway"),
                path(
                    "list/",
                    include(
                        [
                            path("grouped/", views.list_grouped_giveaways, name="list_grouped_giveaways"),
                            path("distribution/", views.list_giveaway_distribution, name="list_giveaway_distribution"),
                            path("arrivals/", views.list_giveaways_arrivals, name="list_giveaways_arrivals"),
                            path("confirm/", views.confirm_giveaways_arrivals, name="confirm_giveaways_arrivals"),
                        ],
                    ),
                ),
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
