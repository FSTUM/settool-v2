from datetime import timedelta

from django.db.models.query_utils import Q
from django.utils.datetime_safe import date

import fahrt
import guidedtours
from fahrt.models import Fahrt
from guidedtours.models import Setting, Tour
from settool_common.models import current_semester, Semester
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


def master_cronjob():
    today = date.today()
    semester = current_semester()
    fahrt_date_reminder(semester, today)
    fahrt_payment_reminder(semester, today)
    tutor_reminder(semester, today)
    guidedtour_reminder(semester, today)
