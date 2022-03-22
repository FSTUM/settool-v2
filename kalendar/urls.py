from django.urls import include, path
from django.views.generic import RedirectView

from . import views
from .feeds import PersonalMeetingFeed

app_name = "kalendar"
urlpatterns = [
    path("", RedirectView.as_view(pattern_name="kalendar:dashboard"), name="main_index"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path(
        "user/",
        include(
            [
                path(
                    "matching/",
                    include([]),
                ),
                path("<uuid:tutor_uuid>/ical/", PersonalMeetingFeed(), name="ical_personal"),
                path("<uuid:tutor_uuid>/view/<uuid:date_pk>/", views.view_date_public, name="view_date_public"),
            ],
        ),
    ),
    path(
        "management/",
        include(
            [
                path(
                    "list/",
                    include(
                        [
                            path("future/", views.list_future_dates, name="list_future_dates"),
                            path("chronologically/", views.list_dates, name="list_dates"),
                            path("grouped/", views.list_dates_grouped, name="list_dates_grouped"),
                        ],
                    ),
                ),
                path("add/<uuid:date_group_pk>/", views.add_date, name="add_date"),
                path("edit/<uuid:date_pk>/", views.edit_date, name="edit_date"),
                path("delete/<uuid:date_pk>/", views.del_date, name="del_date"),
                path("view/<uuid:date_pk>/", views.view_date, name="view_date"),
            ],
        ),
    ),
]
