from django.db import models
from django.utils.translation import ugettext_lazy as _

from settool_common.models import Semester

class Tour(models.Model):
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

    def __str__(self):
        return self.name

class Participant(models.Model):
    tour = models.ForeignKey(
        Tour
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

    def __str__(self):
        return "{} {}".format(self.firstname, self.surname)
