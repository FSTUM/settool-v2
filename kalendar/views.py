from django.contrib.auth.decorators import login_required, permission_required
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render

from kalendar.models import Date, DateGroup
from settool_common.models import get_semester, Semester
from tutors.models import Event


@login_required
def dashboard(request: WSGIRequest) -> HttpResponse:
    context = {}
    return render(request, "kalendar/dashboard.html", context)


@permission_required("tutors.edit_tutors")
def list_dates_chronologically(request: WSGIRequest) -> HttpResponse:
    semester: Semester = get_object_or_404(Semester, pk=get_semester(request))
    events = Event.objects.filter(semester=semester).all()
    return None


@permission_required("tutors.edit_tutors")
def list_dates_grouped(request: WSGIRequest) -> HttpResponse:
    semester: Semester = get_object_or_404(Semester, pk=get_semester(request))
    events = Event.objects.filter(semester=semester).all()
    return None


@permission_required("tutors.edit_tutors")
def add_date(request: WSGIRequest, date_group_pk: int) -> HttpResponse:
    date_group: DateGroup = get_object_or_404(DateGroup, pk=date_group_pk)

    return None


@permission_required("tutors.edit_tutors")
def edit_date(request: WSGIRequest, date_pk: int) -> HttpResponse:
    date: Date = get_object_or_404(Date, pk=date_pk)
    return None


@permission_required("tutors.edit_tutors")
def del_date(request: WSGIRequest, date_pk: int) -> HttpResponse:
    date: Date = get_object_or_404(Date, pk=date_pk)
    return None


@permission_required("tutors.edit_tutors")
def view_date(request: WSGIRequest, date_pk: int) -> HttpResponse:
    date: Date = get_object_or_404(Date, pk=date_pk)
    return None
