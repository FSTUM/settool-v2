import datetime
from typing import Optional
from uuid import UUID

import django.utils.timezone
import icalendar
from django.db.models import QuerySet
from django.http import Http404, HttpRequest
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.html import escape
from django_ical.views import ICalFeed, ICAL_EXTRA_FIELDS

from tutors.models import Tutor

from .models import Date


class PersonalMeetingFeed(ICalFeed):
    file_name = "meetings.ics"
    timezone = "MET"
    tutor: Optional[Tutor] = None

    # noinspection PyMethodOverriding
    # pylint: disable=arguments-differ
    def get_object(self, request: HttpRequest, tutor_uuid: UUID) -> Tutor:
        tutor: Tutor = get_object_or_404(Tutor, pk=tutor_uuid)
        self.tutor = tutor
        return tutor

    @staticmethod
    def product_id(tutor: Tutor) -> str:
        return f"-//set.mpi.fs.tum.de//user//ical//{tutor.pk}"

    @staticmethod
    def items(tutor: Tutor) -> QuerySet[Date]:
        reference_time = django.utils.timezone.now() - datetime.timedelta(days=7 * 6)
        return Date.get_dates_for_tutor(tutor.pk, reference_time)

    def item_title(self, item: Date) -> str:
        super_type = item.group.group_type.capitalize()
        # Titles should be double escaped by default
        return escape(f"[SET-{super_type}] {item.group.super_group.name}")

    def item_updateddate(self, item: Date) -> datetime.datetime:
        return item.updated_at

    def item_created(self, item: Date) -> datetime.datetime:
        return item.created_at

    def item_description(self, item: Date) -> str:
        return str(item.group.super_group.description)

    def item_link(self, item: Date) -> str:
        if not self.tutor:
            raise Http404()
        return reverse("kalendar:view_date_public", args=[self.tutor.pk, item.pk])

    @staticmethod
    def item_organizer(_item: Date) -> icalendar.vCalAddress:
        organizer = icalendar.vCalAddress("MAILTO:set-tutoren@fs.tum.de")
        organizer.params["CN"] = icalendar.vText("SET-Tutor-Team")
        return organizer

    @staticmethod
    def item_start_datetime(item: Date) -> datetime.datetime:
        return item.date

    @staticmethod
    def item_end_datetime(item: Date) -> datetime.datetime:
        return item.date + datetime.timedelta(minutes=item.probable_length)

    @staticmethod
    def item_location(item: Date) -> str:
        location = item.group.location
        return str(location) if location else ""

    @staticmethod
    def item_categories(item: Date) -> str:
        group_type = item.group.group_type.upper()
        return f"SET,{group_type}"

    def item_extra_kwargs(self, item):
        kwargs = {}
        for field in ICAL_EXTRA_FIELDS + ["categories"]:
            val = self._get_dynamic_attr("item_" + field, item)
            if val:
                kwargs[field] = val
        return kwargs
