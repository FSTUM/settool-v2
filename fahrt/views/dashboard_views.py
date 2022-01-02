from django.contrib.auth.decorators import permission_required
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import Count, Q, QuerySet
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils.translation import gettext_lazy as _

from settool_common.models import get_semester, Semester, Subject

from ..models import Participant, Transportation


def _get_cp_u18_counts(c_p: QuerySet[Participant]) -> list[int]:
    part_u18 = [participant.u18 for participant in c_p.all()]
    u18_count = len([participant for participant in part_u18 if participant])
    non_u18_count = len(part_u18) - u18_count
    return [u18_count, non_u18_count]


def _get_cp_paid_counts(c_p: QuerySet[Participant]) -> list[int]:
    paid_participants_count: int = c_p.exclude(paid=None).count()
    unpaid_participants_count: int = c_p.filter(paid=None).count()
    return [paid_participants_count, unpaid_participants_count]


def _get_cp_non_liability_counts(c_p: QuerySet[Participant]) -> list[int]:
    submitted_non_liability_count: int = c_p.exclude(non_liability=None).count()
    not_submitted_non_liability_count: int = c_p.filter(non_liability=None).count()
    return [submitted_non_liability_count, not_submitted_non_liability_count]


def _get_cp_bachlor_master_counts(c_p: QuerySet[Participant]) -> list[int]:
    master_count: int = c_p.filter(subject__degree=Subject.MASTER).count()
    bachlor_count: int = c_p.filter(subject__degree=Subject.BACHELOR).count()
    return [bachlor_count, master_count]


def _get_cp_transportation_type_counts(c_p):
    return [
        c_p.filter(transportation__transport_type=Transportation.CAR).count(),
        c_p.filter(transportation__transport_type=Transportation.TRAIN).count(),
        c_p.filter(transportation=None).count(),
    ]


@permission_required("fahrt.view_participants")
def dashboard(request: WSGIRequest) -> HttpResponse:
    semester: Semester = get_object_or_404(Semester, pk=get_semester(request))
    # confirmed_participants
    c_p: QuerySet[Participant] = Participant.objects.filter(Q(semester=semester) & Q(status="confirmed"))
    cp_by_studies = c_p.values("subject").annotate(subject_count=Count("subject")).order_by("subject_count")
    participants_by_status = (
        Participant.objects.filter(semester=semester)
        .values("status")
        .annotate(status_count=Count("status"))
        .order_by("status")
    )

    cp_by_gender = c_p.values("gender").annotate(gender_count=Count("gender")).order_by("-gender")

    cp_by_food = c_p.values("nutrition").annotate(nutrition_count=Count("nutrition")).order_by("-nutrition")

    context = {
        "cp_by_transportation_type_data": _get_cp_transportation_type_counts(c_p),
        "participants_by_group_labels": [_(status["status"]) for status in participants_by_status],
        "participants_by_group_data": [status["status_count"] for status in participants_by_status],
        "cp_by_studies_labels": [str(Subject.objects.get(pk=subject["subject"])) for subject in cp_by_studies],
        "cp_by_studies_data": [subject["subject_count"] for subject in cp_by_studies],
        "cp_by_food_labels": [_(nutrition["nutrition"]) for nutrition in cp_by_food],
        "cp_by_food_data": [nutrition["nutrition_count"] for nutrition in cp_by_food],
        "cp_by_gender_labels": [_(gender["gender"]) for gender in cp_by_gender],
        "cp_by_gender_data": [gender["gender_count"] for gender in cp_by_gender],
        "cp_bachlor_master": _get_cp_bachlor_master_counts(c_p),
        "cp_age": _get_cp_u18_counts(c_p),
        "cp_paid": _get_cp_paid_counts(c_p),
        "cp_non_liability": _get_cp_non_liability_counts(c_p),
    }
    return render(request, "fahrt/fahrt_dashboard.html", context)
