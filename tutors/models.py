from dateutil.relativedelta import relativedelta
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

import settool_common.models as common_models
from settool_common.models import Semester, Subject

ANNONIMISATION_GRACEPERIOD_AFTER_LAST_TASK = relativedelta(weeks=12)


class TutorMail(common_models.Mail):
    # ["{{template}}", "description"]
    general_placeholders = [
        ("{{tutor}}", "The Tutor"),
    ]
    # ["{{template}}", "description", "contition"]
    conditional_placeholders: list[tuple[str, str, str]] = [
        ("{{activation_url}}", _("The Activation-Link"), _("Configured as the registration mail")),
        ("{{task}}", _("The Task"), _("Configured as the task mail or the reminder")),
    ]
    notes = ""
    required_perm = common_models.Mail.required_perm + ["tutors.edit_tutors"]

    # pylint: disable=signature-differs
    def save(self, *args, **kwargs):
        self.sender = common_models.Mail.SET_TUTOR
        super().save(*args, **kwargs)

    def send_mail_tutor(self, tutor):
        context = {
            "tutor": tutor,
        }
        return self.send_mail(context, tutor.email)

    def send_mail_registration(self, tutor, activation_url):
        context = {
            "tutor": tutor,
            "activation_url": activation_url,
        }
        return self.send_mail(context, tutor.email)

    def send_mail_task(self, tutor, task):
        context = {
            "tutor": tutor,
            "task": task,
        }
        return self.send_mail(context, tutor.email)

    def get_mail_task(self, tutor, task):
        context = {
            "tutor": tutor,
            "task": task,
        }
        return self.get_mail(context)


class Settings(common_models.LoggedModelBase):
    semester = models.OneToOneField(Semester, on_delete=models.CASCADE)

    open_registration = models.DateTimeField(_("Open registration"))
    close_registration = models.DateTimeField(_("Close registration"))
    mail_registration = models.ForeignKey(
        TutorMail,
        verbose_name=_("Mail Registration"),
        related_name="tutors_mail_registration",
        on_delete=models.SET_NULL,  # can be deleted, but can not be ignored in the Settings :)
        null=True,
    )
    mail_confirmed_place = models.ForeignKey(
        TutorMail,
        verbose_name=_("Mail Confirmed Place"),
        related_name="tutors_mail_confirmed_place",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    mail_waiting_list = models.ForeignKey(
        TutorMail,
        verbose_name=_("Mail Waiting List"),
        related_name="tutors_mail_waiting_list",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    mail_declined_place = models.ForeignKey(
        TutorMail,
        verbose_name=_("Mail Declined Place"),
        related_name="tutors_mail_declined_place",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    mail_task = models.ForeignKey(
        TutorMail,
        verbose_name=_("Mail Task"),
        related_name="tutors_mail_task",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    mail_reminder = models.ForeignKey(
        TutorMail,
        verbose_name=_("Mail Reminder"),
        related_name="tutors_mail_reminder",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    reminder_tour_days_count = models.IntegerField(
        verbose_name=_(
            "Send the reminder-mail automatically this amount of days before the beginn of the Task (0=same day)",
        ),
        default=0,
    )

    @property
    def registration_open(self):
        return self.open_registration < timezone.now() < self.close_registration

    def log(self, user, text):
        # LogEntry.objects.create(
        #     participant=self,
        #     user=user,
        #     text=text,
        # )
        pass


class Tutor(common_models.UUIDModelBase, common_models.LoggedModelBase, common_models.SemesterModelBase):
    class Meta:
        unique_together = ("semester", "email")

    first_name = models.CharField(_("First name"), max_length=30)
    last_name = models.CharField(_("Last name"), max_length=50)
    email = models.EmailField(_("Email address"))
    birthday = models.DateField(_("Birthday"), null=True, blank=True)
    subject = models.ForeignKey(Subject, verbose_name=_("Subject"), on_delete=models.CASCADE)
    matriculation_number = models.CharField(
        _("Matriculation number"),
        max_length=8,
        validators=[
            RegexValidator(
                r"^[0-9]{8,8}$",  # noqa: FS003
                message=_("The matriculation number has to be of the form 01234567."),
            ),
        ],
        null=True,
        blank=True,
    )
    ects = models.BooleanField(
        _("I want to receive ECTS for my work as a SET tutor."),
        help_text=_("tutors_ects_agreement"),
        default=False,
    )

    TSHIRT_SIZES = (
        ("S", "S"),
        ("M", "M"),
        ("L", "L"),
        ("XL", "XL"),
        ("XXL", "XXL"),
    )

    tshirt_size = models.CharField(_("Tshirt size"), max_length=5, choices=TSHIRT_SIZES)
    tshirt_girls_cut = models.BooleanField(_("Tshirt as Girls cut"))

    registration_time = models.DateTimeField(_("Registration Time"), auto_now_add=True)

    answers = models.ManyToManyField("Question", verbose_name=_("Tutor Answers"), through="Answer", blank=True)

    STATUS_DECLINED = "declined"
    STATUS_ACCEPTED = "accepted"
    STATUS_INACTIVE = "inactive"
    STATUS_ACTIVE = "active"
    STATUS_EMPLOYEE = "employee"
    STATUS_OPTIONS = (
        (STATUS_ACCEPTED, _(STATUS_ACCEPTED)),
        (STATUS_ACTIVE, _(STATUS_ACTIVE)),
        (STATUS_DECLINED, _(STATUS_DECLINED)),
        (STATUS_INACTIVE, _(STATUS_INACTIVE)),
        (STATUS_EMPLOYEE, _(STATUS_EMPLOYEE)),
    )

    status = models.CharField(verbose_name=_("Status"), default=STATUS_INACTIVE, choices=STATUS_OPTIONS, max_length=100)

    comment = models.TextField(_("Comment"), max_length=500, blank=True)

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def log(self, user, text):
        # LogEntry.objects.create(
        #     participant=self,
        #     user=user,
        #     text=text,
        # )
        pass


class Event(common_models.UUIDModelBase, common_models.LoggedModelBase, common_models.SemesterModelBase):
    name = models.CharField(_("Name"), max_length=250)
    description = models.TextField(_("Description"), blank=True)
    begin = models.DateTimeField(_("Begin"))
    end = models.DateTimeField(_("End"))
    meeting_point = models.CharField(_("Meeting Point"), max_length=200)

    subjects = models.ManyToManyField(Subject, verbose_name=_("Subjects"), blank=True)

    def log(self, user, text):
        # LogEntry.objects.create(
        #     participant=self,
        #     user=user,
        #     text=text,
        # )
        pass

    def __str__(self) -> str:
        return f"{self.name} {self.begin.date()}"


class Task(common_models.UUIDModelBase, common_models.LoggedModelBase, common_models.SemesterModelBase):
    name = models.CharField(_("Task name"), max_length=250)
    description = models.TextField(_("Description"), blank=True)
    begin = models.DateTimeField(_("Begin"))
    end = models.DateTimeField(_("End"))
    meeting_point = models.CharField(_("Meeting point"), max_length=50)

    event = models.ForeignKey(Event, verbose_name=_("Event"), on_delete=models.CASCADE)
    allowed_subjects = models.ManyToManyField(Subject, verbose_name=_("Allowed Subjects"), blank=True)
    requirements = models.ManyToManyField("Question", verbose_name=_("Requirements"), blank=True)
    min_tutors = models.IntegerField(_("Tutors (min)"), blank=True, null=True)
    max_tutors = models.IntegerField(_("Tutors (max)"), blank=True, null=True)

    tutors = models.ManyToManyField(Tutor, verbose_name=_("Assigned tutors"), through="TutorAssignment", blank=True)

    def __str__(self) -> str:
        return str(self.name)

    def log(self, user, text):
        # LogEntry.objects.create(
        #     participant=self,
        #     user=user,
        #     text=text,
        # )
        pass


class TutorAssignment(common_models.LoggedModelBase):
    tutor = models.ForeignKey(Tutor, on_delete=models.CASCADE)
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    absent = models.BooleanField(_("absent"), default=False)

    def __str__(self) -> str:
        return f"{self.tutor}"


class Question(common_models.UUIDModelBase, common_models.LoggedModelBase, common_models.SemesterModelBase):
    question = models.CharField(_("Question"), max_length=100)

    def __str__(self) -> str:
        return str(self.question)

    def log(self, user, text):
        # LogEntry.objects.create(
        #     participant=self,
        #     user=user,
        #     text=text,
        # )
        pass


class Answer(common_models.LoggedModelBase):
    class Meta:
        unique_together = ("tutor", "question")

    tutor = models.ForeignKey(Tutor, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)

    YES = "YES"
    NO = "NO"
    MAYBE = "MAYBE"
    ANSWERS = (
        (YES, _(YES)),
        (MAYBE, _(MAYBE)),
        (NO, _(NO)),
    )
    answer = models.CharField(_("Answer"), max_length=10, null=True, blank=False, choices=ANSWERS)

    def __str__(self) -> str:
        return f"{self.tutor}: {self.question} -> {self.answer}"


class MailTutorTask(common_models.LoggedModelBase):
    mail = models.ForeignKey(TutorMail, on_delete=models.CASCADE)
    tutor = models.ForeignKey(Tutor, on_delete=models.CASCADE)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self) -> str:
        return f"{self.created_at}: {self.tutor} -> {self.mail} - {self.task}"


class SubjectTutorCountAssignment(common_models.LoggedModelBase, common_models.SemesterModelBase):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    wanted = models.PositiveIntegerField(default=0, null=True, blank=True)
    waitlist = models.PositiveIntegerField(default=0, null=True, blank=True)

    def log(self, user, text):
        # LogEntry.objects.create(
        #     participant=self,
        #     user=user,
        #     text=text,
        # )
        pass

    def save_unpack(self) -> tuple[Subject, int, int]:
        if self.wanted is None or self.waitlist is None:
            raise RuntimeError(
                f"{self.subject} " f"wanted={self.wanted}, wait-list={self.waitlist} is impossible.",
            )
        return self.subject, self.wanted, self.waitlist
