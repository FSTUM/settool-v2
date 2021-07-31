import datetime
from typing import Any, Dict

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import QuerySet
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import ugettext_lazy as _

from kalendar.forms import DateForm
from kalendar.models import Date, DateGroup
from settool_common.models import get_semester, Semester
from tutors.models import Event


@login_required
def dashboard(request: WSGIRequest) -> HttpResponse:
    context: Dict[str, Any] = {}
    return render(request, "kalendar/dashboard.html", context)


@permission_required("tutors.edit_tutors")
def list_dates_chronologically(request: WSGIRequest) -> HttpResponse:
    dates: QuerySet[Date] = Date.objects.filter(date__date__gte=datetime.datetime.today()).order_by("date").all()
    context = {"dates": dates}
    return render(request, "kalendar/management/list/chronological.html", context)


@permission_required("tutors.edit_tutors")
def list_dates_grouped(request: WSGIRequest) -> HttpResponse:
    semester: Semester = get_object_or_404(Semester, pk=get_semester(request))
    events = Event.objects.filter(semester=semester).all()
    context = {"events": events}
    return render(request, "kalendar/management/list/grouped.html", context)


@permission_required("tutors.edit_tutors")
def add_date(request: WSGIRequest, date_group_pk: int) -> HttpResponse:
    date_group: DateGroup = get_object_or_404(DateGroup, pk=date_group_pk)

    form = DateForm(request.POST or None, date_group=date_group)
    if form.is_valid():
        date: Date = form.save()
        messages.success(request, _("Successfully added date %s.").format(date))
        return redirect("kalendar:main_index")

    context = {"date_group": date_group, "form": form}
    return render(request, "kalendar/management/add_date.html", context)


@permission_required("tutors.edit_tutors")
def edit_date(request: WSGIRequest, date_pk: int) -> HttpResponse:
    date: Date = get_object_or_404(Date, pk=date_pk)

    form = DateForm(request.POST or None, instance=date, date_group=date.group)
    if form.is_valid():
        edited_date: Date = form.save()
        messages.success(request, _("Successfully added date %s.").format(edited_date))
        return redirect("kalendar:main_index")

    context = {"date": date, "form": form}
    return render(request, "kalendar/management/edit_date.html", context)


@permission_required("tutors.edit_tutors")
def del_date(request: WSGIRequest, date_pk: int) -> HttpResponse:
    date: Date = get_object_or_404(Date, pk=date_pk)

    form = forms.Form(request.POST or None)
    if form.is_valid():
        date.delete()
        messages.success(request, _("Deleted date %s.").format(date))
        return redirect("kalendar:main_index")

    context = {"date": date, "form": form}
    return render(request, "kalendar/management/delete_date.html", context)


@permission_required("tutors.edit_tutors")
def view_date(request: WSGIRequest, date_pk: int) -> HttpResponse:
    date: Date = get_object_or_404(Date, pk=date_pk)

    context = {"date": date}
    return render(request, "kalendar/management/view_date.html", context)
