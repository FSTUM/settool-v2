from __future__ import unicode_literals

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.core.mail import send_mail
from django.template import engines
from django.contrib.auth.models import User
from django.utils import timezone

#from django_mailman.models import List

from settool_common.models import Semester, Subject, current_semester


MAILINGLIST_NAME = 'setfahrt-teilnehmer'
MAILINGLIST_DOMAIN = 'fs.tum.de'


class Fahrt(models.Model):
    semester = models.OneToOneField(
        Semester,
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
        return (self.open_registration < timezone.now() and
                timezone.now() < self.close_registration)


class Participant(models.Model):
    class Meta:
        permissions = (("view_participants",
            "Can view and edit the list of participants"),)

    semester = models.ForeignKey(
        Semester,
        related_name="fahrt_participant",
    )

    gender = models.CharField(
        _("Gender"),
        max_length=200,
        choices=(("male", _("male")), ("female", _("female"))),
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
        _("Places in my car"),
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
    def u18(self):
        return not (
            self.semester.fahrt.date.year - self.birthday.year > 18 or (
            self.semester.fahrt.date.year - self.birthday.year == 18 and (
            self.semester.fahrt.date.month > self.birthday.month or (
            self.semester.fahrt.date.month == self.birthday.month and
            self.semester.fahrt.date.day >= self.birthday.day))))


    def toggle_mailinglist(self):
        list_name = 'setfahrt-teilnehmer'
        list_pwd = 'codioguhup'
        list_email = 'setfahrt-teilnehmer@fs.tum.de'
        list_url = 'https://mail.fs.tum.de/listenadmin'
        list_encoding = 'iso-8859-1'

        mailinglist = List(
            name=list_name,
            password=list_pwd,
            email=list_email,
            main_url=list_url,
            encoding=list_encoding,
        )

        members = mailinglist.get_all_members()
        print(members)
        members = [m[0] for m in members]
        if self.mailinglist:
            if self.email not in members:
                mailinglist.subscribe(self.email, self.firstname,
                    self.surname)
        else:
            if self.email in members:
                mailinglist.unsubscribe(self.email)

        #if self.mailinglist:
        #    to_email = MAILINGLIST_NAME + "-join@" + MAILINGLIST_DOMAIN
        #else:
        #    to_email = MAILINGLIST_NAME + "-leave@" + MAILINGLIST_DOMAIN
        #send_mail("", "", self.email, [to_email], fail_silently=False)


class Mail(models.Model):
    FROM_MAIL = "SET-Fahrt-Team <setfahrt@fs.tum.de>"
    semester = models.ForeignKey(
        Semester,
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
            return "{} ({})". format(self.subject, self.comment)
        else:
            return str(self.subject)

    def get_mail(self, request):
        django_engine = engines['django']
        subject_template = django_engine.from_string(self.subject)
        context = {
            'vorname': "<Vorname>",
            'frist': "<Zahlungsfrist>",
        }
        subject = subject_template.render(context).rstrip()

        text_template = django_engine.from_string(self.text)
        text = text_template.render(context)

        return (subject, text, Mail.FROM_MAIL)

    def send_mail(self, request, participant):
        django_engine = engines['django']
        subject_template = django_engine.from_string(self.subject)
        context = {
            'vorname': participant.firstname,
            'frist': participant.payment_deadline,
        }
        subject = subject_template.render(context).rstrip()

        text_template = django_engine.from_string(self.text)
        text = text_template.render(context)

        send_mail(subject, text, Mail.FROM_MAIL, [participant.email],
            fail_silently=False)


class LogEntry(models.Model):
    participant = models.ForeignKey(
        Participant,
    )

    user = models.ForeignKey(
        User,
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
