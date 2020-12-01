from __future__ import unicode_literals

import datetime

from dateutil.relativedelta import relativedelta
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db import models
from django.template import engines
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from settool_common.models import Semester, Subject


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

    @property
    def registration_open(self):
        return self.open_registration < timezone.now() < self.close_registration


class Participant(models.Model):
    class Meta:
        permissions = (("view_participants",
                        "Can view and edit the list of participants"),)

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
        choices=(("normal", _("normal")), ("vegeterian", _("vegeterian")),
                 ("vegan", _("vegan"))),
    )

    allergies = models.CharField(
        _("Allergies"),
        max_length=200,
        blank=True,
    )

    car = models.BooleanField(
        _("Drive by car"),
    )

    car_places = models.IntegerField(
        _("Number of people I can take along additionally"),
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
            ("cancelled", _("cancelled"))
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
        return "{0} {1}".format(self.firstname, self.surname)

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

    def toggle_mailinglist(self):
        pass  # not implemented

    # def set_payment_deadline(self, weeks):
    #    today = date.today()
    #    delta = timedelta(days=weeks*7)
    #    deadline = today + delta
    #    print(deadline.strftime("%d.%m.%Y")
    #    self.payment_deadline = deadline.strftime("%d.%m.%Y")


class Mail(models.Model):
    FROM_MAIL = "SET-Fahrt-Team <setfahrt@fs.tum.de>"
    semester = models.ForeignKey(
        Semester,
        on_delete=models.CASCADE,
        related_name="fahrt_mail_set",
    )

    subject = models.CharField(
        _("Email subject"),
        max_length=200,
    )

    text = models.TextField(
        _("Text"),
        help_text=_("You may use {{vorname}} for the participant's first \
name and {{frist}} for the individual payment deadline."),
    )

    comment = models.CharField(
        _("Comment"),
        max_length=200,
        blank=True,
    )

    def __str__(self):
        if self.comment:
            return "{} ({})".format(self.subject, self.comment)
        return str(self.subject)

    def get_mail(self):
        django_engine = engines['django']
        subject_template = django_engine.from_string(self.subject)
        context = {
            'vorname': "<Vorname>",
            'frist': "<Zahlungsfrist>",
        }
        subject = subject_template.render(context).rstrip()

        text_template = django_engine.from_string(self.text)
        text = text_template.render(context)

        return subject, text, Mail.FROM_MAIL

    def send_mail(self, participant):
        django_engine = engines['django']
        context = {
            'vorname': participant.firstname,
            'frist': participant.payment_deadline,
        }

        subject_template = django_engine.from_string(self.subject)
        subject = subject_template.render(context).rstrip()

        text_template = django_engine.from_string(self.text)
        text = text_template.render(context)

        if context['frist'] is None and ("{{frist}}" in self.text or "{{frist}}" in self.subject):
            return False
        send_mail(subject, text, Mail.FROM_MAIL, [participant.email], fail_silently=False)
        return True


class LogEntry(models.Model):
    participant = models.ForeignKey(
        Participant,
        on_delete=models.CASCADE,
    )

    user = models.ForeignKey(
        User,
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
        return "{0}, {1}: {2}".format(self.time, self.user, self.text)
