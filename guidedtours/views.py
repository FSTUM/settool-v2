import time
from datetime import timedelta
from typing import Any, Optional, Union

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import Q, QuerySet
from django.db.models.aggregates import Count
from django.forms import formset_factory
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.datetime_safe import date
from django.utils.translation import gettext as _
from django_tex.response import PDFResponse
from django_tex.shortcuts import render_to_pdf

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


@permission_required("guidedtours.view_participants")
def dashboard(request: WSGIRequest) -> HttpResponse:
    tours = (
        Tour.objects.filter(Q(semester=get_semester(request)) & Q(date__gte=date.today()))
        .values("capacity", "name", "date")
        .annotate(registered=Count("participant"))
        .order_by("date")
    )

    context = {
        "tour_labels": [f"{tour['name']} am {tour['date'].strftime('%d.%m um %H:%M')}Uhr" for tour in tours],
        "tour_registrations": [tour["registered"] for tour in tours],
        "tour_capacity": [tour["capacity"] for tour in tours],
    }
    return render(request, "guidedtours/tour_dashboard.html", context)


@permission_required("guidedtours.view_participants")
def view_tour(request: WSGIRequest, tour_pk: int) -> HttpResponse:
    tour = get_object_or_404(Tour, pk=tour_pk)
    participants = tour.participant_set.order_by("time")
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
def edit_tour(request: WSGIRequest, tour_pk: int) -> HttpResponse:
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
def del_tour(request: WSGIRequest, tour_pk: int) -> HttpResponse:
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


def signup(request: WSGIRequest) -> HttpResponse:
    semester: Semester = get_object_or_404(Semester, pk=get_semester(request))
    curr_settings: Setting = Setting.objects.get_or_create(semester=semester)[0]
    tours = semester.tour_set.filter(
        open_registration__lt=timezone.now(),
        close_registration__gt=timezone.now(),
    ).order_by("date")

    if not tours:
        context: dict[str, Any] = {"semester": semester}
        return render(request, "guidedtours/signup/signup_notour.html", context)

    form = ParticipantForm(request.POST or None, tours=tours, semester=semester)
    if form.is_valid():
        participant: Participant = form.save(commit=False)
        # if there is a tour with a participant using the same mail in the blocked time-window
        # (15min for transitioning and 15min for meeting)
        conflicting_tours = semester.tour_set.filter(
            date__gt=participant.tour.date - timedelta(minutes=30),
            date__lt=participant.tour.date + timedelta(minutes=participant.tour.length) + timedelta(minutes=30),
        )
        if Participant.objects.filter(Q(email=participant.email) & Q(tour__in=conflicting_tours)).exists():
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
        "tours": tours,
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
def export_tour(request: WSGIRequest, file_format: str, tour_pk: int) -> Union[HttpResponse, PDFResponse]:
    tour = get_object_or_404(Tour, pk=tour_pk)
    participants = tour.participant_set.order_by("time")
    confirmed_participants = participants[: tour.capacity]
    filename = f"participants_{tour.name}_{tour.date}_{time.strftime('%Y%m%d-%H%M')}"
    context = {"participants": confirmed_participants, "tour": tour}
    if file_format == "csv":
        return utils.download_csv(
            ["surname", "firstname", "time", "email", "phone", "subject"],
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
