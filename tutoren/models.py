from __future__ import unicode_literals
import uuid

from django.db import models
from django.core.validators import RegexValidator
from django.utils.translation import ugettext_lazy as _

from settool_common.models import Semester, Subject
from settool_common.utils import u


class Status(models.Model):
    name = models.CharField(
        _("Status name"),
        max_length = 30,
    )

    default_status = models.BooleanField(
        _("Default status"),
    )

    def __str__(self):
        return u(self.name)


def get_default_status():
    default = Status.objects.filter(default_status=True).order_by('pk').first()
    if default:
        return default.pk
    else:
        return 1


class Tutor(models.Model):
    TSHIRT_SIZES = (
        ('S', 'S'),
        ('M', 'M'),
        ('L', 'L'),
        ('XL', 'XL'),
        ('XXL', 'XXL')
    )

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    semester = models.OneToOneField(
        Semester,
        editable=False,
        verbose_name=_("Semester"),
        on_delete=models.CASCADE,
    )

    first_name = models.CharField(
        _("First name"),
        max_length=30,
    )

    last_name = models.CharField(
        _("Last name"),
        max_length=50,
    )

    email = models.EmailField(
        _("Email address"),
    )

    registration_time = models.DateTimeField(
        _("Registration Time"),
        auto_now_add=True,
    )

    birthday = models.DateField(
        _("Birthday"),
    )

    matriculation_number = models.CharField(
        _("Matriculation number"),
        max_length=8,
        validators=[RegexValidator(
            r'^[0-9]{8,8}$',
            message=_('The matriculation number has to be of the form ' \
                '01234567.'),
        )],
    )

    tshirt_size = models.CharField(
        _("Tshirt size"),
        max_length=5,
        choices=TSHIRT_SIZES,
    )

    tshirt_girls_cut = models.BooleanField(
        _("Tshirt as Girls cut"),
    )

    status = models.ForeignKey(
        Status,
        on_delete=models.SET_DEFAULT,
        verbose_name=_("Status"),
        default=get_default_status,
    )

    subject = models.ForeignKey(
        Subject,
        verbose_name=_("Subject"),
        on_delete=models.CASCADE,
    )

    minor_subject = models.CharField(
        _("Minor subject"),
        max_length=30,
    )

    def __str__(self):
        return "{0} {1}".format(u(self.first_name), u(self.last_name))
