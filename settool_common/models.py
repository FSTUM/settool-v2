import datetime

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone

from .settings import SEMESTER_SESSION_KEY

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

class Subject(models.Model):
    class Meta:
        unique_together = (('degree', 'subject'),)
        ordering = ['degree', 'subject']

    BACHELOR = 'BA'
    MASTER = 'MA'
    DEGREE_CHOICES = (
        (BACHELOR, _('Bachelor')),
        (MASTER, _('Master')),
    )

    MATHEMATICS = 'Mathe'
    PHYSICS = 'Physik'
    INFORMATICS = 'Info'
    GAMES_ENGINEERING = 'Games'
    INFORMATION_SYSTEMS = 'Winfo'
    ASE = 'ASE'
    CSE = 'CSE'
    BMC = 'BMC'
    ROBOTICS = 'Robotics'
    OPERATIONS_RESEARCH = 'Mathe OR'
    SCIENCE_ENGINEERING = 'Mathe SE'
    FINANCE = 'Mathe Finance'
    BIOMATHE = 'Mathe Bio'

    SUBJECT_CHOICES = (
        (MATHEMATICS, _('Mathematics')),
        (PHYSICS, _('Physics')),
        (INFORMATICS, _('Informatics')),
        (GAMES_ENGINEERING, _('Informatics: Games Engineering')),
        (INFORMATION_SYSTEMS, _('Information Systems')),
        (ASE, _('Automotive Software Engineering')),
        (CSE, _('Computational Science and Engineering')),
        (BMC, _('Biomedical Computing')),
        (ROBOTICS, _('Robotics, Cognition, Intelligence')),
        (OPERATIONS_RESEARCH, _('Mathematics in Operatios Research')),
        (SCIENCE_ENGINEERING, _('Mathematics in Science and Engineering')),
        (FINANCE, _('Mathematics in Finance and Acturial Science')),
        (BIOMATHE, _('Mathematics in Bioscience')),
    )


    degree = models.CharField(
        max_length=2,
        choices=DEGREE_CHOICES,
        default=BACHELOR,
        verbose_name=_("Degree"),
    )

    subject = models.CharField(
        max_length=20,
        choices=SUBJECT_CHOICES,
        default=INFORMATICS,
        verbose_name=_("Subject"),
    )

    def __str__(self):
        return "{} {}".format(self.get_degree_display(),
                self.get_subject_display())

def current_semester():
    now = timezone.now()
    year = now.year
    if now < timezone.make_aware(datetime.datetime(year, 5, 1)):
        semester = Semester.SUMMER
    elif now >= timezone.make_aware(datetime.datetime(year, 11, 1)):
        semester = Semester.SUMMER
        year += 1
    else:
        semester = Semester.WINTER
    return Semester.objects.get_or_create(semester=semester, year=year)[0]


def get_semester(request):
    try:
        sem = request.session[SEMESTER_SESSION_KEY]
    except KeyError:
        sem = current_semester().pk
        request.session[SEMESTER_SESSION_KEY] = sem
    return sem

