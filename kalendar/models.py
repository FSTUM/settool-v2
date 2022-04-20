import datetime
from typing import Optional
from uuid import UUID

from django.db import IntegrityError, models
from django.db.models import Q, QuerySet
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

import kalendar
import settool_common.models as common_models


class Location(common_models.UUIDModelBase, common_models.LoggedModelBase):
    shortname = models.CharField(_("short/simplified Address"), max_length=200)

    address = models.CharField(_("(Street)map-address"), blank=True, max_length=100)
    room = models.CharField(_("Room"), blank=True, max_length=50)

    comment = models.CharField(_("Comment"), blank=True, max_length=200)

    def __str__(self) -> str:
        message = self.shortname
        if self.address:
            message += f"<br/>{_('Adress')}: {self.address}"
        if self.room:
            message += f"<br/>{_('Room')}: {self.room}"
        return mark_safe(message)  # nosec: fully defined


class DateGroup(common_models.UUIDModelBase, common_models.LoggedModelBase):
    location = models.ForeignKey(Location, null=True, blank=True, default=None, on_delete=models.SET_NULL)
    comment = models.CharField(_("Comment"), blank=True, default="", max_length=200)
    subscribers = models.ManyToManyField(
        "tutors.Tutor",
        verbose_name=_("Subscribers to a date_group"),
        through="DateGroupSubscriber",
        blank=True,
    )

    @property
    def super_group(self):
        if hasattr(self, "event"):
            return self.event
        if hasattr(self, "tour"):
            return self.tour
        return self.task

    @property
    def group_type(self):
        if hasattr(self, "event"):
            return "event"
        if hasattr(self, "tour"):
            return "tour"
        return "task"

    @property
    def group_type_str(self):
        lut = {
            "event": _("Event"),
            "tour": _("Tour"),
            "task": _("Task"),
        }
        return lut[self.group_type]

    @property
    def dates(self) -> list[datetime.datetime]:
        return [date.date for date in Date.objects.filter(group=self.id).all()]

    @property
    def date_objects(self) -> list["Date"]:
        return list(Date.objects.filter(group=self.id).all())

    def __str__(self) -> str:
        name = self.super_group.name
        if self.location:
            return f"[{self.group_type_str}] {name} at {self.location}"
        return f"[{self.group_type_str}] {name} ({_('no meeting point specified')})"


class BaseDateGroupInstance(
    common_models.UUIDModelBase,
    common_models.LoggedModelBase,
    common_models.SemesterModelBase,
):
    class Meta:
        abstract = True

    name = models.CharField(_("Name"), max_length=250)
    description = models.TextField(_("Description"), blank=True)

    @property
    def meeting_point_str(self) -> str:
        if not self.associated_meetings:
            raise IntegrityError(f"{self.__class__} {self.id} has no associated_meetings")
        if not self.associated_meetings.location:
            return _("no meeting point specified")
        return str(self.associated_meetings.location)

    associated_meetings = models.OneToOneField(
        DateGroup,
        verbose_name=_("Associated Meetings"),
        null=True,
        on_delete=models.SET_NULL,
    )

    @property
    def first_datetime(self) -> Optional[datetime.datetime]:
        if not self.associated_meetings:
            raise IntegrityError(f"{self.__class__} {self.id} has no associated_meetings")
        date: Optional[kalendar.models.Date] = self.associated_meetings.date_set.order_by("date").first()
        if not date:
            return None
        return date.date

    @property
    def last_datetime(self) -> Optional[datetime.datetime]:
        if not self.associated_meetings:
            raise IntegrityError(f"{self.__class__} {self.id} has no associated_meetings")
        date: Optional[kalendar.models.Date] = self.associated_meetings.date_set.order_by("-date").first()
        if not date:
            return None
        return date.date + datetime.timedelta(minutes=date.probable_length)

    @classmethod
    def sorted_by_semester(cls, semester: int) -> list[type["BaseDateGroupInstance"]]:
        all_instances: QuerySet[type[BaseDateGroupInstance]] = cls.objects.filter(  # type: ignore
            semester=semester,
        ).all()
        instances_sorting: list[tuple[datetime.datetime, type[BaseDateGroupInstance]]] = [
            (instance.first_datetime, instance) for instance in all_instances if instance.first_datetime  # type: ignore
        ]
        return [instance for (_, instance) in sorted(instances_sorting, key=lambda t: t[0])]


class DateGroupSubscriber(common_models.UUIDModelBase, common_models.LoggedModelBase):
    tutor = models.ForeignKey("tutors.Tutor", on_delete=models.CASCADE)
    date = models.ForeignKey(DateGroup, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"{self.tutor}"


class Date(common_models.UUIDModelBase, common_models.LoggedModelBase):
    group = models.ForeignKey(DateGroup, on_delete=models.CASCADE)
    date = models.DateTimeField(_("Date and Time"))
    probable_length = models.IntegerField(_("probable length in minutes"), default=60)
    meeting_subscribers = models.ManyToManyField(
        "tutors.Tutor",
        verbose_name=_("Subscribers to one meeting"),
        through="DateSubscriber",
        blank=True,
    )

    def __str__(self) -> str:
        return self.date.strftime("%x %X")

    def intersects(self, other_date: "Date") -> bool:
        latest_start = max(self.date, other_date.date)
        end_self = self.date + datetime.timedelta(minutes=self.probable_length)
        end_other = other_date.date + datetime.timedelta(minutes=other_date.probable_length)
        earliest_end = min(end_self, end_other)
        return latest_start <= earliest_end

    @property
    def table_color(self) -> str:
        lut = {
            ("event", True): "warning",
            ("event", False): "success",
            ("task", True): "secondary",
            ("task", False): "light",
            ("tour", True): "primary",
            ("tour", False): "info",
        }
        return lut[self.group.group_type, self.is_in_future]

    @classmethod
    def get_dates_for_tutor(cls, tutor_uuid: UUID, reference_time: datetime.datetime) -> QuerySet["Date"]:
        subbed_date_groups = DateGroupSubscriber.objects.filter(tutor=tutor_uuid).values("date")
        subbed_dates = DateSubscriber.objects.filter(tutor=tutor_uuid).values("date")
        return (
            cls.objects.filter(date__gte=reference_time)
            .filter(Q(group__in=subbed_date_groups) | Q(pk__in=subbed_dates))
            .order_by("-date")
            .distinct()
            .all()
        )

    @property
    def probable_end(self) -> datetime.datetime:
        return self.date + datetime.timedelta(minutes=self.probable_length)

    @property
    def is_in_future(self) -> bool:
        return self.probable_end > timezone.now()


class DateSubscriber(common_models.UUIDModelBase, common_models.LoggedModelBase):
    tutor = models.ForeignKey("tutors.Tutor", on_delete=models.CASCADE)
    date = models.ForeignKey(Date, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"{self.tutor}"


def create_associated_meetings() -> UUID:
    return kalendar.models.DateGroup.objects.create().id
