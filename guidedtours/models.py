from django.db import models
from django.utils.translation import ugettext_lazy as _

from settool_common.models import Semester, Subject

class Tour(models.Model):
    class Meta:
        permissions = (("view_participants",
            "Can view and edit the list of participants"),)

    semester = models.ForeignKey(
        Semester
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

    def __str__(self):
        return self.name

class Participant(models.Model):
    tour = models.ForeignKey(
        Tour,
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
        verbose_name=_("Subject"),
    )

    time = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Registration Time"),
    )

    def __str__(self):
        return "{} {}".format(self.firstname, self.surname)


class Mail(models.Model):
    FROM_MAIL = "SET-Referat <set@fs.tum.de>"
    semester = models.ForeignKey(
        Semester,
        related_name="tours_mail_set",
    )

    subject = models.CharField(
        _("Email subject"),
        max_length=200,
    )

    text = models.TextField(
        _("Text"),
        help_text=_("You may use {{vorname}} for the participant's first name."),
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
        }
        subject = subject_template.render(context).rstrip()

        text_template = django_engine.from_string(self.text)
        text = text_template.render(context)

        send_mail(subject, text, Mail.FROM_MAIL, [participant.email],
            fail_silently=False)


