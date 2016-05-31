from __future__ import unicode_literals
from django.utils.translation import ugettext_lazy as _

from django.db import models

from settool_common.models import Semester

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

