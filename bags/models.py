# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from django.utils.translation import ugettext_lazy as _
from django.template import engines
from django.db import models
from django.core.mail import send_mail

from settool_common.models import Semester, current_semester

class Company(models.Model):
    class Meta:
        permissions = (("view_companies",
            "Can view and edit the companies"),)

    semester = models.ForeignKey(
        Semester
    )

    name = models.CharField(
        _("Name"),
        max_length=200,
    )

    contact = models.CharField(
        _("Contact person"),
        max_length=200,
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


class Mail(models.Model):
    FROM_MAIL = "Erstitüten-Team des SET-Referats <set-tueten@fs.tum.de>"
    semester = models.ForeignKey(
        Semester,
        default=current_semester().pk,
    )

    subject = models.CharField(
        _("Email subject"),
        max_length=200,
    )

    text = models.TextField(
        _("Text"),
    )

    comment = models.CharField(
        _("Comment"),
        max_length=200,
    )

    def __str__(self):
        if self.comment:
            return "{} ({})". format(self.subject, self.comment)
        else:
            return str(self.subject)

    def send_mail(self, request, company):
        # text from templates
        django_engine = engines['django']
        subject_template = django_engine.from_string(self.subject)
        subject = subject_template.render({'company': company}).rstrip()

        text_template = django_engine.from_string(self.text)
        text = text_template.render({'company': company})

        # send
        send_mail(subject, text, Mail.FROM_MAIL,
            ["{0} <{1}>".format(company.contact, company.email)],
            fail_silently=False)

