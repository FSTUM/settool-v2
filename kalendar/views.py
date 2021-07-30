from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render

from kalendar.models import Date
from settool_common.models import get_semester, Semester
from tutors.models import Event


def dashboard(request: WSGIRequest) -> HttpResponse:
    context = {}
    return render(request, "kalendar/dashboard.html", context)


def list_dates_chronologically(request: WSGIRequest) -> HttpResponse:
    semester: Semester = get_object_or_404(Semester, pk=get_semester(request))
    events = Event.objects.filter(semester=semester).all()
    return None


def list_dates_grouped(request: WSGIRequest) -> HttpResponse:
    semester: Semester = get_object_or_404(Semester, pk=get_semester(request))
    events = Event.objects.filter(semester=semester).all()
    return None


def add_date(request: WSGIRequest, event_pk: int) -> HttpResponse:
    event: Event = get_object_or_404(Event, pk=event_pk)

    return None


def edit_date(request: WSGIRequest, date_pk: int) -> HttpResponse:
    date: Date = get_object_or_404(Date, pk=date_pk)
    return None


def del_date(request: WSGIRequest, date_pk: int) -> HttpResponse:
    date: Date = get_object_or_404(Date, pk=date_pk)
    return None


def view_date(request: WSGIRequest, date_pk: int) -> HttpResponse:
    date: Date = get_object_or_404(Date, pk=date_pk)
    return None
