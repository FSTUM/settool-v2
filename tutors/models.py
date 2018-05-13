from __future__ import unicode_literals

import uuid

from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from common.models import Semester, Subject
from common.utils import u


class Registration(models.Model):
    semester = models.OneToOneField(
        Semester,
        on_delete=None
    )

    open_registration = models.DateTimeField(
        _("Open registration"),
    )

    close_registration = models.DateTimeField(
        _("Close registration"),
    )

    def registration_open(self):
        return self.open_registration < timezone.now() < self.close_registration


class Status(models.Model):
    key = models.CharField(
        _("Key name"),
        max_length=30,
        unique=True,
    )

    name = models.CharField(
        _("Status name"),
        max_length=30,
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
    class Meta:
        unique_together = ('semester', 'email',)

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
        editable=False,
    )

    semester = models.ForeignKey(
        Semester,
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
            message=_('The matriculation number has to be of the form 01234567.'),
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

    comment = models.TextField(
        _("Comment"),
        max_length=500,
        blank=True,
    )

    def __str__(self):
        return "{0} {1}".format(u(self.first_name), u(self.last_name))

    def log(self, user, text):
        # LogEntry.objects.create(
        #     participant=self,
        #     user=user,
        #     text=text,
        # )
        pass


class Event(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    semester = models.ForeignKey(
        Semester,
        verbose_name=_("Semester"),
        on_delete=models.CASCADE,
    )

    name = models.CharField(
        _("Name"),
        max_length=20,
    )

    description = models.TextField(
        _("Description"),
    )

    begin = models.DateTimeField(
        _("Begin"),
    )
    end = models.DateTimeField(
        _("End"),
    )

    meeting_point = models.CharField(
        _("Meeting Point"),
        max_length=200,
    )

    subjects = models.ManyToManyField(
        Subject,
        verbose_name=_("Subjects"),
        blank=True,
    )

    def log(self, user, text):
        # LogEntry.objects.create(
        #     participant=self,
        #     user=user,
        #     text=text,
        # )
        pass

    def __str__(self):
        return "{0} {1}".format(u(self.name), u(self.begin.date()))


class Task(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    semester = models.ForeignKey(
        Semester,
        verbose_name=_("Semester"),
        on_delete=models.CASCADE,
    )

    name = models.CharField(
        _("Task name"),
        max_length=50,
    )

    description = models.TextField(
        _("Description"),
    )

    begin = models.DateTimeField(
        _("Begin"),
    )

    end = models.DateTimeField(
        _("End"),
    )

    meeting_point = models.CharField(
        _("Meeting point"),
        max_length=50,
    )

    event = models.ForeignKey(
        Event,
        verbose_name=_("Event"),
        on_delete=models.CASCADE,
    )

    allowed_subjects = models.ManyToManyField(
        Subject,
        verbose_name=_("Allowed Subjects"),
        blank=True,
    )

    requirements = models.ManyToManyField(
        'Question',
        verbose_name=_("Requirements"),
        blank=True,
    )

    min_tutors = models.IntegerField(
        _('Tutors (min)'),
        blank=True,
    )

    max_tutors = models.IntegerField(
        _('Tutors (max)'),
        blank=True,
    )

    tutors = models.ManyToManyField(
        Tutor,
        verbose_name=_("Assigned tutors"),
        through='TutorAssignment',
        blank=True,
    )

    def __str__(self):
        return u(self.name)

    def log(self, user, text):
        # LogEntry.objects.create(
        #     participant=self,
        #     user=user,
        #     text=text,
        # )
        pass


class TutorAssignment(models.Model):
    class Meta:
        auto_created = True

    tutor = models.ForeignKey(
        Tutor,
        on_delete=models.CASCADE,
    )

    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
    )

    absent = models.BooleanField(
        _("absent"),
        default=False,
    )

    def __str__(self):
        return "{}".format(self.tutor)


class Question(models.Model):
    question = models.CharField(
        _("Question"),
        max_length=100,
    )

    answers = models.ManyToManyField(
        Tutor,
        verbose_name=_("Assigned tutors"),
        through='Answer',
        blank=True,
    )

    def __str__(self):
        return u(self.question)


class Answer(models.Model):
    YES = 'YES'
    NO = 'NO'
    MAYBE = 'MAYBE'
    ANSWERS = (
        (YES, _("yes")),
        (MAYBE, _("if need be")),
        (NO, _("no")),
    )

    tutor = models.ForeignKey(
        Tutor,
        on_delete=models.CASCADE,
    )

    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
    )

    answer = models.CharField(
        _("Answer"),
        max_length=10,
        blank=True,
        choices=ANSWERS,
    )

    def __str__(self):
        return "{}: {} -> {}".format(self.tutor, self.question, u(self.answer))


class Requirement(models.Model):
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
    )

    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
    )

    inverse = models.BooleanField(
        _("inverse answer"),
    )

    def __str__(self):
        return "{}: {}".format(self.task, self.question)
