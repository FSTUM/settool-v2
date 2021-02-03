from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

import settool_common.models as common_models
from settool_common.models import Semester
from settool_common.models import Subject


class TourMail(common_models.Mail):
    # fmt: off
    possible_placeholders = _(
        "You may use {{vorname}} for the participant's first name, "
        "{{tour}} for the name of the tour, "
        "{{zeit}} for the time of the tour.",
    )
    # fmt: on

    # pylint: disable=signature-differs
    def save(self, *args, **kwargs):
        self.sender = common_models.Mail.SET
        super().save(*args, **kwargs)

    def get_mail_participant(self):
        context = {
            "vorname": "<Vorname>",
            "tour": "<Tour>",
            "zeit": "<Zeit>",
        }
        return self.get_mail(context)

    def send_mail_participant(self, participant):
        context = {
            "vorname": participant.firstname,
            "tour": participant.tour.name,
            "zeit": participant.tour.date,
        }
        return self.send_mail(context, participant.email)


class Tour(models.Model):
    class Meta:
        permissions = (
            (
                "view_participants",
                "Can view and edit the list of participants",
            ),
        )

    semester = models.ForeignKey(
        Semester,
        on_delete=models.CASCADE,
    )

    name = models.CharField(
        max_length=200,
        verbose_name=_("Name"),
    )

    description = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("Description"),
    )

    date = models.DateTimeField(
        verbose_name=_("Date"),
    )

    capacity = models.PositiveIntegerField(
        verbose_name=_("Capacity"),
    )

    open_registration = models.DateTimeField(
        _("Open registration"),
    )

    close_registration = models.DateTimeField(
        _("Close registration"),
    )

    def __str__(self):
        return self.name

    @property
    def registration_open(self):
        return self.open_registration < timezone.now() < self.close_registration


class Participant(models.Model):
    tour = models.ForeignKey(
        Tour,
        on_delete=models.CASCADE,
        verbose_name=_("Tour"),
    )

    firstname = models.CharField(
        max_length=200,
        verbose_name=_("First name"),
    )

    surname = models.CharField(
        max_length=200,
        verbose_name=_("Surname"),
    )

    email = models.EmailField(
        verbose_name=_("E-Mail"),
    )

    phone = models.CharField(
        max_length=200,
        verbose_name=_("Mobile phone"),
    )

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        verbose_name=_("Subject"),
    )

    time = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Registration Time"),
    )

    def __str__(self):
        return f"{self.firstname} {self.surname}"

    @property
    def on_the_tour(self):
        participants = self.tour.participant_set.order_by("time")
        participants = participants[: self.tour.capacity]
        return self in participants

    @property
    def status(self):
        if self.on_the_tour:
            return _("On the tour")
        return _("On waitinglist")
