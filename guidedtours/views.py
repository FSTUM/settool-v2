import dataclasses
import datetime
import time
from typing import Any, Optional, Union
from uuid import UUID

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import Q, QuerySet
from django.forms import formset_factory
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext as _
from django_tex.response import PDFResponse
from django_tex.shortcuts import render_to_pdf

from kalendar.models import Date
from settool_common import utils
from settool_common.models import get_semester, Semester

from .forms import (
    FilterParticipantsForm,
    MailForm,
    ParticipantForm,
    SelectMailForm,
    SelectParticipantForm,
    SettingsAdminForm,
    TourForm,
)
from .models import Participant, Setting, Tour, TourMail


@permission_required("guidedtours.view_participants")
def list_tours(request: WSGIRequest) -> HttpResponse:
    semester: Semester = get_object_or_404(Semester, pk=get_semester(request))
    tours = semester.tour_set.all()

    context = {"tours": tours}
    return render(request, "guidedtours/tours/list_tours.html", context)


@dataclasses.dataclass
class MinimalTour:
    capacity: int
    name: str
    dates: list[datetime.datetime]
    registered: int

    @property
    def label(self) -> str:
        label = [self.name]
        if self.dates:
            for date in self.dates:
                label.append(f"{date.strftime('%d.%m %H')}Uhr")
        else:
            label.append(_("No dates"))
        return " ".join(label)


@permission_required("guidedtours.view_participants")
def dashboard(request: WSGIRequest) -> HttpResponse:
    tours_current_semester: list[Tour] = Tour.sorted_by_semester(get_semester(request))  # type:ignore
    tours: list[MinimalTour] = []
    for tour in tours_current_semester:
        registered = Participant.objects.filter(tour=tour).count()
        meetings = tour.associated_meetings
        if not meetings:
            raise ValueError(f"Tour {tour} has no associated meetings")
        tours.append(
            MinimalTour(
                capacity=tour.capacity,
                name=tour.name,
                dates=meetings.dates,
                registered=registered,
            ),
        )

    context = {
        "tour_labels": [tour.label for tour in tours],
        "tour_registrations": [tour.registered for tour in tours],
        "tour_capacity": [tour.capacity for tour in tours],
    }
    return render(request, "guidedtours/tour_dashboard.html", context)


@permission_required("guidedtours.view_participants")
def view_tour(request: WSGIRequest, tour_pk: UUID) -> HttpResponse:
    tour = get_object_or_404(Tour, pk=tour_pk)
    participants = tour.participant_set.order_by("created_at")
    waitinglist = participants[tour.capacity :]
    participants = participants[: tour.capacity]

    context = {
        "tour": tour,
        "participants": participants,
        "waitinglist": waitinglist,
    }
    return render(request, "guidedtours/participants/list_tour-participants.html", context)


@permission_required("guidedtours.view_participants")
def add_tour(request: WSGIRequest) -> HttpResponse:
    semester: Semester = get_object_or_404(Semester, pk=get_semester(request))

    form = TourForm(request.POST or None, semester=semester)

    if form.is_valid():
        form.save()

        return redirect("guidedtours:list_tours")

    context = {
        "form": form,
    }
    return render(request, "guidedtours/tours/add_tour.html", context)


@permission_required("guidedtours.view_participants")
def edit_tour(request: WSGIRequest, tour_pk: UUID) -> HttpResponse:
    tour = get_object_or_404(Tour, pk=tour_pk)

    form = TourForm(
        request.POST or None,
        semester=tour.semester,
        instance=tour,
    )
    if form.is_valid():
        form.save()

        return redirect("guidedtours:view_tour", tour.id)

    context = {
        "form": form,
        "tour": tour,
    }
    return render(request, "guidedtours/tours/edit_tour.html", context)


@permission_required("guidedtours.view_participants")
def del_tour(request: WSGIRequest, tour_pk: UUID) -> HttpResponse:
    tour = get_object_or_404(Tour, pk=tour_pk)

    form = forms.Form(request.POST or None)
    if form.is_valid():
        tour.delete()

        return redirect("guidedtours:list_tours")

    context = {
        "form": form,
        "tour": tour,
    }
    return render(request, "guidedtours/tours/del_tour.html", context)


@permission_required("guidedtours.view_participants")
def filter_participants(request: WSGIRequest) -> HttpResponse:
    semester: Semester = get_object_or_404(Semester, pk=get_semester(request))
    participants: QuerySet[Participant] = Participant.objects.filter(tour__semester=semester).order_by("surname")

    filterform = FilterParticipantsForm(request.POST or None, semester=semester)

    if filterform.is_valid():
        search: str = filterform.cleaned_data["search"]
        on_the_tour: str = filterform.cleaned_data["on_the_tour"]
        tour: Optional[Tour] = filterform.cleaned_data["tour"]

        if search:
            participants = participants.filter(
                Q(firstname__icontains=search)
                | Q(surname__icontains=search)
                | Q(email__icontains=search)
                | Q(phone__icontains=search)
                | Q(tour__name__icontains=search)
                | Q(tour__description__icontains=search),
            )

        if tour is not None:
            participants = participants.filter(tour=tour)
        if on_the_tour == "True":
            filtered_participants = [p.id for p in participants if p.on_the_tour]
        elif on_the_tour == "False":
            filtered_participants = [p.id for p in participants if not p.on_the_tour]
        else:  # on_the_tour == "":
            filtered_participants = [p.id for p in participants]

        request.session["filtered_participants"] = filtered_participants
        return redirect("guidedtours:filtered_participants")

    context = {
        "participants": participants,
        "filterform": filterform,
    }
    return render(request, "guidedtours/participants/filter_participants.html", context)


@permission_required("guidedtours.view_participants")
def filtered_list(request: WSGIRequest) -> HttpResponse:
    filtered_participants = request.session["filtered_participants"]
    participants = Participant.objects.filter(
        id__in=filtered_participants,
    ).order_by("surname")

    form = SelectMailForm(request.POST or None)
    select_participant_form_set = formset_factory(
        SelectParticipantForm,
        extra=0,
    )
    participantforms = select_participant_form_set(
        request.POST or None,
        initial=[{"id": p.id, "selected": True} for p in participants],
    )

    if form.is_valid() and participantforms.is_valid():
        mail = form.cleaned_data["mail"]

        selected_participants = []
        for participant in participantforms:
            try:
                participant_id = participant.cleaned_data["id"]
            except KeyError:
                continue
            try:
                selected = participant.cleaned_data["selected"]
            except KeyError:
                selected = False
            if selected:
                selected_participants.append(participant_id)

        request.session["selected_participants"] = selected_participants
        return redirect("guidedtours:send_mail", mail.id)

    participants_and_select = []
    for participant in participants:
        for participant_form in participantforms:
            if participant_form.initial["id"] == participant.id:
                participants_and_select.append((participant, participant_form))
                break

    context = {
        "participants": participants_and_select,
        "form": form,
        "participantforms": participantforms,
    }
    return render(request, "guidedtours/participants/filtered_participants.html", context)


@permission_required("guidedtours.view_participants")
def list_mails(request: WSGIRequest) -> HttpResponse:
    context = {"mails": TourMail.objects.all()}
    return render(request, "guidedtours/maintenance/mail/list_mails.html", context)


@permission_required("guidedtours.view_participants")
def add_mail(request: WSGIRequest) -> HttpResponse:
    form = MailForm(request.POST or None)
    if form.is_valid():
        form.save()

        return redirect("guidedtours:list_mails")

    context = {"form": form, "mail": TourMail}
    return render(request, "guidedtours/maintenance/mail/add_mail.html", context)


@permission_required("guidedtours.view_participants")
def edit_mail(request: WSGIRequest, mail_pk: int) -> HttpResponse:
    mail = get_object_or_404(TourMail, pk=mail_pk)

    form = MailForm(request.POST or None, instance=mail)
    if form.is_valid():
        form.save()

        return redirect("guidedtours:list_mails")

    context = {
        "form": form,
        "mail": mail,
    }
    return render(request, "guidedtours/maintenance/mail/edit_mail.html", context)


@permission_required("guidedtours.view_participants")
def delete_mail(request: WSGIRequest, mail_pk: int) -> HttpResponse:
    mail = get_object_or_404(TourMail, pk=mail_pk)

    form = forms.Form(request.POST or None)
    if form.is_valid():
        mail.delete()

        return redirect("guidedtours:list_mails")

    context = {
        "mail": mail,
        "form": form,
    }
    return render(request, "guidedtours/maintenance/mail/del_mail.html", context)


@permission_required("guidedtours.view_participants")
def send_mail(request: WSGIRequest, mail_pk: int) -> HttpResponse:
    mail = get_object_or_404(TourMail, pk=mail_pk)
    selected_participants = request.session["selected_participants"]
    participants = Participant.objects.filter(
        id__in=selected_participants,
    ).order_by("surname")

    subject, text, from_email = mail.get_mail_participant()

    form = forms.Form(request.POST or None)
    if form.is_valid():
        for participant in participants:
            mail.send_mail_participant(participant)
        return redirect("guidedtours:filter_tours")

    context = {
        "participants": participants,
        "subject": subject,
        "text": text,
        "from_email": from_email,
        "form": form,
    }

    return render(request, "guidedtours/maintenance/mail/send_mail.html", context)


def _get_tours_and_dates(semester: Semester) -> tuple[list[tuple[Tour, list[Date]]], list[Tour], list[Date]]:
    tours: QuerySet[Tour] = Tour.objects.filter(
        semester=semester,
        open_registration__lt=timezone.now(),
        close_registration__gt=timezone.now(),
        associated_meetings__isnull=False,
    ).all()
    tmp_tours_and_dates = []
    for tour in tours:
        meeting = tour.associated_meetings
        if not meeting:
            raise ValueError("Tour without associated meeting")
        first_datetime, dates = tour.first_datetime, meeting.date_objects
        if first_datetime is not None and dates:
            tmp_tours_and_dates.append((first_datetime, tour, dates))
    tours_and_dates = [(tour, dates) for first_datetime, tour, dates in sorted(tmp_tours_and_dates)]
    all_tours: list[Tour] = []
    all_dates: list[Date] = []
    for tour, dates in tours_and_dates:
        all_tours.append(tour)
        all_dates += dates
    return tours_and_dates, all_tours, all_dates


def signup(request: WSGIRequest) -> HttpResponse:
    semester: Semester = get_object_or_404(Semester, pk=get_semester(request))
    curr_settings: Setting = Setting.objects.get_or_create(semester=semester)[0]

    tours_and_dates, all_tours, all_dates = _get_tours_and_dates(semester)

    if not tours_and_dates:
        context: dict[str, Any] = {"semester": semester}
        return render(request, "guidedtours/signup/signup_notour.html", context)

    form = ParticipantForm(
        request.POST or None,
        tours_and_dates=tours_and_dates,
        tours=all_tours,
        dates=all_dates,
        semester=semester,
    )
    if form.is_valid():
        participant: Participant = form.save(commit=False)
        # if there is a tour with a participant using the same mail in the blocked time-window
        # (15min for transitioning and 15min for meeting)

        conflicting_dates = []
        for tour, dates in tours_and_dates:
            if tour == participant.tour:
                continue
            for date_obj in dates:
                if date_obj.intersects(participant.date):
                    conflicting_dates.append(date_obj)

        if Participant.objects.filter(Q(email=participant.email) & Q(date__in=conflicting_dates)).exists():
            return render(request, "guidedtours/signup/blocked.html", {"mail": TourMail.SET})
        participant.save()
        if curr_settings.mail_registration:
            mail: TourMail = curr_settings.mail_registration
            if not mail.send_mail_participant(participant):
                messages.error(
                    request,
                    _(
                        "Could not send you the registration email. You are registered, but you did not receve the "
                        "confirmation-email. Your email may be invalid. Please contact {mail}. ",
                    ).format(mail=TourMail.SET),
                )

        return redirect("guidedtours:signup_success")

    context = {
        "semester": semester,
        "form": form,
        "tours_and_dates": tours_and_dates,
    }
    return render(request, "guidedtours/signup/signup.html", context)


def signup_success(request: WSGIRequest) -> HttpResponse:
    return render(request, "guidedtours/signup/success.html")


@permission_required("guidedtours.view_participants")
def signup_internal(request: WSGIRequest) -> HttpResponse:
    semester: Semester = get_object_or_404(Semester, pk=get_semester(request))
    curr_settings: Setting = Setting.objects.get_or_create(semester=semester)[0]
    tours = semester.tour_set.order_by("date")

    if not tours:
        return redirect("guidedtours:add_tour")

    form = ParticipantForm(request.POST or None, tours=tours, semester=semester)
    if form.is_valid():
        participant: Participant = form.save()
        if curr_settings.mail_registration:
            mail: TourMail = curr_settings.mail_registration
            if not mail.send_mail_participant(participant):
                messages.error(
                    request,
                    _(
                        "Could not send the participant the registration email. "
                        "The Participant is registered, but did not receave the confirmation-email. "
                        "The email may be invalid or no Registration-mail may have been set.",
                    ),
                )

        return redirect("guidedtours:view_tour", participant.tour.id)

    context = {
        "semester": semester,
        "form": form,
    }
    return render(request, "guidedtours/signup/signup_internal.html", context)


@permission_required("guidedtours.view_participants")
def export_tour(request: WSGIRequest, file_format: str, tour_pk: UUID) -> Union[HttpResponse, PDFResponse]:
    tour = get_object_or_404(Tour, pk=tour_pk)
    participants = tour.participant_set.order_by("created_at")
    confirmed_participants = participants[: tour.capacity]
    tour_date = tour.first_datetime or "No-Date"
    filename = f"participants_{tour.name}_{tour_date}_{time.strftime('%Y%m%d-%H%M')}"
    context = {"participants": confirmed_participants, "tour": tour}
    if file_format == "csv":
        return utils.download_csv(
            ["surname", "firstname", "created_at", "updated_at", "email", "phone", "subject"],
            f"{filename}.csv",
            confirmed_participants,
        )
    return render_to_pdf(request, "guidedtours/tex/tour.tex", context, f"{filename}.pdf")


@permission_required("guidedtours.view_participants")
def settings(request: WSGIRequest) -> HttpResponse:
    semester: Semester = get_object_or_404(Semester, pk=get_semester(request))
    curr_settings: Setting = Setting.objects.get_or_create(semester=semester)[0]

    form = SettingsAdminForm(request.POST or None, semester=semester, instance=curr_settings)
    if form.is_valid():
        curr_settings = form.save()
        if curr_settings:
            messages.success(request, "Saved Settings.")
        else:
            messages.error(request, "The Settings do not exist.")

        return redirect("guidedtours:dashboard")

    return render(
        request,
        "guidedtours/maintenance/settings/general.html",
        {
            "form": form,
        },
    )
