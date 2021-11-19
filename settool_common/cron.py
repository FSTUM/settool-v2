import datetime as real_datetime
from datetime import timedelta
from typing import Any, Optional, Union

from dateutil.relativedelta import relativedelta
from django.db.models.query_utils import Q
from django.utils.datetime_safe import date, datetime

import fahrt
import guidedtours
from fahrt.models import Fahrt
from guidedtours.models import Setting, Tour
from settool_common.models import AnonymisationLog, current_semester, Semester
from settool_common.utils import get_or_none
from tutors.models import Settings, Task, Tutor


def guidedtour_reminder(semester: Semester, today: date) -> None:
    setting: Setting = get_or_none(Setting, semester=semester)
    if setting and setting.mail_reminder:
        lookup_day = today + timedelta(days=max(setting.reminder_tour_days_count, 0))
        tour: Tour
        for tour in semester.tour_set.filter(
            Q(date__day=lookup_day.day)  # date is datetime
            & Q(date__month=lookup_day.month)
            & Q(date__year=lookup_day.year),
        ):
            participant: guidedtours.models.Participant
            for participant in [participant for participant in tour.participant_set.all() if participant.on_the_tour]:
                setting.mail_reminder.send_mail_participant(participant)


def tutor_reminder(semester: Semester, today: date) -> None:
    settings: Settings = get_or_none(Settings, semester=semester)
    if settings and settings.mail_reminder:
        lookup_day = today + timedelta(days=max(settings.reminder_tour_days_count, 0))
        task: Task
        for task in Task.objects.filter(
            Q(semester=semester)
            & Q(begin__day=lookup_day.day)  # begin is datetime
            & Q(begin__month=lookup_day.month)
            & Q(begin__year=lookup_day.year),
        ):
            tutor: Tutor
            for tutor in list(task.tutors.all()):
                settings.mail_reminder.send_mail_task(tutor, task)


def fahrt_date_reminder(semester: Semester, today: date) -> None:
    current_fahrt: Fahrt = get_or_none(Fahrt, semester=semester)
    if current_fahrt and current_fahrt.mail_reminder:
        lookup_day = today + timedelta(days=max(current_fahrt.reminder_tour_days_count, 0))
        if current_fahrt.date == lookup_day:
            participant: fahrt.models.Participant
            for participant in semester.fahrt_participant.filter(Q(semester=semester) & Q(status="confirmed")):
                current_fahrt.mail_reminder.send_mail_participant(participant)


def fahrt_payment_reminder(semester: Semester, today: date) -> None:
    current_fahrt: Fahrt = get_or_none(Fahrt, semester=semester)
    if current_fahrt and current_fahrt.mail_payment_deadline:
        lookup_day = today + timedelta(days=max(current_fahrt.reminder_payment_deadline_days_count, 0))
        participant: fahrt.models.Participant
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


def anonymise_fahrt(semester: Semester, today: date, log_name: str) -> bool:
    current_fahrt: Optional[Fahrt] = get_or_none(Fahrt, semester=semester)
    if current_fahrt and date_is_too_old(today, current_fahrt.date, log_name):
        # fahrt is save to be anonymised for this semester
        # TODO
        return True
    return False


def anonymise_guidedtours(semester: Semester, today: date, log_name: str) -> bool:
    most_recent_tour: Optional[Tour] = Tour.objects.filter(semester=semester).order_by("date").last()
    if most_recent_tour and date_is_too_old(today, most_recent_tour.date, log_name):
        # guidedtours is save to be anonymised for this semester
        # TODO
        return True
    return False


def anonymise_tutors(semester: Semester, today: date, log_name: str) -> bool:
    most_recent_task: Optional[Task] = Task.objects.filter(semester=semester).order_by("end").last()
    if most_recent_task and date_is_too_old(today, most_recent_task.end, log_name):
        # guidedtours is save to be anonymised for this semester
        # TODO
        return True
    return False


def privacy_helper(semester: Semester, today: date, anonymisation_method: Any, log_name: str) -> None:
    should_anonimise = not semester.anonymisationlog_set.filter(anon_log_str=log_name).exists()
    if should_anonimise and anonymisation_method(semester, today, log_name):
        AnonymisationLog.objects.create(semester=semester, anon_log_str=log_name)


def privacy_cronjob():
    today = date.today()
    for semester in Semester.objects.all():
        # anonymise_bags is not nessesary, as this does not have any personal data
        privacy_helper(semester, today, anonymise_fahrt, "fahrt")
        privacy_helper(semester, today, anonymise_guidedtours, "guidedtours")
        privacy_helper(semester, today, anonymise_tutors, "tutors")
