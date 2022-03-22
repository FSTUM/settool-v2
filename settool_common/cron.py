import datetime as real_datetime
import logging
import warnings
from datetime import timedelta
from typing import Any, Optional, Union

from django.conf import settings
from django.core.mail import send_mail
from django.db.models import QuerySet
from django.db.models.query_utils import Q
from django.utils import timezone
from django.utils.datetime_safe import date, datetime

import fahrt.models as m_fahrt
import guidedtours.models as m_guidedtours
import settool_common.models as m_common
import tutors.models as m_tutors
from settool_common.models import AnonymisationLog, current_semester, Semester
from settool_common.utils import get_or_none


def guidedtour_reminder(semester: Semester, today: date) -> None:
    setting: m_guidedtours.Setting = get_or_none(m_guidedtours.Setting, semester=semester)
    if setting and setting.mail_reminder:
        lookup_day = today + timedelta(days=max(setting.reminder_tour_days_count, 0))
        tour: m_guidedtours.Tour
        for tour in semester.tour_set.filter(
            Q(date__day=lookup_day.day)  # date is datetime
            & Q(date__month=lookup_day.month)
            & Q(date__year=lookup_day.year),
        ):
            tour_participants: list[m_guidedtours.Participant] = list(tour.participant_set.all())
            for participant in tour_participants:
                if participant.on_the_tour:
                    setting.mail_reminder.send_mail_participant(participant)


def tutor_reminder(semester: Semester, today: date) -> None:
    tutor_settings: m_tutors.Settings = get_or_none(m_tutors.Settings, semester=semester)
    if tutor_settings and tutor_settings.mail_reminder:
        lookup_day = today + timedelta(days=max(tutor_settings.reminder_tour_days_count, 0))
        task: m_tutors.Task
        for task in m_tutors.Task.objects.filter(
            Q(semester=semester)
            & Q(begin__day=lookup_day.day)  # begin is datetime
            & Q(begin__month=lookup_day.month)
            & Q(begin__year=lookup_day.year),
        ):
            tutor: m_tutors.Tutor
            for tutor in list(task.tutors.all()):
                tutor_settings.mail_reminder.send_mail_task(tutor, task)


def fahrt_date_reminder(semester: Semester, today: date) -> None:
    current_fahrt: m_fahrt.Fahrt = get_or_none(m_fahrt.Fahrt, semester=semester)
    if current_fahrt and current_fahrt.mail_reminder:
        lookup_day = today + timedelta(days=max(current_fahrt.reminder_tour_days_count, 0))
        if current_fahrt.date == lookup_day:
            participant: m_fahrt.Participant
            for participant in semester.fahrt_participant.filter(Q(semester=semester) & Q(status="confirmed")):
                current_fahrt.mail_reminder.send_mail_participant(participant)


def fahrt_payment_reminder(semester: Semester, today: date) -> None:
    current_fahrt: m_fahrt.Fahrt = get_or_none(m_fahrt.Fahrt, semester=semester)
    if current_fahrt and current_fahrt.mail_payment_deadline:
        lookup_day = today + timedelta(days=max(current_fahrt.reminder_payment_deadline_days_count, 0))
        participant: m_fahrt.Participant
        for participant in semester.fahrt_participant.filter(
            Q(status="confirmed") & Q(payment_deadline=lookup_day),
        ):
            current_fahrt.mail_payment_deadline.send_mail_participant(participant)


def reminder_cronjob():
    today = date.today()
    semester = current_semester()
    fahrt_date_reminder(semester, today)
    fahrt_payment_reminder(semester, today)
    tutor_reminder(semester, today)
    guidedtour_reminder(semester, today)


def date_is_too_old(date_obj: Union[datetime, date, real_datetime.datetime, real_datetime.date], log_name: str) -> bool:
    if isinstance(date_obj, (datetime, real_datetime.datetime)):
        date_obj = date_obj.date()
    graceperiod_lut = {
        "fahrt": m_fahrt.ANNONIMISATION_GRACEPERIOD_AFTER_FAHRT,
        "guidedtours": m_guidedtours.ANNONIMISATION_GRACEPERIOD_AFTER_LAST_TOUR,
        "tutors": m_tutors.ANNONIMISATION_GRACEPERIOD_AFTER_LAST_TASK,
    }
    if log_name not in graceperiod_lut:
        raise ValueError(f"log_name={log_name}")
    graceperiod = graceperiod_lut[log_name]
    return date.today() + graceperiod <= date_obj


def anonymize_fahrt(semester: Semester, log_name: str) -> bool:
    current_fahrt: Optional[m_fahrt.Fahrt] = get_or_none(m_fahrt.Fahrt, semester=semester)
    if current_fahrt and date_is_too_old(current_fahrt.date, log_name):
        # fahrt is save to anonymize for this semester
        m_fahrt.Transportation.objects.filter(fahrt__semester=semester).delete()
        m_fahrt.TransportationComment.objects.filter(sender__semester=semester).delete()
        semester_participants = m_fahrt.Participant.objects.filter(semester=semester)
        semester_participants.exclude(status=m_fahrt.Participant.STATUS_CONFIRMED).delete()
        participant: m_fahrt.Participant
        for participant in semester_participants.all():
            participant.registration_time = timezone.now()
            participant.firstname = f"f {participant.pk}"
            participant.surname = f"l {participant.pk}"
            participant.birthday = timezone.now().date()
            participant.email = f"{participant.pk}@example.com"
            participant.phone = ""
            participant.mobile = ""
            participant.allergies = ""
            participant.publish_contact_to_other_paricipants = False
            participant.mailinglist = False
            participant.comment = ""
            participant.save()
        return True
    return False


def anonymize_guidedtours(semester: Semester, log_name: str) -> bool:
    semester_tours: QuerySet[m_guidedtours.Tour] = m_guidedtours.Tour.objects.filter(semester=semester)
    most_recent_tour: Optional[m_guidedtours.Tour] = semester_tours.order_by("date").last()
    if most_recent_tour and date_is_too_old(most_recent_tour.date, log_name):
        # guidedtours is save to anonymize for this semester
        participant: m_guidedtours.Participant
        for participant in m_guidedtours.Participant.objects.filter(tour__semester=semester).all():
            participant.firstname = f"f {participant.pk}"
            participant.surname = f"l {participant.pk}"
            participant.email = f"{participant.pk}@example.com"
            participant.phone = f"-1 000 {participant.pk}"
            participant.time = timezone.now()
            participant.save()
        return True
    return False


def anonymize_tutors(semester: Semester, log_name: str) -> bool:
    most_recent_task: Optional[m_tutors.Task] = m_tutors.Task.objects.filter(semester=semester).order_by("end").last()
    if most_recent_task and date_is_too_old(most_recent_task.end, log_name):
        # guidedtours is save to anonymize for this semester
        m_tutors.Answer.objects.filter(tutor__semester=semester).delete()
        m_tutors.MailTutorTask.objects.filter(tutor__semester=semester).delete()
        semester_tutors = m_tutors.Tutor.objects.filter(semester=semester)
        semester_tutors.exclude(status__in=[m_tutors.Tutor.STATUS_ACCEPTED, m_tutors.Tutor.STATUS_EMPLOYEE]).delete()
        tutor: m_tutors.Tutor
        for tutor in semester_tutors.all():
            tutor.first_name = f"f {tutor.pk}"
            tutor.last_name = f"l {tutor.pk}"
            tutor.email = f"{tutor.pk}@example.com"
            tutor.registration_time = timezone.now()
            tutor.birthday = timezone.now()
            tutor.matriculation_number = str(tutor.pk).zfill(8)[:8]
            tutor.comment = ""
            tutor.save()
        return True
    return False


def privacy_helper(semester: Semester, anonymisation_method: Any, log_name: str) -> None:
    should_anonimise = not semester.anonymisationlog_set.filter(anon_log_str=log_name).exists()
    subject = text = ""
    try:
        if should_anonimise and anonymisation_method(semester, log_name):
            AnonymisationLog.objects.create(semester=semester, anon_log_str=log_name)
            subject = f"[SUCCESS] Anonymisation of {log_name} for {semester}"
            text = f"Anonymization of {log_name} was successfully executed for {semester}"
            if settings.DEBUG:
                logging.info(subject)
                logging.info(text)
    # pylint: disable=broad-except
    except Exception as exception:
        subject = f"[ERROR] Anonymisation of {log_name} for {semester}"
        text = f"Anonymization of {log_name} failed for {semester}. The root-cause was {exception}"
        if settings.DEBUG:
            warnings.warn(subject)
            warnings.warn(text)
    # pylint: enable=broad-except
    if subject and text and not settings.DEBUG:
        send_mail(subject, text, m_common.Mail.SET, [m_common.Mail.SET_TUTOR], fail_silently=False)


def privacy_cronjob():
    for semester in Semester.objects.all():
        # anonymize_bags is not necessary, as this does not have any personal data
        privacy_helper(semester, anonymize_fahrt, "fahrt")
        privacy_helper(semester, anonymize_guidedtours, "guidedtours")
        privacy_helper(semester, anonymize_tutors, "tutors")
