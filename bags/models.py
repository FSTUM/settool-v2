from __future__ import unicode_literals
from django.utils.translation import ugettext_lazy as _

from django.db import models

from settool_common.models import Semester

class Company(models.Model):
    semester = models.ForeignKey(
        Semester
    )

    name = models.CharField(
        max_length=200,
        verbose_name=_("Name"),
    )

    contact = models.CharField(
        max_length=200,
        verbose_name=_("Contact person"),
    )

    email = models.CharField(
        max_length=200,
        verbose_name=_("Email address"),
    )

    email_sent = models.BooleanField(
        _("Email sent"),
    )

    email_sent_success = models.BooleanField(
        _("Email successfully sent"),
    )

    zusage = models.NullBooleanField(
        _("Zusage"),
    )

    giveaways = models.CharField(
        max_length=200,
        verbose_name=_("Giveaways"),
    )

    arrival_time = models.CharField(
        max_length=200,
        verbose_name=_("Arrival time"),
    )

    comment = models.CharField(
        max_length=200,
        verbose_name=_("Comment"),
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

