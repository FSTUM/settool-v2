from __future__ import unicode_literals

from django.db import models
from django.utils.translation import ugettext_lazy as _

from settool_common.models import Semester, Subject

class Person(models.Model):
    semester = models.ForeignKey(
        Semester,
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
    )

    mailinglist = models.BooleanField(
        _("Mailing list"),
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
