import datetime
import os
import re
from io import BytesIO
from typing import Any, Optional, Union

import qrcode
from django.conf import settings
from django.core.files import File
from django.core.mail import EmailMessage, send_mail
from django.db import models
from django.dispatch import receiver
from django.http import HttpRequest, HttpResponse
from django.template import Context, Template
from django.utils import timezone
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _
from PIL import Image

from .settings import SEMESTER_SESSION_KEY


class Mail(models.Model):
    SET = "SET-Team <set@fs.tum.de>"
    SET_FAHRT = "SET-Fahrt-Team <setfahrt@fs.tum.de>"
    SET_TUTOR = "SET-Tutor-Team <set-tutoren@fs.tum.de>"
    SET_BAGS = "Sponsoring-Team des SET-Referats <set-tueten@fs.tum.de>"
    FROM_CHOICES = (
        (SET, _("SET")),
        (SET_FAHRT, _("SET_FAHRT")),
        (SET_TUTOR, _("SET_TUTOR")),
        (SET_BAGS, _("SET_BAGS")),
    )
    # ["{{template}}", "description"]
    general_placeholders: list[tuple[str, str]] = []
    # ["{{template}}", "description", "contition"]
    conditional_placeholders: list[tuple[str, str, str]] = []
    notes: str = ""

    # perms are or-connected-permissions (you need one of them instead of all of them)
    required_perm = ["set.mail"]

    @classmethod
    def check_perm(cls, user):
        return any(user.has_perm(perm) for perm in cls.required_perm)

    sender = models.CharField(
        max_length=100,
        choices=FROM_CHOICES,
        default=SET,
        verbose_name=_("From"),
    )

    subject = models.CharField(
        _("Email subject"),
        max_length=200,
        help_text=_("You may use placeholders for the subject."),
    )

    text = models.TextField(
        _("Text"),
        help_text=_("You may use placeholders for the text."),
    )

    comment = models.CharField(
        _("Comment"),
        max_length=200,
        default="",
        blank=True,
    )

    def __str__(self) -> str:
        if self.comment:
            return f"{self.subject} ({self.comment})"
        return str(self.subject)

    def get_mail(self, context: Union[Context, dict[str, Any], None]) -> tuple[str, str, str]:
        if not isinstance(context, Context):
            context = Context(context or {})

        subject_template = Template(self.subject)
        subject: str = subject_template.render(context).rstrip()

        text_template = Template(self.text)
        text: str = text_template.render(context)

        return subject, text, self.sender

    def send_mail(
        self,
        context: Union[Context, dict[str, Any], None],
        recipients: Union[list[str], str],
        attachments: Optional[list[Union[HttpResponse, tuple[str, Any, str]]]] = None,
    ) -> bool:
        if isinstance(recipients, str):
            recipients = [recipients]
        if not isinstance(context, Context):
            context = Context(context or {})
        subject_template = Template(self.subject)
        subject = subject_template.render(context).rstrip()

        text_template = Template(self.text)
        text = text_template.render(context)

        regex = r"({{.*?}})"
        subject_matches = re.match(regex, subject, re.MULTILINE)
        text_matches = re.match(regex, text, re.MULTILINE)

        if subject_matches is not None or text_matches is not None:
            return False
        if attachments is None:
            send_mail(subject, text, self.sender, recipients, fail_silently=False)
        else:
            mail = EmailMessage(subject, text, self.sender, recipients)
            attach: Union[HttpResponse, tuple[str, Any, str]]
            for attach in attachments:
                (filename, content, mimetype) = clean_attachable(attach)
                mail.attach(filename, content, mimetype)
            mail.send(fail_silently=False)
        return True


def clean_attachable(response: Union[HttpResponse, tuple[str, Any, str]]) -> tuple[str, Any, str]:
    if not isinstance(response, HttpResponse):
        return response
    content_type = response.get("Content-Type", "text/text")
    filename = response.get("Content-Disposition", "filename.txt").replace("inline; filename=", "")
    return filename, response.content, content_type


@deconstructible
class Semester(models.Model):
    class Meta:
        unique_together = (("semester", "year"),)
        ordering = ["year", "semester"]

    WINTER = "WS"
    SUMMER = "SS"
    SEMESTER_CHOICES = (
        (WINTER, _("Winter semester")),
        (SUMMER, _("Summer semester")),
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

    def short_form(self) -> str:
        return f"{self.semester}{str(self.year)[2:]}"

    def __str__(self) -> str:
        return f"{self.get_semester_display()} {self.year:4}"


class CourseBundle(models.Model):
    class Meta:
        ordering = ["name"]

    name = models.CharField(
        max_length=100,
        verbose_name=_("Course-bundles' name"),
        unique=True,
    )

    def __str__(self) -> str:
        return self.name


class Subject(models.Model):
    class Meta:
        unique_together = (("degree", "subject"),)
        ordering = ["degree", "course_bundle", "subject"]

    BACHELOR = "BA"
    MASTER = "MA"

    course_bundle = models.ForeignKey(
        CourseBundle,
        on_delete=models.CASCADE,
        verbose_name=_("Course-bundle"),
    )

    degree = models.CharField(
        max_length=2,
        choices=(
            (BACHELOR, _("Bachelor")),
            (MASTER, _("Master")),
        ),
        default=BACHELOR,
        verbose_name=_("Degree"),
    )

    subject = models.CharField(
        max_length=100,
        verbose_name=_("Subject"),
    )

    def __str__(self) -> str:
        return f"{self.get_degree_display()} {self.subject} ({self.course_bundle})"


def current_semester() -> Semester:
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


def get_semester(request: HttpRequest) -> int:
    sem: int
    try:
        sem = int(request.session[SEMESTER_SESSION_KEY])
    except KeyError:
        sem = current_semester().pk
        request.session[SEMESTER_SESSION_KEY] = sem
    return sem  # noqa: R504


class QRCode(models.Model):
    content = models.CharField(max_length=200, unique=True)
    qr_code = models.ImageField(upload_to="qr_codes", blank=True)

    def __str__(self) -> str:
        return self.content

    # pylint: disable=signature-differs
    def save(self, *args, **kwargs):
        qr_code = qrcode.QRCode(
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=19,
            border=1,
        )
        qr_code.add_data(self.content)
        qr_code.make(fit=True)
        qr_image = qr_code.make_image(fill_color="black", back_color="white")

        with Image.new("RGB", (qr_image.pixel_size, qr_image.pixel_size), "white") as canvas:
            canvas.paste(qr_image)

            logo_path = os.path.join(settings.STATIC_ROOT, "logo", "eule_squared.png")
            with Image.open(logo_path) as logo:
                total_usable_height = qr_image.pixel_size - qr_image.box_size * qr_image.border * 2
                usable_height = total_usable_height * 0.3
                size = int(usable_height // qr_image.box_size + 1) * qr_image.box_size
                # current image version can take it to have up to 30% covered up.
                # due to math we are always below that limt
                if ((qr_image.pixel_size - size) // 2 % qr_image.box_size) != 0:
                    size += qr_image.box_size

                t_logo = logo.resize((size, size))
                pos = (qr_image.pixel_size - size) // 2
                canvas.paste(t_logo, (pos, pos))

            f_cleaned_content = (
                self.content.replace("https://", "")
                .replace("http://", "")
                .strip("/")
                .replace("/", "-")
                .replace(".", "_")
            )
            buffer = BytesIO()
            canvas.save(buffer, "PNG")
            self.qr_code.save(f"qr_code_{f_cleaned_content}.png", File(buffer), save=False)
            super().save(*args, **kwargs)


@receiver(models.signals.post_delete, sender=QRCode)
def auto_delete_qr_code_on_delete(sender, instance, **_kwargs):
    """
    Deletes file from filesystem
    when corresponding `QRCode` object is deleted.
    """
    _ = sender  # sender is needed, for api. it cannot be renamed, but is unused here.
    if instance.qr_code and os.path.isfile(instance.qr_code.path):
        os.remove(instance.qr_code.path)


class AnonymisationLog(models.Model):
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)
    anon_log_str = models.CharField(max_length=10)

    def __str__(self) -> str:
        return f"{self.semester}-{self.anon_log_str}"
