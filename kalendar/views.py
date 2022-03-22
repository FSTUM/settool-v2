from typing import Any
from uuid import UUID

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import QuerySet
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _

from kalendar.forms import DateForm
from kalendar.models import Date, DateGroup, DateGroupSubscriber, DateSubscriber
from settool_common.models import get_semester, Semester
from tutors.models import Event, Tutor


@login_required
def dashboard(request: WSGIRequest) -> HttpResponse:
    context: dict[str, Any] = {}
    return render(request, "kalendar/dashboard.html", context)


@permission_required("tutors.edit_tutors")
def list_future_dates(request: WSGIRequest) -> HttpResponse:
    dates: list[Date] = [date for date in Date.objects.order_by("date").all() if date.is_in_future]
    context = {"dates": dates}
    return render(request, "kalendar/management/list/chronological.html", context)


@permission_required("tutors.edit_tutors")
def list_dates(request: WSGIRequest) -> HttpResponse:
    dates: QuerySet[Date] = Date.objects.order_by("date").all()
    context = {"dates": dates, "show_past": True}
    return render(request, "kalendar/management/list/chronological.html", context)


@permission_required("tutors.edit_tutors")
def list_dates_grouped(request: WSGIRequest) -> HttpResponse:
    semester: Semester = get_object_or_404(Semester, pk=get_semester(request))
    events = Event.objects.filter(semester=semester).all()
    context = {"events": events}
    return render(request, "kalendar/management/list/grouped.html", context)


@permission_required("tutors.edit_tutors")
def add_date(request: WSGIRequest, date_group_pk: UUID) -> HttpResponse:
    date_group: DateGroup = get_object_or_404(DateGroup, pk=date_group_pk)

    form = DateForm(request.POST or None, date_group=date_group)
    if form.is_valid():
        date: Date = form.save()
        messages.success(request, _("Successfully added date {date}.").format(date=date))
        return redirect("kalendar:main_index")

    context = {"date_group": date_group, "form": form}
    return render(request, "kalendar/management/add_date.html", context)


@permission_required("tutors.edit_tutors")
def edit_date(request: WSGIRequest, date_pk: UUID) -> HttpResponse:
    date: Date = get_object_or_404(Date, pk=date_pk)

    form = DateForm(request.POST or None, instance=date, date_group=date.group)
    if form.is_valid():
        edited_date: Date = form.save()
        messages.success(request, _("Successfully edited date {date}.").format(date=edited_date))
        return redirect("kalendar:main_index")

    context = {"date": date, "form": form}
    return render(request, "kalendar/management/edit_date.html", context)


@permission_required("tutors.edit_tutors")
def del_date(request: WSGIRequest, date_pk: UUID) -> HttpResponse:
    date: Date = get_object_or_404(Date, pk=date_pk)

    form = forms.Form(request.POST or None)
    if form.is_valid():
        date.delete()
        messages.success(request, _("Deleted date {date}.").format(date=date))
        return redirect("kalendar:main_index")

    context = {"date": date, "form": form}
    return render(request, "kalendar/management/delete_date.html", context)


@permission_required("tutors.edit_tutors")
def view_date(request: WSGIRequest, date_pk: UUID) -> HttpResponse:
    date: Date = get_object_or_404(Date, pk=date_pk)

    context = {"date": date}
    return render(request, "kalendar/management/view_date.html", context)


def view_date_public(request: WSGIRequest, tutor_uuid: UUID, date_pk: UUID) -> HttpResponse:
    tutor: Tutor = get_object_or_404(Tutor, pk=tutor_uuid)
    date: Date = get_object_or_404(Date, pk=date_pk)
    if (
        not DateSubscriber.objects.filter(tutor=tutor, date=date).exists()
        and not DateGroupSubscriber.objects.filter(tutor=tutor, date=date.group).exists()
    ):
        raise Http404()

    context = {
        "date": date,
        "tutor": tutor,
    }
    return render(request, "kalendar/user/view_date_public.html", context)
