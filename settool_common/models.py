import datetime
import os
import re
from io import BytesIO
from typing import Any, Dict, List, Optional, Tuple, Union

import qrcode
from django.core.files import File
from django.core.mail import EmailMessage, send_mail
from django.db import models
from django.http import HttpRequest, HttpResponse
from django.template import Context, Template
from django.utils import timezone
from django.utils.deconstruct import deconstructible
from django.utils.translation import ugettext_lazy as _
from PIL import Image

import settool.settings as main_settings

from .settings import SEMESTER_SESSION_KEY
from .utils import pos_http_response_to_attachable


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
    general_placeholders: List[Tuple[str, str]] = []
    # ["{{template}}", "description", "contition"]
    conditional_placeholders: List[Tuple[str, str, str]] = []
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

    def __str__(self):
        if self.comment:
            return f"{self.subject} ({self.comment})"
        return str(self.subject)

    def get_mail(self, context: Union[Context, Dict[str, Any], None]) -> Tuple[str, str, str]:
        if not isinstance(context, Context):
            context = Context(context or {})

        subject_template = Template(self.subject)
        subject: str = subject_template.render(context).rstrip()

        text_template = Template(self.text)
        text: str = text_template.render(context)

        return subject, text, self.sender

    def send_mail(
        self,
        context: Union[Context, Dict[str, Any], None],
        recipients: Union[List[str], str],
        attachments: Optional[Union[HttpResponse, List[Tuple[str, Any, str]]]] = None,
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
            for (filename, content, mimetype) in [pos_http_response_to_attachable(attach) for attach in attachments]:
                mail.attach(filename, content, mimetype)
            mail.send(fail_silently=False)
        return True


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

    def __str__(self):
        return f"{self.get_semester_display()} {self.year:4}"


class Subject(models.Model):
    class Meta:
        unique_together = (("degree", "subject"),)
        ordering = ["degree", "subject"]

    BACHELOR = "BA"
    MASTER = "MA"
    DEGREE_CHOICES = (
        (BACHELOR, _("Bachelor")),
        (MASTER, _("Master")),
    )

    MATHEMATICS = "Mathe"
    PHYSICS = "Physik"
    INFORMATICS = "Info"
    GAMES_ENGINEERING = "Games"
    INFORMATION_SYSTEMS = "Winfo"
    ASE = "ASE"
    CSE = "CSE"
    BMC = "BMC"
    ROBOTICS = "Robotics"
    OPERATIONS_RESEARCH = "Mathe OR"
    SCIENCE_ENGINEERING = "Mathe SE"
    FINANCE = "Mathe Finance"
    BIOMATHE = "Mathe Bio"

    SUBJECT_CHOICES = (
        (MATHEMATICS, _("Mathematics")),
        (PHYSICS, _("Physics")),
        (INFORMATICS, _("Informatics")),
        (GAMES_ENGINEERING, _("Informatics: Games Engineering")),
        (INFORMATION_SYSTEMS, _("Information Systems")),
        (ASE, _("Automotive Software Engineering")),
        (CSE, _("Computational Science and Engineering")),
        (BMC, _("Biomedical Computing")),
        (ROBOTICS, _("Robotics, Cognition, Intelligence")),
        (OPERATIONS_RESEARCH, _("Mathematics in Operatios Research")),
        (SCIENCE_ENGINEERING, _("Mathematics in Science and Engineering")),
        (FINANCE, _("Mathematics in Finance and Acturial Science")),
        (BIOMATHE, _("Mathematics in Bioscience")),
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
        return f"{self.get_degree_display()} {self.get_subject_display()}"


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
    content = models.CharField(max_length=200)
    qr_code = models.ImageField(upload_to="qr_codes", blank=True)

    def __str__(self):
        return self.content

    # pylint: disable=signature-differs
    def save(self, *args, **kwargs):
        qr_code = qrcode.QRCode(
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=20,
            border=1,
        )
        qr_code.add_data(self.content)
        qr_code.make(fit=True)
        qr_image = qr_code.make_image(fill_color="black", back_color="white")

        with Image.new("RGB", (qr_image.pixel_size, qr_image.pixel_size), "white") as canvas:
            canvas.paste(qr_image)

            logo_path = os.path.join(main_settings.STATIC_ROOT, "eule.png")
            with Image.open(logo_path) as logo:
                usable_height = qr_image.pixel_size - qr_image.box_size * qr_image.border * 2
                size = int(usable_height * 0.3 / qr_image.box_size + 1) * qr_image.box_size
                # current image version can take it to have up to 30% covered up.
                # due to math we are always below that limt
                if ((qr_image.pixel_size - size) // 2 % qr_image.box_size) != 0:
                    size += qr_image.box_size

                v_size = int(size * (logo.height / logo.width))  # WHY is our logo not sqare?

                t_logo = logo.resize((size, v_size), Image.ANTIALIAS)
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
