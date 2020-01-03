# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.core.mail import send_mail
from django.db import models
from django.template import engines
from django.utils import encoding
from django.utils.translation import ugettext_lazy as _

from settool_common.models import Semester
from settool_common.utils import u


class Company(models.Model):
    class Meta:
        permissions = (("view_companies",
                        "Can view and edit the companies"),)

    semester = models.ForeignKey(
        Semester,
        on_delete=models.CASCADE,
    )

    name = models.CharField(
        _("Name"),
        max_length=200,
    )

    contact_gender = models.CharField(
        _("Contact person (Gender)"),
        max_length=200,
        choices=(("Herr", _("Herr")), ("Frau", _("Frau"))),
        blank=True,
    )

    contact_firstname = models.CharField(
        _("Contact person (First Name)"),
        max_length=200,
        blank=True,
    )

    contact_lastname = models.CharField(
        _("Contact person (Last Name)"),
        max_length=200,
        blank=True,
    )

    email = models.EmailField(
        _("Email address"),
    )

    email_sent = models.BooleanField(
        _("Email sent"),
    )

    email_sent_success = models.BooleanField(
        _("Email successfully sent"),
    )

    promise = models.NullBooleanField(
        _("Promise"),
    )

    giveaways = models.CharField(
        _("Giveaways"),
        max_length=200,
        blank=True,
    )

    giveaways_last_year = models.CharField(
        _("Giveaways last year"),
        max_length=200,
        blank=True,
    )

    arrival_time = models.CharField(
        _("Arrival time"),
        max_length=200,
        blank=True,
    )

    comment = models.CharField(
        _("Comment"),
        max_length=200,
        blank=True,
    )

    last_year = models.BooleanField(
        _("Participated last year"),
    )

    arrived = models.BooleanField(
        _("Arrived"),
    )

    contact_again = models.NullBooleanField(
        _("Contact again"),
    )

    def __str__(self):
        return u(self.name)

    @property
    def full_contact(self):
        return "{} {} {}".format(self.contact_gender, self.contact_firstname,
                                 self.contact_lastname)

    @property
    def anrede(self):
        if self.contact_gender and self.contact_lastname:
            return "Hallo {} {}".format(self.contact_gender, self.contact_lastname)
        else:
            return "Sehr geehrte Damen und Herren"

    @property
    def formale_anrede(self):
        if self.contact_gender and self.contact_lastname:
            if self.contact_gender == "Herr":
                return "Sehr geehrter Herr {}".format(self.contact_lastname)
            elif self.contact_gender == "Frau":
                return "Sehr geehrte Frau {}".format(self.contact_lastname)
            else:
                return "Sehr geehrte Damen und Herren"
        else:
            return "Sehr geehrte Damen und Herren"

    @property
    def contact_name(self):
        return "{} {}".format(self.contact_firstname, self.contact_lastname)


#@encoding.python_2_unicode_compatible
class Mail(models.Model):
    FROM_MAIL = 'Sponsoring Team des SET-Referats <set-tueten@fs.tum.de>'
    semester = models.ForeignKey(
        Semester,
        on_delete=models.CASCADE,
    )

    subject = models.CharField(
        _("Email subject"),
        max_length=200,
    )

    text = models.TextField(
        _("Text"),
        help_text=_(
            'You may use {{firma}} for the company name, {{anrede}} for the greeting "Hallo Herr/Frau XYZ" and '
            '{{formale_anrede}} for the formal greeting "Sehr geehrte/r Herr/Frau XYZ".'),
    )

    comment = models.CharField(
        _("Comment"),
        max_length=200,
        blank=True,
    )

    def __str__(self):
        if self.comment:
            return "{} ({})".format(self.subject, self.comment)
        else:
            return u(self.subject)

    def get_mail(self, request):
        # text from templates
        django_engine = engines['django']
        subject_template = django_engine.from_string(self.subject)
        context = {
            'firma': "<Firma>",
            'anrede': "<Hallo Herr/Frau XYZ>",
            'formale_anrede': "<Sehr geehrte/r Herr/Frau XYZ>",
        }
        subject = subject_template.render(context).rstrip()

        text_template = django_engine.from_string(self.text)
        text = text_template.render(context)

        return subject, text, Mail.FROM_MAIL

    def send_mail(self, request, company):
        # text from templates
        django_engine = engines['django']
        subject_template = django_engine.from_string(self.subject)
        context = {
            'firma': company.name,
            'anrede': company.anrede,
            'formale_anrede': company.formale_anrede,
        }
        subject = subject_template.render(context).rstrip()

        text_template = django_engine.from_string(self.text)
        text = text_template.render(context)

        send_mail(subject, text, Mail.FROM_MAIL, [company.email],
                  fail_silently=False)
