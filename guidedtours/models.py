from dateutil.relativedelta import relativedelta
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

import kalendar.models
import settool_common.models as common_models
from settool_common.models import Semester, Subject

ANNONIMISATION_GRACEPERIOD_AFTER_LAST_TOUR = relativedelta(weeks=6)


class TourMail(common_models.Mail):
    # ["{{template}}", "description"]
    general_placeholders = [
        ("{{vorname}}", _("The participant's first name")),
        ("{{tour}}", _("The name of the tour")),
        ("{{participant}}", _("The participant")),
        ("{{zeit}}", _("The time of the tour")),
        ("{{tour_status}}", _("'Tour' or 'Waitinglist' depending on on_the_tour status")),
    ]
    # ["{{template}}", "description", "contition"]
    conditional_placeholders: list[tuple[str, str, str]] = []
    notes = ""

    required_perm = common_models.Mail.required_perm + ["guidedtours.view_participants"]

    # pylint: disable=signature-differs
    def save(self, *args, **kwargs):
        self.sender = common_models.Mail.SET
        super().save(*args, **kwargs)

    def get_mail_participant(self):
        context = {
            "vorname": "<Vorname>",
            "tour": "<Tour>",
            "zeit": "<Zeit>",
            "participant": "<Participant>",
            "tour_status": "<tour_status>",
        }
        return self.get_mail(context)

    def send_mail_participant(self, participant):
        context = {
            "vorname": participant.firstname,
            "tour": participant.tour.name,
            "zeit": participant.tour.date,
            "participant": participant,
            "tour_status": "Tour" if participant.on_the_tour else "Waitinglist",
        }
        return self.send_mail(context, participant.email)


class Tour(kalendar.models.BaseDateGroupInstance):
    class Meta:
        permissions = (
            (
                "view_participants",
                "Can view and edit the list of participants",
            ),
        )

    capacity = models.PositiveIntegerField(verbose_name=_("Capacity"))

    open_registration = models.DateTimeField(_("Open registration"))
    close_registration = models.DateTimeField(_("Close registration"))

    def __str__(self) -> str:
        return self.name

    @property
    def registration_open(self):
        return self.open_registration < timezone.now() < self.close_registration


# pylint: disable=unused-argument
@receiver(post_save, sender=Tour)
def create_event_meetings(sender, instance, created, **kwargs):
    if not instance.associated_meetings:
        instance.associated_meetings = kalendar.models.create_associated_meetings()
        instance.save()


# pylint: enable=unused-argument


class Participant(common_models.LoggedModelBase):
    class Meta:
        unique_together = ("tour", "email")

    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, verbose_name=_("Tour"))
    date = models.ForeignKey("kalendar.Date", on_delete=models.CASCADE, verbose_name=_("Date"))
    firstname = models.CharField(max_length=200, verbose_name=_("First name"))
    surname = models.CharField(max_length=200, verbose_name=_("Surname"))
    email = models.EmailField(verbose_name=_("E-Mail"))
    phone = models.CharField(max_length=200, verbose_name=_("Mobile phone"))
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, verbose_name=_("Subject"))

    def __str__(self) -> str:
        return f"{self.firstname} {self.surname}"

    @property
    def on_the_tour(self):
        participants = self.tour.participant_set.order_by("created_at")
        participants = participants[: self.tour.capacity]
        return self in participants

    @property
    def status(self):
        if self.on_the_tour:
            return _("On the tour")
        return _("On waitinglist")


class Setting(common_models.LoggedModelBase):
    semester = models.OneToOneField(Semester, on_delete=models.CASCADE)

    mail_registration = models.ForeignKey(
        TourMail,
        verbose_name=_("Mail Registration"),
        related_name="tours_mail_registration",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    mail_reminder = models.ForeignKey(
        TourMail,
        verbose_name=_("Mail Reminder"),
        related_name="tours_mail_reminder",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    reminder_tour_days_count = models.IntegerField(
        verbose_name=_("Send the reminder-mail automatically this amount of days before the Tour (0=same day)"),
        default=0,
    )

    def __str__(self) -> str:
        return f"Tour-Settings for {self.semester}"
