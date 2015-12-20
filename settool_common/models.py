from django.db import models
from django.utils.translation import ugettext_lazy as _

class Semester(models.Model):
    class Meta:
        unique_together = (('semester', 'year'),)
        ordering = ['year', 'semester']

    WINTER = 'WS'
    SUMMER = 'SS'
    SEMESTER_CHOICES = (
        (WINTER, _('Winter semester')),
        (SUMMER, _('Summer semester')),
    )

    semester = models.CharField(
        max_length=2,
        choices=SEMESTER_CHOICES,
        default=WINTER,
        verbose_name=_("Semester"),
    )

    year = models.PositiveIntegerField(
        verbose_name=_("Year"),
    )

    def __str__(self):
        return "{} {:4}".format(self.get_semester_display(), self.year)
