import datetime
from typing import List

from django.db import models
from django.utils.translation import ugettext_lazy as _


class Location(models.Model):
    shortname = models.CharField(_("short/simplified Address"), max_length=100)

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


class DateGroup(models.Model):
    location = models.ForeignKey(Location, null=True, blank=True, on_delete=models.SET_NULL)
    comment = models.CharField(_("Comment"), blank=True, max_length=200)
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
        return self.task

    @property
    def is_event(self):
        return hasattr(self, "event")

    @property
    def dates(self) -> List[datetime.datetime]:
        return [date.date for date in Date.objects.filter(group=self.id).all()]

    @classmethod
    def create_new_date_group(cls):
        return DateGroup.objects.create().id

    def __str__(self) -> str:
        name = self.super_group.name
        group_type = _("Event") if self.is_event else _("Task")
        if self.location:
            return f"[{group_type}] {name} at {self.location}"
        return f"[{group_type}] {name} ({_('no meeting point specified')})"


class DateGroupSubscriber(models.Model):
    tutor = models.ForeignKey("tutors.Tutor", on_delete=models.CASCADE)
    date = models.ForeignKey(DateGroup, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.tutor}"


class Date(models.Model):
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


class DateSubscriber(models.Model):
    tutor = models.ForeignKey("tutors.Tutor", on_delete=models.CASCADE)
    date = models.ForeignKey(Date, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.tutor}"
