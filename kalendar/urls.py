from django.urls import include, path
from django.views.generic import RedirectView

from . import views

app_name = "kalendar"
urlpatterns = [
    path("", RedirectView.as_view(pattern_name="kalendar:dashboard"), name="main_index"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path(
        "matching/",
        include([]),
    ),
    path(
        "management/",
        include(
            [
                path(
                    "list/",
                    include(
                        [
                            path(
                                "chronologically/",
                                views.list_dates_chronologically,
                                name="list_dates_chronologically",
                            ),
                            path("grouped/", views.list_dates_grouped, name="list_dates_grouped"),
                        ],
                    ),
                ),
                path("add/<uuid:date_group_pk>/", views.add_date, name="add_date"),
                path("edit/<uuid:date_pk>/", views.edit_date, name="edit_dates"),
                path("delete/<uuid:date_pk>/", views.del_date, name="del_dates"),
                path("view/<uuid:date_pk>/", views.view_date, name="view_dates"),
            ],
        ),
    ),
]
