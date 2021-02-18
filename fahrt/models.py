import datetime
from typing import List, Tuple

from dateutil.relativedelta import relativedelta
from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

import settool_common.models as common_models
from settool_common.models import Semester, Subject


class FahrtMail(common_models.Mail):
    # ["{{template}}", "description"]
    general_placeholders = [
        ("{{vorname}}", _("The participant's first name")),
        ("{{frist}}", _("The individual payment deadline")),
        ("{{participant}}", _("The participant")),
    ]
    # ["{{template}}", "description", "contition"]
    conditional_placeholders: List[Tuple[str, str, str]] = []
    notes = _(
        "If the Email is configured as the fahrt's registration mail, the participants' personalised non-liability "
        "form is automatically attached",
    )

    required_perm = common_models.Mail.required_perm + ["fahrt.view_participants"]

    # pylint: disable=signature-differs
    def save(self, *args, **kwargs):
        self.sender = common_models.Mail.SET_FAHRT
        super().save(*args, **kwargs)

    def send_mail_participant(self, participant):
        context = {
            "vorname": participant.firstname,
            "frist": participant.payment_deadline,
            "participant": participant,
        }
        return self.send_mail(context, participant.email)

    def send_mail_registration(self, participant, non_liability):
        context = {
            "vorname": participant.firstname,
            "frist": participant.payment_deadline,
            "participant": participant,
        }
        return self.send_mail(context, participant.email, attachments=[non_liability])

    def get_mail_participant(self):
        context = {
            "vorname": "<Vorname>",
            "frist": "<Zahlungsfrist>",
            "participant": "<participant>",
        }
        return self.get_mail(context)


class Fahrt(models.Model):
    semester = models.OneToOneField(
        Semester,
        on_delete=models.CASCADE,
    )

    date = models.DateField(
        _("Date"),
    )

    open_registration = models.DateTimeField(
        _("Open registration"),
    )

    close_registration = models.DateTimeField(
        _("Close registration"),
    )

    mail_registration = models.ForeignKey(
        FahrtMail,
        verbose_name=_("Mail Registration"),
        related_name="fahrt_mail_registration",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )

    mail_reminder = models.ForeignKey(
        FahrtMail,
        verbose_name=_("Mail Reminder"),
        related_name="fahrt_mail_reminder",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    reminder_tour_days_count = models.IntegerField(
        verbose_name=_("Send the Reminder-mail automatically this amount of days before the Fahrt (0=same day)"),
        default=0,
    )

    mail_payment_deadline = models.ForeignKey(
        FahrtMail,
        verbose_name=_("Mail Payment-Deadline Reminder"),
        related_name="fahrt_mail_payment_deadline",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    reminder_payment_deadline_days_count = models.IntegerField(
        verbose_name=_(
            "Send the Payment-Deadline Reminder-mail automatically this amount of days before the Deadline "
            "(0=same day)",
        ),
        default=0,
    )

    def __str__(self):
        return f"Fahrt {self.semester} at {self.date}"

    @property
    def registration_open(self):
        return self.open_registration < timezone.now() < self.close_registration


class Transportation(models.Model):
    CAR = 0
    TRAIN = 1

    transport_type = models.PositiveSmallIntegerField(
        _("Type of Transport"),
        choices=(
            (CAR, _("Car")),
            (TRAIN, _("Train")),
        ),
    )

    creator = models.OneToOneField(
        "Participant",
        on_delete=models.SET_NULL,
        related_name="fahrt_transportation_creator",
        null=True,
    )

    fahrt = models.ForeignKey(
        Semester,
        on_delete=models.CASCADE,
        related_name="fahrt_transportation",
    )

    places = models.PositiveSmallIntegerField(
        _("Number of people (totally) for this mode of transport"),
        default=1,
    )


class Participant(models.Model):
    class Meta:
        permissions = (
            (
                "view_participants",
                "Can view and edit the list of participants",
            ),
        )

    GENDER_CHOICES = (
        ("male", _("male")),
        ("female", _("female")),
        ("diverse", _("diverse")),
    )

    semester = models.ForeignKey(
        Semester,
        on_delete=models.CASCADE,
        related_name="fahrt_participant",
    )

    gender = models.CharField(
        _("Gender"),
        max_length=200,
        choices=GENDER_CHOICES,
    )

    firstname = models.CharField(
        _("First name"),
        max_length=200,
    )

    surname = models.CharField(
        _("Surname"),
        max_length=200,
    )

    birthday = models.DateField(
        _("Birthday"),
    )

    email = models.EmailField(
        _("Email address"),
    )

    phone = models.CharField(
        _("Phone"),
        max_length=200,
        blank=True,
    )

    mobile = models.CharField(
        _("Mobile phone"),
        max_length=200,
        blank=True,
    )

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        verbose_name=_("Subject"),
        related_name="fahrt_participant",
    )

    nutrition = models.CharField(
        _("Nutrition"),
        max_length=200,
        choices=(
            ("normal", _("normal")),
            ("vegeterian", _("vegeterian")),
            ("vegan", _("vegan")),
        ),
    )

    allergies = models.CharField(
        _("Allergies"),
        max_length=200,
        blank=True,
    )

    transportation = models.ForeignKey(
        Transportation,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )

    non_liability = models.DateField(
        _("Non-liability submitted"),
        blank=True,
        null=True,
    )

    paid = models.DateField(
        _("Paid"),
        blank=True,
        null=True,
    )

    payment_deadline = models.DateField(
        _("Payment deadline"),
        blank=True,
        null=True,
    )

    status = models.CharField(
        _("Status"),
        max_length=200,
        choices=(
            ("registered", _("registered")),
            ("confirmed", _("confirmed")),
            ("waitinglist", _("waitinglist")),
            ("cancelled", _("cancelled")),
        ),
        default="registered",
    )

    mailinglist = models.BooleanField(
        _("Mailing list"),
        default=False,
    )

    comment = models.CharField(
        _("Comment"),
        max_length=400,
        blank=True,
    )

    registration_time = models.DateTimeField(
        _("Registration time"),
        auto_now_add=True,
    )

    def __str__(self):
        return f"{self.firstname} {self.surname}"

    def log(self, user, text):
        LogEntry.objects.create(
            participant=self,
            user=user,
            text=text,
        )

    @property
    def u18(self) -> bool:
        return relativedelta(self.semester.fahrt.date, self.birthday).years < 18

    @property
    def deadline_exceeded(self) -> bool:
        if not self.payment_deadline:
            return False
        return self.payment_deadline < datetime.date.today()

    @property
    def deadline_soon(self) -> bool:
        if not self.payment_deadline:
            return False
        return self.payment_deadline < datetime.date.today() + datetime.timedelta(days=7)

    def toggle_mailinglist(self) -> None:
        self.mailinglist = not self.mailinglist
        self.save()

    # def set_payment_deadline(self, weeks):
    #    today = date.today()
    #    delta = timedelta(days=weeks*7)
    #    deadline = today + delta
    #    self.payment_deadline = deadline.strftime("%d.%m.%Y")


class TransportationComment(models.Model):
    sender = models.ForeignKey(
        Participant,
        on_delete=models.CASCADE,
    )

    commented_on = models.ForeignKey(
        Transportation,
        on_delete=models.CASCADE,
    )

    comment_content = models.CharField(
        _("Text"),
        max_length=200,
    )

    def log(self, user, text):
        LogEntry.objects.create(
            participant=self.sender,
            user=user,
            text=text,
        )


class LogEntry(models.Model):
    participant = models.ForeignKey(
        Participant,
        on_delete=models.CASCADE,
    )

    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name="mylogentry_set",
        blank=True,
        null=True,
    )

    text = models.CharField(
        _("Text"),
        max_length=200,
    )

    time = models.DateTimeField(
        _("Time"),
        auto_now_add=True,
    )

    def __str__(self):
        return f"{self.time}, {self.user}: {self.text}"
