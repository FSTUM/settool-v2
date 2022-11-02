import datetime

from dateutil.relativedelta import relativedelta
from django.contrib.auth import get_user_model
from django.db import models
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_tex.response import PDFResponse
from django_tex.shortcuts import render_to_pdf

import settool_common.models as common_models
from settool_common.models import Semester, Subject

ANNONIMISATION_GRACEPERIOD_AFTER_FAHRT = relativedelta(weeks=6)


class FahrtMail(common_models.Mail):
    # ["{{template}}", "description"]
    general_placeholders = [
        ("{{vorname}}", _("The participant's first name")),
        ("{{frist}}", _("The individual payment deadline")),
        ("{{participant}}", _("The participant")),
    ]
    # ["{{template}}", "description", "contition"]
    conditional_placeholders: list[tuple[str, str, str]] = []
    notes = _(
        "If the Email is configured as the fahrt's registration mail, the participants' personalised non-liability "
        "form is automatically attached. Please notify the Participant to atach his ID "
        "(THIS-->{{ participant.id }}<--THIS) in the Payment-Subject-Line.",
    )

    required_perm = common_models.Mail.required_perm + ["fahrt.view_participants"]

    # pylint: disable=signature-differs
    def save(self, *args, **kwargs):
        self.sender = common_models.Mail.SET_FAHRT
        super().save(*args, **kwargs)

    def send_mail_participant(self, participant: "Participant") -> bool:
        context = {
            "vorname": participant.firstname,
            "frist": participant.payment_deadline,
            "participant": participant,
        }
        return self.send_mail(context, participant.email)

    def send_mail_registration(self, participant: "Participant", non_liability: HttpResponse) -> bool:
        context = {
            "vorname": participant.firstname,
            "frist": participant.payment_deadline,
            "participant": participant,
        }
        return self.send_mail(context, participant.email, attachments=[non_liability])

    def get_mail_participant(self) -> tuple[str, str, str]:
        context = {
            "vorname": "<Vorname>",
            "frist": "<Zahlungsfrist>",
            "participant": "<participant>",
        }
        return self.get_mail(context)


class Fahrt(common_models.LoggedModelBase):
    semester = models.OneToOneField(Semester, on_delete=models.CASCADE)

    date = models.DateField(_("Date"))
    open_registration = models.DateTimeField(_("Open registration"))
    close_registration = models.DateTimeField(_("Close registration"))

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

    def __str__(self) -> str:
        return f"Fahrt {self.semester} at {self.date}"

    @property
    def registration_open(self):
        return self.open_registration < timezone.now() < self.close_registration


class Transportation(common_models.LoggedModelBase):
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

    fahrt = models.ForeignKey(Fahrt, on_delete=models.CASCADE)

    deparure_time = models.DateTimeField(
        _("Planned time of departure for the trip (leave blank if you dont have a preferance)"),
        null=True,
        blank=True,
    )

    return_departure_time = models.DateTimeField(
        _("Planned time of departure for the return-trip (leave blank if you dont have a preferance)"),
        null=True,
        blank=True,
    )

    departure_place = models.CharField(_("The place we will start our trip"), max_length=100, blank=True)

    places = models.PositiveSmallIntegerField(
        _("Number of people (totally) for this mode of transport"),
        default=1,
    )

    def __str__(self) -> str:
        free_places = self.places - self.participant_set.count()
        if self.transport_type:
            return _("Train ({free_places} free)").format(free_places=free_places)
        return _("Car ({free_places} free)").format(free_places=free_places)


class Participant(common_models.UUIDModelBase, common_models.LoggedModelBase, common_models.SemesterModelBase):
    class Meta:
        permissions = (
            (
                "view_participants",
                "Can view and edit the list of participants",
            ),
        )

    registration_time = models.DateTimeField(_("Registration time"), auto_now_add=True)

    GENDER_CHOICES = (
        ("male", _("male")),
        ("female", _("female")),
        ("diverse", _("diverse")),
    )
    gender = models.CharField(_("Gender"), max_length=200, choices=GENDER_CHOICES)
    firstname = models.CharField(_("First name"), max_length=200)
    surname = models.CharField(_("Surname"), max_length=200)
    birthday = models.DateField(_("Birthday"))
    email = models.EmailField(_("Email address"))
    phone = models.CharField(_("Phone"), max_length=200, blank=True)
    mobile = models.CharField(_("Mobile phone"), max_length=200, blank=True)
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        verbose_name=_("Subject"),
        related_name="fahrt_participant",
    )
    NUTRITION_CHOICES = (
        ("normal", _("normal")),
        ("vegeterian", _("vegeterian")),
        ("vegan", _("vegan")),
    )
    nutrition = models.CharField(_("Nutrition"), max_length=200, choices=NUTRITION_CHOICES)
    allergies = models.CharField(_("Allergies"), max_length=200, blank=True)

    transportation = models.ForeignKey(Transportation, on_delete=models.SET_NULL, blank=True, null=True)
    publish_contact_to_other_paricipants = models.BooleanField(
        _("Publish your most relevant (mobile > phone > email), contact-info to other Fahrt-participants."),
        default=False,
    )

    non_liability = models.DateField(_("Non-liability submitted"), blank=True, null=True)
    paid = models.DateField(_("Paid"), blank=True, null=True)
    payment_deadline = models.DateField(_("Payment deadline"), blank=True, null=True)

    STATUS_REGISTERED = "registered"
    STATUS_CONFIRMED = "confirmed"
    STATUS_WAITINGLIST = "waitinglist"
    STATUS_CANCELED = "cancelled"
    status = models.CharField(
        _("Status"),
        max_length=200,
        choices=(
            (STATUS_REGISTERED, _("registered")),
            (STATUS_CONFIRMED, _("confirmed")),
            (STATUS_WAITINGLIST, _("waitinglist")),
            (STATUS_CANCELED, _("cancelled")),
        ),
        default="registered",
    )

    mailinglist = models.BooleanField(_("Mailing list"), default=False)

    comment = models.CharField(_("Comment"), max_length=400, blank=True)

    def __str__(self) -> str:
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

    def get_non_liability(self) -> PDFResponse:
        fahrt: Fahrt = get_object_or_404(Fahrt, semester=self.semester)
        context = {
            "participant": self,
            "fahrt": fahrt,
        }
        filename = f"non_liability_{self.surname}_{self.firstname}.pdf"
        # first param is not needed and only included to make the signature conform to django's render function
        if self.u18:
            return render_to_pdf({}, "fahrt/tex/u18_non_liability.tex", context, filename)
        return render_to_pdf({}, "fahrt/tex/ü18_non_liability.tex", context, filename)

    def toggle_mailinglist(self) -> None:
        self.mailinglist = not self.mailinglist
        self.save()

    # def set_payment_deadline(self, weeks):
    #    today = date.today()
    #    delta = timedelta(days=weeks*7)
    #    deadline = today + delta
    #    self.payment_deadline = deadline.strftime("%d.%m.%Y")


class TransportationComment(common_models.LoggedModelBase):
    sender = models.ForeignKey(Participant, on_delete=models.CASCADE)
    commented_on = models.ForeignKey(Transportation, on_delete=models.CASCADE)
    comment_content = models.CharField(_("Text"), max_length=200)

    def __str__(self) -> str:
        if len(self.comment_content) > 30:
            comment_content = self.comment_content[:30] + "..."
        else:
            comment_content = self.comment_content
        return _("{sender} on {commented_on}: {comment_content}").format(
            sender=self.sender,
            commented_on=self.commented_on,
            comment_content=comment_content,
        )


class LogEntry(common_models.LoggedModelBase):
    time = models.DateTimeField(_("Time"), auto_now_add=True)
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE)
    text = models.CharField(_("Text"), max_length=200)
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name="mylogentry_set",
        blank=True,
        null=True,
    )

    def __str__(self) -> str:
        return f"{self.time}, {self.user}: {self.text}"
